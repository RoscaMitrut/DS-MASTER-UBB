import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Route, Routes, Navigate, useNavigate } from 'react-router-dom';
import './App.css';

const API_URL = 'http://localhost:5000';

function setAuthToken(token) {
  if (token) axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  else delete axios.defaults.headers.common['Authorization'];
}
setAuthToken(localStorage.getItem('token'));

// Auto sign-out if the token expires / is rejected.
axios.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && localStorage.getItem('token')) {
      localStorage.removeItem('token');
      setAuthToken(null);
      window.location.href = '/';
    }
    return Promise.reject(err);
  }
);

const errMsg = (err, fallback) => err.response?.data?.error || err.response?.data?.msg || fallback;

function fmt(v) {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') return Number.isInteger(v) ? v.toLocaleString() : v.toFixed(4).replace(/\.?0+$/, '');
  return String(v);
}

/* ───────────────────────── Shared bits ───────────────────────── */
function Header({ title, sub }) {
  return <div className="page-head"><div className="page-title">{title}</div><div className="page-sub">{sub}</div></div>;
}
function Empty({ text }) {
  return <div className="empty-state"><p>{text}</p></div>;
}

function DataTable({ table }) {
  if (!table?.rows?.length) return <Empty text="No rows to show." />;
  const cols = table.columns;
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th className="row-idx">#</th>{cols.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {table.rows.map((row, i) => (
            <tr key={i}><td className="row-idx">{i}</td>{cols.map((c) => <td key={c}>{fmt(row[c])}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ColumnsTable({ data }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th className="row-idx">#</th><th>Column</th><th>Dtype</th><th>Non-Null</th><th>Nulls</th><th>Unique</th></tr></thead>
        <tbody>
          {data.map((c, i) => (
            <tr key={c.name}>
              <td className="row-idx">{i + 1}</td><td>{c.name}</td>
              <td><span className="badge">{c.type}</span></td>
              <td>{c.non_null.toLocaleString()}</td>
              <td className={c.nulls ? 'warn-cell' : ''}>{c.nulls.toLocaleString()}</td>
              <td>{c.unique.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DescribeTable({ data }) {
  const { stats, columns, rows } = data;
  if (!columns.length) return <Empty text="No numeric columns to describe." />;
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Stat</th>{columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {stats.map((s, i) => (
            <tr key={s}><td className="stat-label">{s}</td>{rows[i].map((v, j) => <td key={j}>{fmt(v)}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ShapeView({ data }) {
  return (
    <div className="shape-display">
      <div className="shape-box"><span className="shape-num">{data.rows.toLocaleString()}</span><span className="shape-lbl">Rows</span></div>
      <div className="shape-sep">×</div>
      <div className="shape-box"><span className="shape-num">{data.columns.toLocaleString()}</span><span className="shape-lbl">Columns</span></div>
    </div>
  );
}

/* ───────────────────────────── Login ───────────────────────────── */
function Login({ setAuth }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [registering, setRegistering] = useState(false);
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setMsg(null);
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}${registering ? '/register' : '/login'}`, { username, password });
      if (registering) {
        setMsg({ text: 'Account created! Please sign in.', type: 'success' });
        setRegistering(false);
      } else {
        localStorage.setItem('token', res.data.access_token);
        setAuthToken(res.data.access_token);
        setAuth(true);
        navigate('/dashboard');
      }
    } catch (err) {
      setMsg({ text: errMsg(err, 'Something went wrong.'), type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <span className="icon">◆</span>
          <h1>DataLab</h1>
          <p>Upload, explore &amp; model any dataset</p>
        </div>
        <form onSubmit={submit}>
          <div className="field"><label>Username</label><input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus /></div>
          <div className="field"><label>Password</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
          {msg && <div className={`msg ${msg.type}`}>{msg.text}</div>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? <span className="spinner" /> : registering ? 'Create Account' : 'Sign In'}
          </button>
        </form>
        <button className="link-btn" onClick={() => { setRegistering(!registering); setMsg(null); }}>
          {registering ? 'Already have an account? Sign In' : "Don't have an account? Register"}
        </button>
      </div>
    </div>
  );
}

/* ─────────────────────────── Upload tab ────────────────────────── */
function UploadTab({ status, refresh, notify, goExplore }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [info, setInfo] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const r = await axios.post(`${API_URL}/data/upload`, fd);
      setInfo(r.data);
      notify(`Loaded ${r.data.filename} — ${r.data.rows.toLocaleString()} rows × ${r.data.columns} cols`);
      await refresh();
    } catch (err) {
      notify(errMsg(err, 'Upload failed.'), 'error');
    } finally {
      setLoading(false);
    }
  };

  const onDrop = (e) => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) setFile(f); };

  return (
    <>
      <Header title="Upload Dataset" sub="Upload a CSV file to start exploring and modeling. Each account keeps its own dataset." />
      <div className="card upload-card">
        <form onSubmit={submit}>
          <label className="dropzone" onDragOver={(e) => e.preventDefault()} onDrop={onDrop}>
            <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files[0])} hidden />
            <div className="dz-icon">⬆</div>
            <div className="dz-text">{file ? file.name : 'Click to choose a .csv file'}</div>
            <div className="dz-hint">{file ? `${(file.size / 1024).toFixed(1)} KB` : 'or drag & drop it here'}</div>
          </label>
          <button className="btn-primary full" type="submit" disabled={!file || loading}>
            {loading ? <span className="spinner" /> : 'Upload & Load'}
          </button>
        </form>
      </div>

      {(info || status?.has_data) && (
        <div className="card center-card">
          <ShapeView data={{ rows: info?.rows ?? status.rows, columns: info?.columns ?? status.columns }} />
          <button className="btn" onClick={goExplore}>Explore the data →</button>
        </div>
      )}
    </>
  );
}

/* ─────────────────────────── Explore tab ───────────────────────── */
function ExploreTab({ refresh, notify }) {
  const [result, setResult] = useState(null);
  const [type, setType] = useState('');
  const [loading, setLoading] = useState(false);
  const [n, setN] = useState(5);

  const run = async (fn, t) => {
    setLoading(true);
    try { setResult(await fn()); setType(t); }
    catch (err) { notify(errMsg(err, 'Request failed.'), 'error'); }
    finally { setLoading(false); }
  };
  const get = (url, t) => run(() => axios.get(`${API_URL}${url}`).then((r) => r.data), t);

  const dropna = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${API_URL}/data/dropna`);
      setResult(r.data); setType('dropna');
      notify(`Removed ${r.data.removed.toLocaleString()} rows with empty values.`);
      await refresh();
    } catch (err) { notify(errMsg(err, 'Failed.'), 'error'); }
    finally { setLoading(false); }
  };

  return (
    <>
      <Header title="Explore Data" sub="Inspect shape, column details, sample rows and summary statistics." />
      <div className="toolbar">
        <button className="btn" onClick={() => get('/data/shape', 'shape')}>Shape</button>
        <button className="btn" onClick={() => get('/data/columns', 'columns')}>Columns &amp; Types</button>
        <button className="btn" onClick={() => get('/data/describe', 'describe')}>Statistics</button>
        <div className="toolbar-sep" />
        <input className="n-input" type="number" min="1" value={n} onChange={(e) => setN(e.target.value)} />
        <button className="btn" onClick={() => get(`/data/head/${n || 5}`, 'head')}>First N rows</button>
        <button className="btn" onClick={() => get(`/data/tail/${n || 5}`, 'tail')}>Last N rows</button>
        <div className="toolbar-sep" />
        <button className="btn btn-warn" onClick={dropna}>Drop Empty Rows</button>
        {loading && <span className="loading-pill">Loading…</span>}
      </div>
      <div className="result-area">
        {!result && !loading && <Empty text="Run a query above to see results here." />}
        {result && type === 'shape' && <ShapeView data={result} />}
        {result && type === 'columns' && <ColumnsTable data={result} />}
        {result && type === 'describe' && <DescribeTable data={result} />}
        {result && (type === 'head' || type === 'tail') && <DataTable table={result} />}
        {result && type === 'dropna' && (
          <div className="empty-state">
            <div className="big-check">✓</div>
            <p><b>{result.removed.toLocaleString()}</b> rows with empty values removed.</p>
            <p className="hint">Dataset now has <b>{result.rows.toLocaleString()}</b> rows × <b>{result.columns}</b> columns.</p>
          </div>
        )}
      </div>
    </>
  );
}

/* ───────────────────────── Preprocess tab ──────────────────────── */
const isNumericType = (t) => /(int|float|bool|number)/i.test(t);

function TransformTab({ status, refresh, notify }) {
  const [method, setMethod] = useState('onehot');
  const [cols, setCols] = useState([]);
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    axios.get(`${API_URL}/data/columns`).then((r) => setCols(r.data)).catch(() => {});
  }, [status?.columns, status?.rows]);

  const categorical = cols.filter((c) => !isNumericType(c.type));
  const toggle = (name) => setSelected((s) => (s.includes(name) ? s.filter((x) => x !== name) : [...s, name]));

  const apply = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${API_URL}/data/transform`, { method, columns: selected });
      setResult(r.data);
      notify(`Applied ${method === 'onehot' ? 'one-hot (get_dummies)' : 'ordinal'} encoding — now ${r.data.columns} columns.`);
      setSelected([]);
      await refresh();
    } catch (err) { notify(errMsg(err, 'Transform failed.'), 'error'); }
    finally { setLoading(false); }
  };

  const reset = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${API_URL}/data/reset`);
      setResult(null);
      notify(`Reset to original — ${r.data.rows.toLocaleString()} rows × ${r.data.columns} cols.`);
      await refresh();
    } catch (err) { notify(errMsg(err, 'Reset failed.'), 'error'); }
    finally { setLoading(false); }
  };

  return (
    <>
      <Header title="Preprocess & Encode" sub="Turn text columns into numbers with one-hot (get_dummies) or ordinal encoding before training." />
      <div className="grid-2">
        <div className="card">
          <h4>Encoding method</h4>
          <div className="radio-row">
            <label className={`radio-card ${method === 'onehot' ? 'sel' : ''}`}>
              <input type="radio" checked={method === 'onehot'} onChange={() => setMethod('onehot')} hidden />
              <b>One-Hot</b><span>get_dummies — a 0/1 column per category</span>
            </label>
            <label className={`radio-card ${method === 'ordinal' ? 'sel' : ''}`}>
              <input type="radio" checked={method === 'ordinal'} onChange={() => setMethod('ordinal')} hidden />
              <b>Ordinal</b><span>OrdinalEncoder.fit_transform — an integer code per category</span>
            </label>
          </div>

          <h4 className="mt">Columns to encode {selected.length > 0 && `(${selected.length})`}</h4>
          {categorical.length === 0 ? (
            <p className="hint">No text columns detected — your dataset is already fully numeric.</p>
          ) : (
            <>
              <p className="hint">Leave all unselected to encode every text column.</p>
              <div className="chip-grid">
                {categorical.map((c) => (
                  <button key={c.name} className={`chip ${selected.includes(c.name) ? 'sel' : ''}`} onClick={() => toggle(c.name)}>
                    {c.name} <span className="chip-type">{c.type}</span>
                  </button>
                ))}
              </div>
            </>
          )}

          <div className="btn-row">
            <button className="btn-primary" onClick={apply} disabled={loading || categorical.length === 0}>
              {loading ? <span className="spinner" /> : 'Apply Encoding'}
            </button>
            <button className="btn" onClick={reset} disabled={loading}>Reset to original</button>
          </div>
        </div>

        <div className="card">
          <h4>Result</h4>
          {!result ? (
            <p className="hint">Apply an encoding to see the resulting dataset shape and columns.</p>
          ) : (
            <>
              <div className="shape-mini"><b>{result.rows.toLocaleString()}</b> rows × <b>{result.columns}</b> columns</div>
              <div className="chip-grid scroll">{result.column_names.map((c) => <span key={c} className="chip static">{c}</span>)}</div>
            </>
          )}
        </div>
      </div>
    </>
  );
}

/* ──────────────────────────── Train tab ────────────────────────── */
const TASKS = [
  { id: 'regression', label: 'Regression', desc: 'Predict a continuous number', needTarget: true },
  { id: 'classification', label: 'Classification', desc: 'Predict a category / label', needTarget: true },
  { id: 'clustering', label: 'Clustering', desc: 'Group similar rows (no target)', needTarget: false },
];

const METRIC_LABELS = {
  R2: 'R² Score', MAE: 'MAE', RMSE: 'RMSE', accuracy: 'Accuracy', f1_macro: 'F1 (macro)',
  n_classes: 'Classes', test_size: 'Test rows', clusters: 'Clusters', silhouette: 'Silhouette',
};

function MetricsView({ result }) {
  const m = result.metrics || {};
  const entries = Object.entries(m).filter(([k]) => k !== 'sizes');
  return (
    <div>
      <div className="model-head">
        <span className="badge big">{result.task}</span>
        <span className="model-algo">{result.algorithm}</span>
      </div>
      {result.target && <p className="hint">Target: <b>{result.target}</b></p>}
      <div className="metric-grid">
        {entries.map(([k, v]) => (
          <div className="metric-box" key={k}>
            <span className="metric-num">{typeof v === 'number' && !Number.isInteger(v) ? v.toFixed(4) : String(v)}</span>
            <span className="metric-lbl">{METRIC_LABELS[k] || k}</span>
          </div>
        ))}
      </div>
      {m.sizes && (
        <>
          <h4 className="mt">Cluster sizes</h4>
          <div className="chip-grid">{Object.entries(m.sizes).map(([k, v]) => <span key={k} className="chip static">Cluster {k}: {v}</span>)}</div>
        </>
      )}
      <p className="hint mt">Features: {result.features.join(', ')}</p>
      <p className="hint go-predict">✓ Model ready — open the <b>Predict</b> tab to use it.</p>
    </div>
  );
}

function TrainTab({ status, refresh, notify }) {
  const [algos, setAlgos] = useState({});
  const [cols, setCols] = useState([]);
  const [task, setTask] = useState('regression');
  const [algorithm, setAlgorithm] = useState('');
  const [features, setFeatures] = useState([]);
  const [target, setTarget] = useState('');
  const [nClusters, setNClusters] = useState(3);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => { axios.get(`${API_URL}/meta/algorithms`).then((r) => setAlgos(r.data)).catch(() => {}); }, []);
  useEffect(() => { axios.get(`${API_URL}/data/columns`).then((r) => setCols(r.data)).catch(() => {}); }, [status?.columns, status?.rows]);
  useEffect(() => { setAlgorithm(Object.keys(algos[task] || {})[0] || ''); }, [task, algos]);

  const colNames = cols.map((c) => c.name);
  const taskDef = TASKS.find((t) => t.id === task);
  const toggleFeat = (n) => setFeatures((f) => (f.includes(n) ? f.filter((x) => x !== n) : [...f, n]));

  const train = async () => {
    setLoading(true);
    setResult(null);
    try {
      const r = await axios.post(`${API_URL}/data/train`, { task, algorithm, features, target, n_clusters: Number(nClusters) });
      setResult(r.data);
      notify(`Trained ${r.data.algorithm}. You can now make predictions.`);
      await refresh();
    } catch (err) { notify(errMsg(err, 'Training failed.'), 'error'); }
    finally { setLoading(false); }
  };

  const disabled = loading || features.length === 0 || (taskDef.needTarget && !target);

  return (
    <>
      <Header title="Train a Model" sub="Pick a task, choose feature columns, then train a regression, classification or clustering model." />
      <div className="grid-2">
        <div className="card train-config">
          <h4>1 · Task type</h4>
          <div className="radio-row three">
            {TASKS.map((t) => (
              <label key={t.id} className={`radio-card ${task === t.id ? 'sel' : ''}`}>
                <input type="radio" checked={task === t.id} onChange={() => setTask(t.id)} hidden />
                <b>{t.label}</b><span>{t.desc}</span>
              </label>
            ))}
          </div>

          <h4 className="mt">2 · Algorithm</h4>
          <select className="select" value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}>
            {Object.entries(algos[task] || {}).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>

          {task === 'clustering' && (
            <div className="inline-field">
              <label>Number of clusters (k)</label>
              <input className="n-input" type="number" min="2" max="20" value={nClusters} onChange={(e) => setNClusters(e.target.value)} />
            </div>
          )}

          <h4 className="mt">3 · Feature columns {features.length > 0 && `(${features.length})`}</h4>
          <p className="hint">These are fed to the algorithm. The prediction form is generated from them.</p>
          <div className="chip-grid scroll">
            {colNames.filter((c) => !taskDef.needTarget || c !== target).map((c) => (
              <button key={c} className={`chip ${features.includes(c) ? 'sel' : ''}`} onClick={() => toggleFeat(c)}>{c}</button>
            ))}
          </div>

          {taskDef.needTarget && (
            <>
              <h4 className="mt">4 · Target column (what to predict)</h4>
              <select className="select" value={target} onChange={(e) => { setTarget(e.target.value); setFeatures((f) => f.filter((x) => x !== e.target.value)); }}>
                <option value="">— select target —</option>
                {colNames.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </>
          )}

          <button className="btn-primary full mt" onClick={train} disabled={disabled}>
            {loading ? <span className="spinner" /> : 'Train Model'}
          </button>
        </div>

        <div className="card">
          <h4>Training result</h4>
          {!result ? <p className="hint">Configure the options on the left and train to see metrics here.</p> : <MetricsView result={result} />}
        </div>
      </div>
    </>
  );
}

/* ─────────────────────────── Predict tab ───────────────────────── */
function PredictionView({ result, target }) {
  const value = typeof result.prediction === 'number' && !Number.isInteger(result.prediction)
    ? result.prediction.toFixed(3) : String(result.prediction);
  return (
    <div className="predict-result-inner">
      <div className="score-ring">
        <span className="score-num">{value}</span>
        <span className="score-sub">{result.task}</span>
      </div>
      <p>
        {result.task === 'regression' && <>Predicted value of <b>{target}</b></>}
        {result.task === 'classification' && <>Predicted class for <b>{target}</b></>}
        {result.task === 'clustering' && <>Assigned to <b>{result.label}</b></>}
      </p>
    </div>
  );
}

function PredictTab({ status, notify }) {
  const model = status?.model;
  const [values, setValues] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!model) return;
    const init = {};
    model.features_meta.forEach((f) => { init[f.name] = f.kind === 'categorical' ? f.options[0] ?? '' : ''; });
    setValues(init);
    setResult(null);
  }, [model?.algorithm, model?.target, model?.task]);

  if (!model) return (<><Header title="Make a Prediction" sub="Train a model first." /><div className="result-area"><Empty text="No trained model yet — head to the Train tab." /></div></>);

  const set = (k, v) => setValues((s) => ({ ...s, [k]: v }));

  const predict = async (e) => {
    e.preventDefault();
    setLoading(true);
    try { const r = await axios.post(`${API_URL}/predict`, { values }); setResult(r.data); }
    catch (err) { notify(errMsg(err, 'Prediction failed.'), 'error'); }
    finally { setLoading(false); }
  };

  return (
    <>
      <Header title="Make a Prediction" sub={`Inputs are generated from your model's feature columns (${model.task} · ${model.algorithm}).`} />
      <div className="predict-layout">
        <div className="card predict-form-card">
          <h4>Feature inputs</h4>
          <form onSubmit={predict}>
            {model.features_meta.map((f) => (
              <div className="pfield" key={f.name}>
                <label>{f.name} {f.kind === 'numeric' && <span className="muted-tag">numeric</span>}</label>
                {f.kind === 'categorical' ? (
                  <select value={values[f.name] ?? ''} onChange={(e) => set(f.name, e.target.value)}>
                    {f.options.map((o) => <option key={o} value={o}>{o}</option>)}
                  </select>
                ) : (
                  <input type="number" step="any" value={values[f.name] ?? ''}
                    placeholder={f.mean != null ? `avg ≈ ${f.mean}` : ''}
                    onChange={(e) => set(f.name, e.target.value)} required />
                )}
              </div>
            ))}
            <button className="btn-predict" disabled={loading}>{loading ? <span className="spinner" /> : '⊹ Predict'}</button>
          </form>
        </div>
        <div className="card predict-result-card">
          {!result ? <Empty text="Enter values and click Predict." /> : <PredictionView result={result} target={model.target} />}
        </div>
      </div>
    </>
  );
}

/* ──────────────────────────── Dashboard ────────────────────────── */
function NavButton({ id, tab, set, icon, label, disabled }) {
  return (
    <button className={`nav-btn ${tab === id ? 'active' : ''}`} disabled={disabled}
      onClick={() => !disabled && set(id)} title={disabled ? 'Not available yet' : ''}>
      <span className="nav-ic">{icon}</span> {label}
    </button>
  );
}

function Dashboard() {
  const [tab, setTab] = useState('upload');
  const [status, setStatus] = useState(null);
  const [toast, setToast] = useState(null);

  const refresh = useCallback(async () => {
    try { setStatus((await axios.get(`${API_URL}/data/status`)).data); } catch { /* ignore */ }
  }, []);
  useEffect(() => { refresh(); }, [refresh]);

  const notify = (text, type = 'success') => { setToast({ text, type }); setTimeout(() => setToast(null), 3800); };
  const logout = () => { localStorage.removeItem('token'); setAuthToken(null); window.location.href = '/'; };
  const hasData = status?.has_data;

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="sidebar-brand"><span>◆</span> DataLab</div>
        <NavButton id="upload" tab={tab} set={setTab} icon="⬆" label="Upload Data" />
        <NavButton id="explore" tab={tab} set={setTab} icon="⊞" label="Explore" disabled={!hasData} />
        <NavButton id="transform" tab={tab} set={setTab} icon="✦" label="Preprocess" disabled={!hasData} />
        <NavButton id="train" tab={tab} set={setTab} icon="◷" label="Train Model" disabled={!hasData} />
        <NavButton id="predict" tab={tab} set={setTab} icon="⊹" label="Predict" disabled={!status?.has_model} />

        <div className="sidebar-status">
          {hasData ? (
            <>
              <div className="ds-row"><span>Rows</span><b>{status.rows.toLocaleString()}</b></div>
              <div className="ds-row"><span>Columns</span><b>{status.columns}</b></div>
              <div className="ds-row"><span>Model</span><b>{status.has_model ? status.model.task : '—'}</b></div>
            </>
          ) : (
            <div className="ds-empty">No dataset loaded</div>
          )}
        </div>
        <button className="logout-btn" onClick={logout}>⏻ Sign Out</button>
      </aside>

      <div className="main">
        {toast && <div className={`toast ${toast.type}`}>{toast.text}</div>}
        {tab === 'upload' && <UploadTab status={status} refresh={refresh} notify={notify} goExplore={() => setTab('explore')} />}
        {tab === 'explore' && <ExploreTab refresh={refresh} notify={notify} />}
        {tab === 'transform' && <TransformTab status={status} refresh={refresh} notify={notify} />}
        {tab === 'train' && <TrainTab status={status} refresh={refresh} notify={notify} />}
        {tab === 'predict' && <PredictTab status={status} notify={notify} />}
      </div>
    </div>
  );
}

/* ────────────────────────────── App ────────────────────────────── */
function App() {
  const [isAuth, setAuth] = useState(!!localStorage.getItem('token'));
  return (
    <Router>
      <Routes>
        <Route path="/" element={isAuth ? <Navigate to="/dashboard" /> : <Login setAuth={setAuth} />} />
        <Route path="/dashboard" element={isAuth ? <Dashboard /> : <Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
