import { useState, useEffect } from 'react';
import './App.css';

const API = 'http://127.0.0.1:5000';

const STATUS_COLORS = {
  Draft: '#FFF9C4',
  Submitted: '#E3F2FD',
  'Under Review': '#FFF3E0',
  Approved: '#E8F5E9',
  Rejected: '#FFEBEE'
};

const TRANSITIONS = {
  Draft: 'Submitted',
  Submitted: 'Under Review',
  'Under Review': 'Approved',
  Rejected: 'Draft'
};

function App() {
  const [user, setUser] = useState(null);
  const [labels, setLabels] = useState([]);
  const [form, setForm] = useState({
    product_name: '', label_type: 'Primary', content: ''
  });
  const [audit, setAudit] = useState([]);
  const [selectedLabel, setSelectedLabel] = useState(null);
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    if (urlToken) {
      localStorage.setItem('auth_token', urlToken);
      window.history.replaceState({}, '', '/');
    }
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) { setLoading(false); return; }

      const res = await fetch(`${API}/auth/user?token=${token}`);
      const data = await res.json();
      if (data.authenticated) {
        setUser(data.user);
        fetchLabels(token);
      } else {
        localStorage.removeItem('auth_token');
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const fetchLabels = async (token) => {
    const t = token || localStorage.getItem('auth_token');
    try {
      const res = await fetch(`${API}/labels`, {
        headers: { 'X-Auth-Token': t }
      });
      if (res.ok) setLabels(await res.json());
    } catch (e) { console.error(e); }
  };

  const handleLogin = () => {
    window.location.href = `${API}/auth/login`;
  };

  const handleLogout = async () => {
    const token = localStorage.getItem('auth_token');
    await fetch(`${API}/auth/logout?token=${token}`);
    localStorage.removeItem('auth_token');
    setUser(null);
    setLabels([]);
  };

  const submitLabel = async () => {
    setErrors([]);
    const token = localStorage.getItem('auth_token');
    const res = await fetch(`${API}/labels`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Auth-Token': token
      },
      body: JSON.stringify({ ...form, submitted_by: user?.name })
    });
    const data = await res.json();
    if (data.errors) { setErrors(data.errors); return; }
    setForm({ product_name: '', label_type: 'Primary', content: '' });
    fetchLabels();
  };

  const updateStatus = async (label, newStatus) => {
    const token = localStorage.getItem('auth_token');
    await fetch(`${API}/labels/${label.id}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-Auth-Token': token
      },
      body: JSON.stringify({ status: newStatus })
    });
    fetchLabels();
  };

  const viewAudit = async (label) => {
    const token = localStorage.getItem('auth_token');
    setSelectedLabel(label);
    const res = await fetch(`${API}/labels/${label.id}/audit`, {
      headers: { 'X-Auth-Token': token }
    });
    const data = await res.json();
    setAudit(data.audit_trail || []);
  };

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center',
      alignItems: 'center', height: '100vh' }}>
      <p>Loading...</p>
    </div>
  );

  // ── Login Page ──
  if (!user) return (
    <div style={{ display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      height: '100vh', fontFamily: 'Arial', background: '#F5F5F5' }}>
      <div style={{ background: 'white', padding: 40, borderRadius: 12,
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        textAlign: 'center', maxWidth: 420 }}>
        <h1 style={{ color: '#1F4E79', marginBottom: 8 }}>
          💊 Pharma Workflow
        </h1>
        <p style={{ color: '#555', marginBottom: 8 }}>
          Label Approval & Compliance System
        </p>
        <p style={{ color: '#888', fontSize: 12, marginBottom: 30 }}>
          Secured with Google OAuth 2.0 SSO
        </p>
        <button onClick={handleLogin} style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '12px 24px', background: 'white',
          border: '2px solid #ddd', borderRadius: 8,
          cursor: 'pointer', fontSize: 16, margin: '0 auto',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
          <img
            src="https://developers.google.com/identity/images/g-logo.png"
            alt="Google" width="24" />
          Sign in with Google
        </button>
        <p style={{ color: '#888', fontSize: 11, marginTop: 20 }}>
          OAuth 2.0 / OpenID Connect — same protocol used in enterprise SSO
        </p>
      </div>
    </div>
  );

  // ── Main App ──
  return (
    <div style={{ maxWidth: 900, margin: '30px auto',
      fontFamily: 'Arial', padding: 20 }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', borderBottom: '3px solid #1F4E79',
        paddingBottom: 10, marginBottom: 20 }}>
        <div>
          <h1 style={{ color: '#1F4E79', margin: 0 }}>
            💊 Pharma Label Workflow
          </h1>
          <p style={{ color: '#555', margin: 0, fontSize: 12 }}>
            Draft → Submitted → Under Review → Approved → SAP
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {user.picture && (
            <img src={user.picture} alt="avatar"
              style={{ width: 36, height: 36, borderRadius: '50%' }} />
          )}
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontWeight: 'bold', fontSize: 14 }}>{user.name}</div>
            <div style={{ color: '#888', fontSize: 11 }}>{user.email}</div>
            <div style={{ color: '#4CAF50', fontSize: 10 }}>
              ✅ SSO Authenticated
            </div>
          </div>
          <button onClick={handleLogout} style={{ padding: '6px 14px',
            background: '#f44336', color: 'white', border: 'none',
            borderRadius: 5, cursor: 'pointer' }}>
            Logout
          </button>
        </div>
      </div>

      {/* Submit Form */}
      <div style={{ background: '#F5F5F5', padding: 20,
        borderRadius: 8, marginBottom: 30 }}>
        <h3 style={{ color: '#1F4E79', marginTop: 0 }}>Submit New Label</h3>
        {errors.length > 0 && (
          <div style={{ background: '#FFEBEE', padding: 10,
            borderRadius: 5, marginBottom: 10 }}>
            {errors.map((e, i) =>
              <div key={i} style={{ color: '#C62828' }}>⚠️ {e}</div>)}
          </div>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr',
          gap: 10, marginBottom: 10 }}>
          <input placeholder="Product Name" value={form.product_name}
            onChange={e => setForm({ ...form, product_name: e.target.value })}
            style={{ padding: 8, borderRadius: 5, border: '1px solid #ccc' }} />
          <select value={form.label_type}
            onChange={e => setForm({ ...form, label_type: e.target.value })}
            style={{ padding: 8, borderRadius: 5, border: '1px solid #ccc' }}>
            <option>Primary</option>
            <option>Secondary</option>
            <option>Insert</option>
            <option>Carton</option>
          </select>
        </div>
        <textarea placeholder="Label Content / Description"
          value={form.content}
          onChange={e => setForm({ ...form, content: e.target.value })}
          style={{ width: '100%', padding: 8, borderRadius: 5,
            border: '1px solid #ccc', height: 80,
            boxSizing: 'border-box' }} />
        <button onClick={submitLabel} style={{ marginTop: 10,
          padding: '10px 24px', background: '#1F4E79', color: 'white',
          border: 'none', borderRadius: 5, cursor: 'pointer',
          fontSize: 15 }}>
          Submit Label
        </button>
      </div>

      {/* Labels */}
      <h3 style={{ color: '#1F4E79' }}>Label Queue</h3>
      {labels.length === 0 &&
        <p style={{ color: '#888' }}>No labels submitted yet.</p>}
      {labels.map(label => (
        <div key={label.id} style={{
          background: STATUS_COLORS[label.status] || '#fff',
          border: '1px solid #ddd', borderRadius: 8,
          padding: 16, marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between',
            alignItems: 'center' }}>
            <div>
              <strong style={{ fontSize: 16 }}>{label.product_name}</strong>
              <span style={{ marginLeft: 10, background: '#1F4E79',
                color: 'white', padding: '2px 10px',
                borderRadius: 10, fontSize: 12 }}>{label.label_type}</span>
              <span style={{ marginLeft: 10, color: '#555', fontSize: 13 }}>
                by {label.submitted_by}
              </span>
            </div>
            <span style={{ fontWeight: 'bold', color: '#1F4E79' }}>
              {label.status}
            </span>
          </div>
          <p style={{ color: '#555', margin: '8px 0', fontSize: 13 }}>
            {label.content}
          </p>
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            {TRANSITIONS[label.status] && (
              <button
                onClick={() => updateStatus(label, TRANSITIONS[label.status])}
                style={{ padding: '6px 14px', background: '#0078D4',
                  color: 'white', border: 'none', borderRadius: 5,
                  cursor: 'pointer' }}>
                Move to: {TRANSITIONS[label.status]}
              </button>
            )}
            {label.status === 'Under Review' && (
              <button onClick={() => updateStatus(label, 'Rejected')}
                style={{ padding: '6px 14px', background: '#C62828',
                  color: 'white', border: 'none', borderRadius: 5,
                  cursor: 'pointer' }}>
                Reject
              </button>
            )}
            <button onClick={() => viewAudit(label)}
              style={{ padding: '6px 14px', background: '#555',
                color: 'white', border: 'none', borderRadius: 5,
                cursor: 'pointer' }}>
              View Audit Trail
            </button>
          </div>
        </div>
      ))}

      {/* Audit Trail */}
      {selectedLabel && (
        <div style={{ marginTop: 30, background: '#F5F5F5',
          padding: 20, borderRadius: 8 }}>
          <h3 style={{ color: '#1F4E79', marginTop: 0 }}>
            📋 Audit Trail — {selectedLabel.product_name}
          </h3>
          {audit.length === 0 &&
            <p style={{ color: '#888' }}>No audit logs yet.</p>}
          {audit.map((log, i) => (
            <div key={i} style={{ borderLeft: '3px solid #1F4E79',
              paddingLeft: 12, marginBottom: 10 }}>
              <strong>{log.action}</strong> by <em>{log.performed_by}</em>
              <div style={{ color: '#555', fontSize: 12 }}>{log.details}</div>
              <div style={{ color: '#888', fontSize: 11 }}>
                {log.timestamp}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;