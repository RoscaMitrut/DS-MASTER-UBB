import React, { useState } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Route, Routes, Navigate, useNavigate } from 'react-router-dom';
import './App.css';

const API_URL = 'http://localhost:5000';

function setAuthToken(token) {
  if (token) axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  else delete axios.defaults.headers.common['Authorization'];
}
setAuthToken(localStorage.getItem('token'));



function DataTable({ data }) {
  if (!data?.length) return <p style={{ padding: 16, color: 'var(--muted)' }}>No rows.</p>;
  const cols = Object.keys(data[0]);
  return (
    <table>
      <thead><tr>{cols.map(c => <th key={c}>{c}</th>)}</tr></thead>
      <tbody>{data.map((row, i) => (
        <tr key={i}>{cols.map(c => <td key={c}>{String(row[c] ?? '')}</td>)}</tr>
      ))}</tbody>
    </table>
  );
}

function ColumnsTable({ data }) {
  return (
    <table>
      <thead><tr><th>#</th><th>Column</th><th>Type</th></tr></thead>
      <tbody>{data.map((col, i) => (
        <tr key={col.name}>
          <td>{i + 1}</td><td>{col.name}</td><td><span className="badge">{col.type}</span></td>
        </tr>
      ))}</tbody>
    </table>
  );
}

function DescribeTable({ data }) {
  const stats = Object.keys(data);
  const cols  = Object.keys(data[stats[0]] || {});
  return (
    <table>
      <thead><tr><th>Stat</th>{cols.map(c => <th key={c}>{c}</th>)}</tr></thead>
      <tbody>{stats.map(stat => (
        <tr key={stat}>
          <td className="stat-label">{stat}</td>
          {cols.map(c => <td key={c}>{typeof data[stat][c] === 'number' ? data[stat][c].toFixed(2) : String(data[stat][c] ?? '')}</td>)}
        </tr>
      ))}</tbody>
    </table>
  );
}

function PredictionResult({ result }) {
  const rank  = Math.round(result.prediction);
  return (
    <div className="predict-result-inner">
      <div className="score-ring">
        <span className="score-num">#{rank}</span>
        <span className="score-sub">out of 156</span>
      </div>
      <p>Predicted happiness rank. Lower is happier — #1 is Finland.</p>
    </div>
  );
}

function ResultArea({ result, type, loading }) {
  if (loading) return <div className="empty-state"><p>Loading...</p></div>;
  if (!result) return <div className="empty-state"><p>Run a query to see results here.</p></div>;

  if (type === 'shape') return (
    <div className="shape-display">
      <div className="shape-box"><span className="shape-num">{result.rows.toLocaleString()}</span><span className="shape-lbl">Rows</span></div>
      <div className="shape-sep">x</div>
      <div className="shape-box"><span className="shape-num">{result.columns}</span><span className="shape-lbl">Columns</span></div>
    </div>
  );

  if (type === 'columns')  return <ColumnsTable data={result} />;
  if (type === 'describe') return <DescribeTable data={result} />;
  if (type === 'head' || type === 'tail') return <DataTable data={result} />;
  if (type === 'prediction') return <PredictionResult result={result} />;

  return <pre style={{ padding: 16 }}>{JSON.stringify(result, null, 2)}</pre>;
}



