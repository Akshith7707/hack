import { useState } from 'react';
import { runWorkflow, getNextMockEmail, getGmailEmails } from '../api';

export default function WorkflowCanvas({ agents, onWorkflowComplete, isRunning, setIsRunning }) {
  const [inputData, setInputData] = useState('');
  const [error, setError] = useState('');
  const [gmailEmails, setGmailEmails] = useState([]);
  const [showGmailList, setShowGmailList] = useState(false);
  const [loadingGmail, setLoadingGmail] = useState(false);

  const hasRequiredAgents = () => {
    const types = agents.map(a => a.type);
    return types.includes('classifier') && 
           types.filter(t => t === 'worker').length >= 3 &&
           types.includes('supervisor') &&
           types.includes('decision');
  };

  const handleRun = async () => {
    if (!inputData.trim()) {
      setError('Please enter an email to process');
      return;
    }
    
    setError('');
    setIsRunning(true);
    
    try {
      const result = await runWorkflow(inputData);
      onWorkflowComplete(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const handleLoadMockEmail = async () => {
    try {
      const email = await getNextMockEmail();
      setInputData(email.formatted);
    } catch (err) {
      setError('No more mock emails available');
    }
  };

  const handleFetchGmail = async () => {
    setLoadingGmail(true);
    setError('');
    try {
      const emails = await getGmailEmails();
      setGmailEmails(emails);
      setShowGmailList(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingGmail(false);
    }
  };

  const handleSelectGmailEmail = (email) => {
    setInputData(`Subject: ${email.subject}\nFrom: ${email.sender}\n\n${email.snippet}`);
    setShowGmailList(false);
  };

  const pipelineNodes = [
    { icon: '📥', label: 'Input', active: false },
    { icon: '🏷️', label: 'Classifier', active: isRunning },
    { icon: '✍️', label: 'Workers (×3)', active: isRunning, parallel: true },
    { icon: '👁️', label: 'Supervisor', active: isRunning },
    { icon: '🎯', label: 'Decision', active: isRunning },
    { icon: '📤', label: 'Output', active: false }
  ];

  return (
    <div className="workflow-canvas fade-in">
      <div className="pipeline-visual">
        {pipelineNodes.map((node, idx) => (
          <div key={idx} style={{ display: 'flex', alignItems: 'center' }}>
            <div className={`pipeline-node ${node.active ? 'active glow' : ''}`}>
              <span className="pipeline-node-icon">{node.icon}</span>
              <span className="pipeline-node-label">{node.label}</span>
            </div>
            {idx < pipelineNodes.length - 1 && (
              <span className="pipeline-arrow" style={{ margin: '0 var(--space-sm)' }}>→</span>
            )}
          </div>
        ))}
      </div>

      <div className="workflow-input">
        <label style={{ marginBottom: 'var(--space-sm)' }}>
          Email to Process
        </label>
        <textarea
          placeholder="Paste an email here, use a mock email, or fetch from Gmail..."
          value={inputData}
          onChange={(e) => setInputData(e.target.value)}
          rows={6}
          disabled={isRunning}
        />
      </div>

      {error && (
        <p style={{ color: 'var(--accent-red)', fontSize: '0.875rem' }}>{error}</p>
      )}

      {/* Gmail Email List */}
      {showGmailList && gmailEmails.length > 0 && (
        <div className="glass-card" style={{ marginBottom: 'var(--space-lg)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-md)' }}>
            <h4 style={{ color: 'var(--accent-cyan)' }}>📬 Latest Gmail Emails</h4>
            <button className="btn btn-ghost btn-sm" onClick={() => setShowGmailList(false)}>✕ Close</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
            {gmailEmails.map((email) => (
              <div 
                key={email.id}
                onClick={() => handleSelectGmailEmail(email)}
                style={{
                  padding: 'var(--space-md)',
                  background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  border: '1px solid transparent'
                }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent-indigo)'}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = 'transparent'}
              >
                <div style={{ fontWeight: 600, marginBottom: 'var(--space-xs)' }}>{email.subject}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 'var(--space-xs)' }}>{email.sender}</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{email.snippet}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="workflow-actions">
        <button
          className="btn btn-primary btn-lg"
          onClick={handleRun}
          disabled={isRunning || !hasRequiredAgents()}
        >
          {isRunning ? (
            <>
              <span className="loading-spinner" />
              Processing...
            </>
          ) : (
            <>🚀 Run Workflow</>
          )}
        </button>
        
        <button
          className="btn btn-ghost"
          onClick={handleLoadMockEmail}
          disabled={isRunning}
        >
          📧 Use Mock Email
        </button>

        <button
          className="btn btn-success"
          onClick={handleFetchGmail}
          disabled={isRunning || loadingGmail}
        >
          {loadingGmail ? <span className="loading-spinner" /> : '📬 Fetch Gmail'}
        </button>

        {!hasRequiredAgents() && (
          <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Need: 1 classifier, 3 workers, 1 supervisor, 1 decision agent
          </span>
        )}
      </div>
    </div>
  );
}
