from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import joblib
import json

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['JWT_SECRET_KEY'] = 'super-secret-key-change-this-in-production'
db = SQLAlchemy(app)
jwt = JWTManager(app)

pipeline = joblib.load('./pipeline.joblib')
df = pd.read_pickle('./dataset.pkl')

class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "Username already exists"}), 400
    new_user = User(username=data['username'], password=generate_password_hash(data['password']))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User created successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        return jsonify(access_token=create_access_token(identity=user.username)), 200
    return jsonify({"msg": "Invalid credentials"}), 401



@app.route('/data/shape', methods=['GET'])
@jwt_required()
def get_shape():
    return jsonify({"rows": df.shape[0], "columns": df.shape[1]})

@app.route('/data/columns', methods=['GET'])
@jwt_required()
def get_columns():
    return jsonify([{"name": col, "type": str(dtype)} for col, dtype in df.dtypes.items()])

@app.route('/data/head/<int:n>', methods=['GET'])
@jwt_required()
def get_head(n):
    return jsonify(json.loads(df.head(n).to_json(orient='records')))

@app.route('/data/tail/<int:n>', methods=['GET'])
@jwt_required()
def get_tail(n):
    return jsonify(json.loads(df.tail(n).to_json(orient='records')))

@app.route('/data/describe', methods=['GET'])
@jwt_required()
def get_describe():
    return jsonify(json.loads(df.describe().to_json()))

@app.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    data = request.json
    try:
        import pandas as pd
        features = pd.DataFrame([{
            "Social support":              float(data['social_support']),
            "Healthy life\nexpectancy":    float(data['healthy_life_expectancy']),
            "Log of GDP\nper capita":      float(data['log_gdp_per_capita']),
            "Freedom":                     float(data['freedom']),
        }])
        prediction = pipeline.predict(features)[0]
        return jsonify({"prediction": round(float(prediction), 4)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400



if __name__ == '__main__':
    app.run(debug=True, port=5000)