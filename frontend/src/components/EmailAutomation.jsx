import { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000/api';

export default function EmailAutomation({ workflows, onRefresh }) {
  const [gmailStatus, setGmailStatus] = useState(null);
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState('');
  const [results, setResults] = useState([]);
  const [autoMode, setAutoMode] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchGmailStatus();
  }, []);

  useEffect(() => {
    let interval;
    if (autoMode && selectedWorkflow) {
      interval = setInterval(() => {
        processEmails();
      }, 30000); // Auto-process every 30 seconds
    }
    return () => clearInterval(interval);
  }, [autoMode, selectedWorkflow]);

  const fetchGmailStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/gmail/status`);
      const data = await res.json();
      setGmailStatus(data);
    } catch (err) {
      console.error('Failed to fetch Gmail status:', err);
    }
  };

  const connectGmail = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/gmail/connect`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Connection failed');
      await fetchGmailStatus();
      fetchEmails();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const disconnectGmail = async () => {
    try {
      await fetch(`${API_BASE}/gmail/disconnect`, { method: 'POST' });
      await fetchGmailStatus();
      setEmails([]);
    } catch (err) {
      console.error('Disconnect failed:', err);
    }
  };

  const fetchEmails = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/gmail/emails?max_results=5`);
      const data = await res.json();
      setEmails(data.emails || []);
    } catch (err) {
      console.error('Failed to fetch emails:', err);
    } finally {
      setLoading(false);
    }
  };

  const processEmail = async (email) => {
    if (!selectedWorkflow) {
      setError('Please select a workflow first');
      return;
    }

    setProcessing(true);
    try {
      const res = await fetch(`${API_BASE}/gmail/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_id: email.id,
          email: email,
          workflow_id: selectedWorkflow
        })
      });
      const data = await res.json();
      
      setResults(prev => [{
        email_id: email.id,
        subject: email.subject,
        timestamp: new Date().toISOString(),
        ...data.result
      }, ...prev].slice(0, 10));

      // Refresh to show feedback can be given
      if (onRefresh) onRefresh();
    } catch (err) {
      setError('Processing failed: ' + err.message);
    } finally {
      setProcessing(false);
    }
  };

  const processEmails = async () => {
    if (!selectedWorkflow) return;

    setProcessing(true);
    try {
      const res = await fetch(`${API_BASE}/gmail/auto-process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: selectedWorkflow,
          max_emails: 3
        })
      });
      const data = await res.json();
      
      // Add to results
      const newResults = data.results.map(r => ({
        ...r,
        timestamp: new Date().toISOString()
      }));
      setResults(prev => [...newResults, ...prev].slice(0, 20));

      if (onRefresh) onRefresh();
    } catch (err) {
      setError('Auto-process failed: ' + err.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="email-automation">
      <div className="section-header">
        <h2>📧 Email Automation</h2>
        <p className="section-subtitle">Connect Gmail and auto-respond with AI agents</p>
      </div>

      {error && (
        <div className="error-banner">
          <span>❌ {error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {/* Gmail Connection Status */}
      <div className="connection-card">
        <div className="connection-header">
          <div className="connection-icon">
            {gmailStatus?.authenticated ? '✅' : '📭'}
          </div>
          <div className="connection-info">
            <h3>Gmail Connection</h3>
            {gmailStatus?.authenticated ? (
              <p className="connected">Connected as {gmailStatus.user_email}</p>
            ) : gmailStatus?.needs_setup ? (
              <p className="needs-setup">credentials.json required</p>
            ) : (
              <p className="disconnected">Not connected - Using demo data</p>
            )}
          </div>
          <div className="connection-actions">
            {gmailStatus?.authenticated ? (
              <button className="btn-secondary" onClick={disconnectGmail}>
                Disconnect
              </button>
            ) : (
              <button 
                className="btn-primary" 
                onClick={connectGmail}
                disabled={loading || gmailStatus?.needs_setup}
              >
                {loading ? 'Connecting...' : 'Connect Gmail'}
              </button>
            )}
          </div>
        </div>

        {gmailStatus?.needs_setup && (
          <div className="setup-instructions">
            <h4>Setup Instructions:</h4>
            <ol>
              <li>Go to <a href="https://console.cloud.google.com" target="_blank" rel="noreferrer">Google Cloud Console</a></li>
              <li>Create a project and enable Gmail API</li>
              <li>Create OAuth 2.0 credentials (Desktop app)</li>
              <li>Download and save as <code>backend/credentials.json</code></li>
              <li>Refresh this page and click Connect</li>
            </ol>
          </div>
        )}
      </div>

      {/* Workflow Selection */}
      <div className="workflow-selector">
        <label>Select Workflow:</label>
        <select 
          value={selectedWorkflow} 
          onChange={(e) => setSelectedWorkflow(e.target.value)}
        >
          <option value="">-- Choose a workflow --</option>
          {workflows.map(w => (
            <option key={w.id} value={w.id}>{w.name}</option>
          ))}
        </select>

        <div className="auto-mode-toggle">
          <label>
            <input 
              type="checkbox" 
              checked={autoMode}
              onChange={(e) => setAutoMode(e.target.checked)}
              disabled={!selectedWorkflow}
            />
            Auto-process mode (every 30s)
          </label>
        </div>
      </div>

      {/* Email List */}
      <div className="email-section">
        <div className="section-title">
          <h3>📬 Incoming Emails</h3>
          <button 
            className="btn-secondary" 
            onClick={fetchEmails}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        <div className="email-list">
          {emails.length === 0 ? (
            <div className="empty-state">
              <p>No emails to display. Click Refresh to fetch emails.</p>
            </div>
          ) : (
            emails.map((email, idx) => (
              <div key={email.id || idx} className="email-card">
                <div className="email-header">
                  <span className="email-sender">{email.sender}</span>
                  <span className="email-date">{email.date || ''}</span>
                </div>
                <div className="email-subject">{email.subject}</div>
                <div className="email-snippet">{email.snippet || email.body?.slice(0, 100)}</div>
                <div className="email-actions">
                  <button 
                    className="btn-primary btn-sm"
                    onClick={() => processEmail(email)}
                    disabled={processing || !selectedWorkflow}
                  >
                    {processing ? '⏳ Processing...' : '🤖 Process with AI'}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Process All Button */}
      {emails.length > 0 && selectedWorkflow && (
        <div className="bulk-actions">
          <button 
            className="btn-primary btn-large"
            onClick={processEmails}
            disabled={processing}
          >
            {processing ? '⏳ Processing...' : `🚀 Process All ${emails.length} Emails`}
          </button>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="results-section">
          <h3>📊 Processing Results</h3>
          <div className="results-list">
            {results.map((result, idx) => (
              <div key={idx} className={`result-card ${result.status === 'error' ? 'error' : 'success'}`}>
                <div className="result-header">
                  <span className="result-subject">{result.subject}</span>
                  <span className={`result-status ${result.status}`}>
                    {result.status === 'processed' ? '✅' : '❌'} {result.status}
                  </span>
                </div>
                {result.selected_agent && (
                  <div className="result-agent">
                    <span className="agent-badge">🏆 {result.selected_agent || result.selected_agent_name}</span>
                  </div>
                )}
                {result.response_preview && (
                  <div className="result-preview">
                    {result.response_preview}
                  </div>
                )}
                {result.error && (
                  <div className="result-error">{result.error}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Auto Mode Status */}
      {autoMode && (
        <div className="auto-mode-status">
          <span className="pulse-dot"></span>
          Auto-processing active - checking every 30 seconds
        </div>
      )}
    </div>
  );
}
