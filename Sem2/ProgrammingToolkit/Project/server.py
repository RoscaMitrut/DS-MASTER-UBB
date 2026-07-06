
import os
import io
import json
import hashlib
import threading
from datetime import timedelta

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash

import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import (
    RandomForestRegressor, RandomForestClassifier,
    GradientBoostingRegressor,
)
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import (
    r2_score, mean_absolute_error, mean_squared_error,
    accuracy_score, f1_score, silhouette_score,
)

# ───────────────────────────── App setup ─────────────────────────────
BASE_DIR  = os.path.abspath(os.path.dirname(__file__))
DATA_ROOT = os.path.join(BASE_DIR, 'instance', 'userdata')
os.makedirs(DATA_ROOT, exist_ok=True)

app = Flask(__name__)
CORS(app)
app.json.sort_keys = False   # preserve our insertion order in JSON responses

app.config['SQLALCHEMY_DATABASE_URI']  = 'sqlite:///users.db'
app.config['JWT_SECRET_KEY']           = 'super-secret-key-change-this-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=12)
app.config['MAX_CONTENT_LENGTH']       = 64 * 1024 * 1024   # 64 MB upload cap

db  = SQLAlchemy(app)
jwt = JWTManager(app)


class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80),  unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


with app.app_context():
    db.create_all()


# ────────────────────── Per-user workspace store ─────────────────────
# username -> {"original": DataFrame, "df": DataFrame, "model": bundle}
_LOCK  = threading.Lock()
_STORE = {}


def _user_dir(username):
    h = hashlib.sha1(username.encode('utf-8')).hexdigest()[:16]
    d = os.path.join(DATA_ROOT, h)
    os.makedirs(d, exist_ok=True)
    return d


def _slot(username):
    """Return the user's workspace, lazily restoring it from disk."""
    with _LOCK:
        if username not in _STORE:
            d    = _user_dir(username)
            slot = {"original": None, "df": None, "model": None}
            orig_p, work_p = os.path.join(d, 'original.pkl'), os.path.join(d, 'working.pkl')
            model_p        = os.path.join(d, 'model.joblib')
            if os.path.exists(orig_p):
                slot["original"] = pd.read_pickle(orig_p)
            if os.path.exists(work_p):
                slot["df"] = pd.read_pickle(work_p)
            if os.path.exists(model_p):
                try:
                    slot["model"] = joblib.load(model_p)
                except Exception:
                    slot["model"] = None
            _STORE[username] = slot
        return _STORE[username]


def _save_df(username):
    slot, d = _STORE[username], _user_dir(username)
    if slot["original"] is not None:
        slot["original"].to_pickle(os.path.join(d, 'original.pkl'))
    if slot["df"] is not None:
        slot["df"].to_pickle(os.path.join(d, 'working.pkl'))


def _save_model(username):
    slot = _STORE[username]
    if slot["model"] is not None:
        joblib.dump(slot["model"], os.path.join(_user_dir(username), 'model.joblib'))


def require_df():
    """Fetch the requesting user's working dataframe, or an error response."""
    username = get_jwt_identity()
    slot     = _slot(username)
    if slot["df"] is None:
        return None, None, (jsonify({"error": "No dataset uploaded yet. Upload a CSV first."}), 400)
    return slot, username, None


def _table(frame):
    """JSON-safe table preserving column order; NaN becomes null."""
    return {
        "columns": [str(c) for c in frame.columns],
        "rows":    json.loads(frame.to_json(orient='records')),
    }


