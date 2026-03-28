import { useState } from 'react';
import { deleteWorkflow, runWorkflowById } from '../api';

function WorkflowDashboard({ workflows, executions, onCreateWorkflow, onEditWorkflow, onRefresh, onWorkflowExecuted }) {
  const [runningWorkflows, setRunningWorkflows] = useState(new Set());
  const [showInputModal, setShowInputModal] = useState(null); // workflow id
  const [inputText, setInputText] = useState('');
  const [activeWorkflowForModal, setActiveWorkflowForModal] = useState(null);

  // Calculate stats
  const totalRuns = executions.length;
  const activeWorkflows = workflows.filter(w => w.is_active).length;
  const avgRLScore = executions.length > 0 
    ? executions.reduce((acc, e) => acc + (e.score || 70), 0) / executions.length 
    : 75;

  // Demo input data per workflow type
  const getDemoInput = (workflow) => {
    const name = workflow.name.toLowerCase();
    if (name.includes('email')) {
      return `Subject: URGENT: Production database is down\nFrom: ops@company.com\n\nOur main production database has been unreachable for the past 15 minutes. All customer-facing services are affected. We need immediate action. The error logs show connection timeouts and the failover hasn't kicked in automatically.`;
    } else if (name.includes('support') || name.includes('triage')) {
      return `Subject: I've been charged twice for my subscription\nFrom: angry.customer@gmail.com\n\nHi, I noticed two charges of $49.99 on my credit card statement from your service this month. I only have one account and should only be charged once. I've been a loyal customer for 2 years and this is really frustrating. Please fix this immediately and process a refund for the duplicate charge.`;
    }
    return 'Type any text input here...';
  };

  const getPlaceholder = (workflow) => {
    if (!workflow) return 'Type your input here...';
    const name = workflow.name.toLowerCase();
    if (name.includes('email')) {
      return 'Paste an email here...\n\nExample:\nSubject: Meeting follow-up\nFrom: manager@company.com\n\nHey, can you send me the slides from today?';
    } else if (name.includes('support') || name.includes('triage')) {
      return 'Paste a customer support ticket here...\n\nExample:\nSubject: Can\'t login to my account\nFrom: user@gmail.com\n\nI\'ve been trying to log in but keep getting an error.';
    }
    return 'Type or paste any text input you want the AI agents to process...';
  };

  const handleRunWorkflow = async (workflowId, triggerInput) => {
    setShowInputModal(null);
    setRunningWorkflows(prev => new Set(prev).add(workflowId));
    try {
      // Fire-and-forget the API call, immediately navigate to results
      const runPromise = runWorkflowById(workflowId, { input: triggerInput });
      
      // Auto-navigate to Run Results page to show progress
      if (onWorkflowExecuted) {
        onWorkflowExecuted();
      }

      await runPromise;
      await onRefresh();
    } catch (err) {
      console.error('Failed to run workflow:', err);
    } finally {
      setRunningWorkflows(prev => {
        const next = new Set(prev);
        next.delete(workflowId);
        return next;
      });
    }
  };

  const handleDeleteWorkflow = async (workflowId) => {
    if (!confirm('Delete this workflow?')) return;
    try {
      await deleteWorkflow(workflowId);
      await onRefresh();
    } catch (err) {
      console.error('Failed to delete workflow:', err);
    }
  };

  const getTriggerIcon = (triggerType) => {
    const icons = {
      'webhook': '🔗',
      'manual': '🖱️',
      'scheduled': '⏰',
      'polling': '🔄'
    };
    return icons[triggerType] || '▶️';
  };

  const hasCompetitionNode = (workflow) => {
    return workflow.nodes?.some(n => n.type === 'competition');
  };

  const getWorkflowRuns = (workflowId) => {
    return executions.filter(e => e.workflow_id === workflowId);
  };

  const getWinRate = (workflowId) => {
    const runs = getWorkflowRuns(workflowId);
    if (runs.length === 0) return 0;
    const completed = runs.filter(r => r.status === 'completed');
    return completed.length / runs.length;
  };

  return (
    <div className="workflow-dashboard">
      {/* Top Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">🔄</div>
          <div className="stat-value">{workflows.length}</div>
          <div className="stat-label">Total Workflows</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">▶️</div>
          <div className="stat-value">{totalRuns}</div>
          <div className="stat-label">Total Runs</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-value">{activeWorkflows}</div>
          <div className="stat-label">Active Workflows</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🧠</div>
          <div className="stat-value">{avgRLScore.toFixed(0)}%</div>
          <div className="stat-label">Avg RL Score</div>
        </div>
      </div>

      {/* Workflows Header */}
      <div className="section-header">
        <h2 className="section-title">My Workflows</h2>
        <button className="btn btn-primary" onClick={onCreateWorkflow}>
          <span>➕</span>
          Create Workflow
        </button>
      </div>

      {/* Workflows Grid */}
      <div className="workflow-grid">
        {workflows.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📋</div>
            <h3>No workflows yet</h3>
            <p>Create your first automated workflow with competing AI agents</p>
            <button className="btn-primary" onClick={onCreateWorkflow}>
              ➕ Create Workflow
            </button>
          </div>
        ) : (
          workflows.map(workflow => {
            const runs = getWorkflowRuns(workflow.id);
            const lastRun = runs[0];
            const winRate = getWinRate(workflow.id);
            const isLearning = hasCompetitionNode(workflow);
            const isRunning = runningWorkflows.has(workflow.id);

            return (
              <div key={workflow.id} className="workflow-card">
                {/* Header */}
                <div className="workflow-card-header">
                  <div className="workflow-title-row">
                    <span className="workflow-trigger-icon">
                      {getTriggerIcon(workflow.trigger_type)}
                    </span>
                    <h3 className="workflow-name">{workflow.name}</h3>
                    {isLearning && (
                      <span className="learning-badge">
                        🧠 Learning
                      </span>
                    )}
                  </div>
                  <span className={`status-badge ${workflow.is_active ? 'active' : 'paused'}`}>
                    {workflow.is_active ? '✓ Active' : '⏸ Paused'}
                  </span>
                </div>

                {/* Description */}
                {workflow.description && (
                  <p className="workflow-description">{workflow.description}</p>
                )}

                {/* Stats Row */}
                <div className="workflow-stats">
                  <div className="workflow-stat">
                    <span className="stat-icon">📦</span>
                    <span>{workflow.nodes?.length || 0} nodes</span>
                  </div>
                  <div className="workflow-stat">
                    <span className="stat-icon">▶️</span>
                    <span>{runs.length} runs</span>
                  </div>
                  {lastRun && (
                    <div className="workflow-stat">
                      <span className="stat-icon">⏱️</span>
                      <span>{new Date(lastRun.started_at).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>

                {/* Win Rate Sparkline (if learning) */}
                {isLearning && runs.length > 0 && (
                  <div className="rl-progress">
                    <div className="rl-label">RL Win Rate</div>
                    <div className="weight-bar">
                      <div className="weight-track">
                        <div 
                          className="weight-fill" 
                          style={{ width: `${winRate * 100}%` }}
                        />
                      </div>
                      <div className="weight-value">{(winRate * 100).toFixed(0)}%</div>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="workflow-card-actions">
                  <button 
                    className="btn-run" 
                    onClick={() => {
                      setInputText('');
                      setActiveWorkflowForModal(workflow);
                      setShowInputModal(workflow.id);
                    }}
                    disabled={isRunning}
                    title="Run workflow"
                  >
                    {isRunning ? '⏳ Running...' : '▶️ Run'}
                  </button>
                  <button 
                    className="btn-icon" 
                    onClick={() => onEditWorkflow(workflow)}
                    title="Edit workflow"
                  >
                    ✏️
                  </button>
                  <button 
                    className="btn-icon btn-danger" 
                    onClick={() => handleDeleteWorkflow(workflow.id)}
                    title="Delete workflow"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Input Modal */}
      {showInputModal && (
        <div className="modal-overlay" onClick={() => setShowInputModal(null)}>
          <div className="input-modal-content" onClick={e => e.stopPropagation()}>
            <div className="input-modal-header">
              <h2 className="input-modal-title">📥 Trigger Input</h2>
              <button className="input-modal-close" onClick={() => setShowInputModal(null)}>×</button>
            </div>
            <p className="text-secondary" style={{marginBottom: '1rem'}}>
              Type or paste any data you want the AI agents to process
            </p>
            <textarea
              className="input"
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              rows={8}
              placeholder={getPlaceholder(activeWorkflowForModal)}
              autoFocus
            />
            <div className="input-modal-actions">
              <button 
                className="btn btn-secondary" 
                onClick={() => setInputText(getDemoInput(activeWorkflowForModal))}
                title="Fill with sample data for demo"
              >
                📋 Load Example
              </button>
              <div style={{flex:1}} />
              <button className="btn btn-ghost" onClick={() => setShowInputModal(null)}>
                Cancel
              </button>
              <button 
                className="btn btn-primary"
                onClick={() => handleRunWorkflow(showInputModal, inputText)}
                disabled={!inputText.trim()}
              >
                ⚡ Execute Pipeline
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default WorkflowDashboard;