function Login({ setAuth }) {
  const [username, setUsername]       = useState('');
  const [password, setPassword]       = useState('');
  const [registering, setRegistering] = useState(false);
  const [msg, setMsg]                 = useState(null);
  const [loading, setLoading]         = useState(false);
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
      setMsg({ text: err.response?.data?.msg || 'Something went wrong.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <p>World Happiness Report 2019</p>
        </div>
        <form onSubmit={submit}>
          <div className="field"><label>Username</label><input type="text" value={username} onChange={e => setUsername(e.target.value)} required autoFocus /></div>
          <div className="field"><label>Password</label><input type="password" value={password} onChange={e => setPassword(e.target.value)} required /></div>
          {msg && <div className={`msg ${msg.type}`}>{msg.text}</div>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? <span className="spinner" /> : (registering ? 'Create Account' : 'Sign In')}
          </button>
        </form>
        <button className="link-btn" onClick={() => { setRegistering(!registering); setMsg(null); }}>
          {registering ? 'Already have an account? Sign In' : "Don't have an account? Register"}
        </button>
      </div>
    </div>
  );
}



const PREDICT_FIELDS = [
  { key: 'social_support',          label: 'Social Support rank',              min: 1, max: 155, placeholder: 'e.g. 5  (1=best)' },
  { key: 'healthy_life_expectancy', label: 'Healthy Life Expectancy rank',     min: 1, max: 155, placeholder: 'e.g. 20  (1=best)' },
  { key: 'log_gdp_per_capita',      label: 'Log of GDP per Capita rank',       min: 1, max: 155, placeholder: 'e.g. 15  (1=best)' },
  { key: 'freedom',                 label: 'Freedom to Make Life Choices rank', min: 1, max: 155, placeholder: 'e.g. 10  (1=best)' },
];

function Dashboard() {
  const [tab, setTab]         = useState('explore');
  const [result, setResult]   = useState(null);
  const [type, setType]       = useState('');
  const [loading, setLoading] = useState(false);
  const [nRows, setNRows]     = useState(5);
  const [predictData, setPredictData] = useState(
    Object.fromEntries(PREDICT_FIELDS.map(f => [f.key, '']))
  );

  const query = async (fn, t) => {
    setLoading(true);
    try { setResult(await fn()); setType(t); }
    catch (err) { setResult({ error: err.message }); setType('error'); }
    finally { setLoading(false); }
  };

  const predict = (e) => {
    e.preventDefault();
    query(() => axios.post(`${API_URL}/predict`, predictData).then(r => r.data), 'prediction');
  };

  const switchTab = (t) => { setTab(t); setResult(null); setType(''); };

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <button className={`nav-btn ${tab === 'explore' ? 'active' : ''}`} onClick={() => switchTab('explore')}>⊞ Data Explorer</button>
        <button className={`nav-btn ${tab === 'predict' ? 'active' : ''}`} onClick={() => switchTab('predict')}>⊹ Predict Rank</button>
        <button className="logout-btn" onClick={() => { localStorage.removeItem('token'); setAuthToken(null); window.location.reload(); }}>⏻ Sign Out</button>
      </aside>

      <div className="main">

        {tab === 'explore' && <>
          <div>
            <div className="page-title">Data Explorer</div>
            <div className="page-sub">World Happiness Report 2019 — all values are country rankings (1 = best)</div>
          </div>
          <div className="toolbar">
            <button className="btn" onClick={() => query(() => axios.get(`${API_URL}/data/shape`).then(r => r.data), 'shape')}>Shape</button>
            <button className="btn" onClick={() => query(() => axios.get(`${API_URL}/data/columns`).then(r => r.data), 'columns')}>Columns</button>
            <button className="btn" onClick={() => query(() => axios.get(`${API_URL}/data/describe`).then(r => r.data), 'describe')}>Statistics</button>
            <div className="toolbar-sep" />
            <input className="n-input" type="number" value={nRows} min="1" max="156" onChange={e => setNRows(e.target.value)} />
            <button className="btn" onClick={() => query(() => axios.get(`${API_URL}/data/head/${nRows}`).then(r => r.data), 'head')}>Head</button>
            <button className="btn" onClick={() => query(() => axios.get(`${API_URL}/data/tail/${nRows}`).then(r => r.data), 'tail')}>Tail</button>
            {loading && <span className="loading-pill">Loading...</span>}
          </div>
          <div className="result-area">
            <ResultArea result={result} type={type} loading={loading} />
          </div>
        </>}

        {tab === 'predict' && <>
          <div>
            <div className="page-title">Predict Happiness Rank</div>
            <div className="page-sub">Enter each feature's country rank (1 = best) — the model predicts the overall Ladder rank</div>
          </div>
          <div className="predict-layout">
            <div className="predict-form-card">
              <h4>Feature Rankings</h4>
              <form onSubmit={predict}>
                {PREDICT_FIELDS.map(f => (
                  <div className="pfield" key={f.key}>
                    <label>{f.label}</label>
                    <input
                      type="number"
                      step="1"
                      min={f.min}
                      max={f.max}
                      placeholder={f.placeholder}
                      value={predictData[f.key]}
                      onChange={e => setPredictData({ ...predictData, [f.key]: e.target.value })}
                      required
                    />
                  </div>
                ))}
                <button type="submit" className="btn-predict" disabled={loading}>
                  {loading ? <span className="spinner" /> : '⊹ Predict Rank'}
                </button>
              </form>
            </div>

            <div className="predict-result-card">
              <ResultArea result={result} type={type} loading={loading} />
            </div>
          </div>
        </>}

      </div>
    </div>
  );
}


function App() {
  const [isAuth, setAuth] = useState(!!localStorage.getItem('token'));
  return (
    <Router>
      <Routes>
        <Route path="/"          element={isAuth ? <Navigate to="/dashboard" /> : <Login setAuth={setAuth} />} />
        <Route path="/dashboard" element={isAuth ? <Dashboard /> : <Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;