# ───────────────────────────── Auth ──────────────────────────────────
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    username, password = (data.get('username') or '').strip(), data.get('password') or ''
    if not username or not password:
        return jsonify({"msg": "Username and password are required."}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 400
    db.session.add(User(username=username, password=generate_password_hash(password)))
    db.session.commit()
    return jsonify({"msg": "User created successfully!"}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    user = User.query.filter_by(username=(data.get('username') or '').strip()).first()
    if user and check_password_hash(user.password, data.get('password') or ''):
        return jsonify(access_token=create_access_token(identity=user.username)), 200
    return jsonify({"msg": "Invalid credentials"}), 401


# ─────────────────────── Dataset: upload / inspect ───────────────────
@app.route('/data/upload', methods=['POST'])
@jwt_required()
def upload():
    username = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
    f = request.files['file']
    if not f or f.filename == '':
        return jsonify({"error": "No file selected."}), 400
    if not f.filename.lower().endswith('.csv'):
        return jsonify({"error": "Please upload a .csv file."}), 400
    try:
        df = pd.read_csv(io.BytesIO(f.read()))
    except Exception as e:
        return jsonify({"error": f"Could not parse CSV: {e}"}), 400
    if df.shape[1] == 0 or df.shape[0] == 0:
        return jsonify({"error": "The CSV appears to be empty."}), 400

    slot = _slot(username)
    slot["original"], slot["df"], slot["model"] = df.copy(), df.copy(), None
    mp = os.path.join(_user_dir(username), 'model.joblib')
    if os.path.exists(mp):
        os.remove(mp)
    _save_df(username)
    return jsonify({
        "filename":     f.filename,
        "rows":         int(df.shape[0]),
        "columns":      int(df.shape[1]),
        "column_names": [str(c) for c in df.columns],
    })


@app.route('/data/shape')
@jwt_required()
def shape():
    slot, _, err = require_df()
    if err:
        return err
    df = slot["df"]
    return jsonify({"rows": int(df.shape[0]), "columns": int(df.shape[1])})


@app.route('/data/columns')
@jwt_required()
def columns():
    """Column names and their details (dtype, null counts, cardinality)."""
    slot, _, err = require_df()
    if err:
        return err
    df = slot["df"]
    return jsonify([{
        "name":     str(col),
        "type":     str(df[col].dtype),
        "non_null": int(df[col].notna().sum()),
        "nulls":    int(df[col].isna().sum()),
        "unique":   int(df[col].nunique(dropna=True)),
    } for col in df.columns])


@app.route('/data/head/<int:n>')
@jwt_required()
def head(n):
    slot, _, err = require_df()
    if err:
        return err
    return jsonify(_table(slot["df"].head(max(1, min(n, 1000)))))


@app.route('/data/tail/<int:n>')
@jwt_required()
def tail(n):
    slot, _, err = require_df()
    if err:
        return err
    return jsonify(_table(slot["df"].tail(max(1, min(n, 1000)))))


@app.route('/data/describe')
@jwt_required()
def describe():
    slot, _, err = require_df()
    if err:
        return err
    df = slot["df"]
    try:
        desc = df.describe()
        if desc.shape[1] == 0:
            desc = df.describe(include='all')
    except ValueError:
        desc = df.describe(include='all')
    return jsonify({
        "stats":   [str(i) for i in desc.index],
        "columns": [str(c) for c in desc.columns],
        "rows":    json.loads(desc.to_json(orient='values')),
    })


# ─────────────────────── Dataset: clean / encode ─────────────────────
@app.route('/data/dropna', methods=['POST'])
@jwt_required()
def dropna():
    slot, username, err = require_df()
    if err:
        return err
    before     = len(slot["df"])
    slot["df"] = slot["df"].dropna().reset_index(drop=True)
    _save_df(username)
    return jsonify({
        "removed": int(before - len(slot["df"])),
        "rows":    int(slot["df"].shape[0]),
        "columns": int(slot["df"].shape[1]),
    })


@app.route('/data/transform', methods=['POST'])
@jwt_required()
def transform():
    """Encode categorical columns with get_dummies (one-hot) or OrdinalEncoder."""
    slot, username, err = require_df()
    if err:
        return err
    body   = request.get_json(silent=True) or {}
    method = body.get('method', 'onehot')
    chosen = body.get('columns') or []
    df     = slot["df"]

    cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    targets  = [c for c in chosen if c in df.columns] if chosen else cat_cols
    if not targets:
        return jsonify({"error": "No categorical columns to transform."}), 400

    try:
        if method == 'onehot':
            df = pd.get_dummies(df, columns=targets)
            bool_cols = df.select_dtypes(include='bool').columns
            df[bool_cols] = df[bool_cols].astype(int)
        elif method == 'ordinal':
            enc = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
            df[targets] = enc.fit_transform(df[targets].astype(str))
        else:
            return jsonify({"error": f"Unknown method '{method}'."}), 400
    except Exception as e:
        return jsonify({"error": f"Transform failed: {e}"}), 400

    slot["df"] = df
    _save_df(username)
    return jsonify({
        "method":       method,
        "transformed":  targets,
        "rows":         int(df.shape[0]),
        "columns":      int(df.shape[1]),
        "column_names": [str(c) for c in df.columns],
    })


@app.route('/data/reset', methods=['POST'])
@jwt_required()
def reset():
    username = get_jwt_identity()
    slot     = _slot(username)
    if slot["original"] is None:
        return jsonify({"error": "No dataset to reset."}), 400
    slot["df"] = slot["original"].copy()
    _save_df(username)
    return jsonify({"rows": int(slot["df"].shape[0]), "columns": int(slot["df"].shape[1])})


# ───────────────────────────── Modeling ──────────────────────────────
ALGORITHMS = {
    'regression': {
        'linear':            'Linear Regression',
        'random_forest':     'Random Forest Regressor',
        'gradient_boosting': 'Gradient Boosting Regressor',
        'decision_tree':     'Decision Tree Regressor',
    },
    'classification': {
        'logistic':          'Logistic Regression',
        'random_forest':     'Random Forest Classifier',
        'decision_tree':     'Decision Tree Classifier',
        'knn':               'K-Nearest Neighbors',
    },
    'clustering': {
        'kmeans':            'K-Means',
        'agglomerative':     'Agglomerative (Hierarchical)',
    },
}


def _make_estimator(task, algorithm, n_clusters):
    if task == 'regression':
        return {
            'linear':            LinearRegression(),
            'random_forest':     RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(random_state=42),
            'decision_tree':     DecisionTreeRegressor(random_state=42),
        }[algorithm]
    if task == 'classification':
        return {
            'logistic':          LogisticRegression(max_iter=1000),
            'random_forest':     RandomForestClassifier(n_estimators=100, random_state=42),
            'decision_tree':     DecisionTreeClassifier(random_state=42),
            'knn':               KNeighborsClassifier(),
        }[algorithm]
    if task == 'clustering':
        if algorithm == 'agglomerative':
            return AgglomerativeClustering(n_clusters=int(n_clusters))
        return KMeans(n_clusters=int(n_clusters), n_init=10, random_state=42)
    raise ValueError("Unknown task")


def _build_preprocessor(X, features):
    """StandardScaler for numeric features, OrdinalEncoder for categorical."""
    num = [c for c in features if pd.api.types.is_numeric_dtype(X[c])]
    cat = [c for c in features if c not in num]
    steps = []
    if num:
        steps.append(('num', StandardScaler(), num))
    if cat:
        steps.append(('cat', OrdinalEncoder(handle_unknown='use_encoded_value',
                                            unknown_value=-1), cat))
    return ColumnTransformer(steps, remainder='drop'), num, cat


def _feature_schema(data, features, num):
    """Describe each feature so the client can render the prediction form."""
    meta = []
    for c in features:
        if c in num:
            col = data[c]
            meta.append({"name": str(c), "kind": "numeric",
                         "min":  float(col.min()), "max": float(col.max()),
                         "mean": round(float(col.mean()), 4)})
        else:
            opts = sorted({str(v) for v in data[c].astype(str).tolist()})[:200]
            meta.append({"name": str(c), "kind": "categorical", "options": opts})
    return meta


@app.route('/data/train', methods=['POST'])
@jwt_required()
def train():
    slot, username, err = require_df()
    if err:
        return err
    df         = slot["df"]
    body       = request.get_json(silent=True) or {}
    task       = body.get('task')
    algorithm  = body.get('algorithm')
    features   = [c for c in (body.get('features') or []) if c in df.columns]
    target     = body.get('target')
    n_clusters = body.get('n_clusters', 3)

    # ── validation ───────────────────────────────────────────────────
    if task not in ALGORITHMS:
        return jsonify({"error": "Choose a task: regression, classification or clustering."}), 400
    if task == 'clustering':
        if algorithm not in ALGORITHMS['clustering']:
            algorithm = 'kmeans'
    elif algorithm not in ALGORITHMS[task]:
        return jsonify({"error": "Choose a valid algorithm for this task."}), 400
    if not features:
        return jsonify({"error": "Select at least one feature column."}), 400

    needs_target = task in ('regression', 'classification')
    if needs_target:
        if not target or target not in df.columns:
            return jsonify({"error": "Select a target column."}), 400
        if target in features:
            return jsonify({"error": "The target column can't also be a feature."}), 400

    used = features + ([target] if needs_target else [])
    data = df[used].dropna()
    if len(data) < 5:
        return jsonify({"error": "Not enough complete rows to train (need ≥ 5). "
                                 "Try 'Drop empty rows' or pick other columns."}), 400

    X = data[features]
    pre, num, _ = _build_preprocessor(X, features)
    pipeline    = Pipeline([('pre', pre),
                            ('model', _make_estimator(task, algorithm, n_clusters))])

    # ── fit + evaluate ───────────────────────────────────────────────
    try:
        if task == 'regression':
            y    = pd.to_numeric(data[target], errors='coerce')
            mask = y.notna()
            X, y = X[mask], y[mask]
            if len(y) < 5:
                return jsonify({"error": "Target column is not numeric enough for regression."}), 400
            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
            pipeline.fit(X_tr, y_tr)
            pred    = pipeline.predict(X_te)
            metrics = {
                "R2":        round(float(r2_score(y_te, pred)), 4),
                "MAE":       round(float(mean_absolute_error(y_te, pred)), 4),
                "RMSE":      round(float(np.sqrt(mean_squared_error(y_te, pred))), 4),
                "test_size": int(len(y_te)),
            }

        elif task == 'classification':
            y     = data[target].astype(str)
            strat = y if y.value_counts().min() >= 2 else None
            X_tr, X_te, y_tr, y_te = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=strat)
            pipeline.fit(X_tr, y_tr)
            pred    = pipeline.predict(X_te)
            metrics = {
                "accuracy":  round(float(accuracy_score(y_te, pred)), 4),
                "f1_macro":  round(float(f1_score(y_te, pred, average='macro', zero_division=0)), 4),
                "n_classes": int(y.nunique()),
                "test_size": int(len(y_te)),
            }

        else:  # clustering
            labels        = pipeline.fit_predict(X)
            uniq, counts  = np.unique(labels, return_counts=True)
            metrics = {"clusters": int(len(uniq)),
                       "sizes": {int(k): int(v) for k, v in zip(uniq, counts)}}
            if len(uniq) > 1 and len(X) > len(uniq):
                Xt = pipeline.named_steps['pre'].transform(X)
                metrics["silhouette"] = round(float(silhouette_score(Xt, labels)), 4)
    except Exception as e:
        return jsonify({"error": f"Training failed: {e}"}), 400

    bundle = {
        "pipeline":        pipeline,
        "task":            task,
        "algorithm":       algorithm,
        "algorithm_label": ALGORITHMS[task][algorithm],
        "features":        features,
        "features_meta":   _feature_schema(data, features, num),
        "target":          target if needs_target else None,
        "metrics":         metrics,
    }
    slot["model"] = bundle
    _save_model(username)
    return jsonify(_model_public(bundle))


@app.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    slot   = _slot(get_jwt_identity())
    bundle = slot["model"]
    if bundle is None:
        return jsonify({"error": "No trained model. Train a model first."}), 400

    values = (request.get_json(silent=True) or {}).get('values') or {}
    row    = {}
    try:
        for meta in bundle["features_meta"]:
            name, raw = meta["name"], values.get(meta["name"])
            if meta["kind"] == "numeric":
                if raw is None or raw == '':
                    return jsonify({"error": f"Missing value for '{name}'."}), 400
                row[name] = float(raw)
            else:
                row[name] = '' if raw is None else str(raw)
        X    = pd.DataFrame([row], columns=bundle["features"])
        pred = bundle["pipeline"].predict(X)[0]
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {e}"}), 400

    task = bundle["task"]
    if task == 'regression':
        return jsonify({"task": task, "target": bundle["target"],
                        "prediction": round(float(pred), 4)})
    if task == 'classification':
        return jsonify({"task": task, "target": bundle["target"],
                        "prediction": str(pred)})
    return jsonify({"task": task, "prediction": int(pred), "label": f"Cluster {int(pred)}"})


# ────────────────────────────── Metadata ─────────────────────────────
def _model_public(m):
    return {
        "task":          m["task"],
        "algorithm":     m["algorithm_label"],
        "features":      m["features"],
        "features_meta": m["features_meta"],
        "target":        m["target"],
        "metrics":       m["metrics"],
    }


@app.route('/meta/algorithms')
@jwt_required()
def meta_algorithms():
    return jsonify(ALGORITHMS)


@app.route('/data/status')
@jwt_required()
def status():
    slot = _slot(get_jwt_identity())
    df, m = slot["df"], slot["model"]
    return jsonify({
        "has_data":     df is not None,
        "rows":         int(df.shape[0]) if df is not None else 0,
        "columns":      int(df.shape[1]) if df is not None else 0,
        "column_names": [str(c) for c in df.columns] if df is not None else [],
        "has_model":    m is not None,
        "model":        _model_public(m) if m else None,
    })


if __name__ == '__main__':
    # threaded=True lets several users hit the API at the same time.
    app.run(debug=True, port=5000, threaded=True)
