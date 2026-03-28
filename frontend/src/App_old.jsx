import { useState, useEffect } from 'react';
import { getAgents, getWeights, setupDemo, getRunHistory } from './api';
import AgentBuilder from './components/AgentBuilder';
import AgentCard from './components/AgentCard';
import WorkflowCanvas from './components/WorkflowCanvas';
import ConflictDashboard from './components/ConflictDashboard';
import DecisionPanel from './components/DecisionPanel';
import FeedbackButtons from './components/FeedbackButtons';
import WeightChart from './components/WeightChart';
import LogViewer from './components/LogViewer';
import AutoTrigger from './components/AutoTrigger';
import './App.css';

function App() {
  const [agents, setAgents] = useState([]);
  const [weights, setWeights] = useState([]);
  const [activeTab, setActiveTab] = useState('workflow');
  const [workflowResult, setWorkflowResult] = useState(null);
  const [logs, setLogs] = useState([]);
  const [runHistory, setRunHistory] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [setupLoading, setSetupLoading] = useState(false);

  const fetchAgents = async () => {
    try {
      const data = await getAgents();
      setAgents(data);
    } catch (err) {
      console.error('Failed to fetch agents:', err);
    }
  };

  const fetchWeights = async () => {
    try {
      const data = await getWeights();
      setWeights(data);
    } catch (err) {
      console.error('Failed to fetch weights:', err);
    }
  };

  const fetchHistory = async () => {
    try {
      const data = await getRunHistory();
      setRunHistory(data);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  useEffect(() => {
    fetchAgents();
    fetchWeights();
    fetchHistory();
  }, []);

  const handleSetupDemo = async () => {
    setSetupLoading(true);
    try {
      await setupDemo();
      await fetchAgents();
      await fetchWeights();
    } catch (err) {
      console.error('Failed to setup demo:', err);
    } finally {
      setSetupLoading(false);
    }
  };

  const handleWorkflowComplete = (result) => {
    setWorkflowResult(result);
    setLogs(result.logs || []);
    setActiveTab('results');
    fetchHistory();
  };

  const handleFeedbackSubmitted = (newWeights) => {
    setWeights(newWeights);
    fetchAgents();
  };

  const workerAgents = agents.filter(a => a.type === 'worker');

  return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <h1 className="header-logo">🔥 FlexCode</h1>
          <span className="header-tagline">Zapier for Autonomous AI Teams</span>
        </div>
        <div className="header-actions">
          <AutoTrigger 
            agents={agents}
            onWorkflowComplete={handleWorkflowComplete}
            isRunning={isRunning}
            setIsRunning={setIsRunning}
          />
          <button 
            className="btn btn-primary"
            onClick={handleSetupDemo}
            disabled={setupLoading}
          >
            {setupLoading ? <span className="loading-spinner" /> : '⚡ Quick Demo Setup'}
          </button>
        </div>
      </header>

      <div className="main-layout">
        <aside className="sidebar">
          <div className="sidebar-section">
            <h3 className="sidebar-title">Create Agent</h3>
            <AgentBuilder onAgentCreated={fetchAgents} />
          </div>

          <div className="sidebar-section">
            <h3 className="sidebar-title">
              Agents ({agents.length})
            </h3>
            {agents.length === 0 ? (
              <div className="empty-state" style={{ padding: 'var(--space-md)' }}>
                <p style={{ fontSize: '0.875rem' }}>No agents yet. Create one or use Quick Demo Setup.</p>
              </div>
            ) : (
              <div className="agent-list">
                {agents.map(agent => (
                  <AgentCard 
                    key={agent.id} 
                    agent={agent} 
                    onDelete={fetchAgents}
                  />
                ))}
              </div>
            )}
          </div>

          <div className="sidebar-section" style={{ flex: 1 }}>
            <h3 className="sidebar-title">RL Weights</h3>
            <WeightChart weights={weights} />
          </div>
        </aside>

        <main className="main-content">
          <div className="tabs">
            <button 
              className={`tab ${activeTab === 'workflow' ? 'active' : ''}`}
              onClick={() => setActiveTab('workflow')}
            >
              🔄 Workflow
            </button>
            <button 
              className={`tab ${activeTab === 'results' ? 'active' : ''}`}
              onClick={() => setActiveTab('results')}
              disabled={!workflowResult}
            >
              📊 Results
            </button>
            <button 
              className={`tab ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              📜 History ({runHistory.length})
            </button>
          </div>

          <div className="tab-content">
            {activeTab === 'workflow' && (
              <WorkflowCanvas 
                agents={agents}
                onWorkflowComplete={handleWorkflowComplete}
                isRunning={isRunning}
                setIsRunning={setIsRunning}
              />
            )}

            {activeTab === 'results' && workflowResult && (
              <div className="slide-up">
                <div style={{ marginBottom: 'var(--space-lg)' }}>
                  <h2 style={{ marginBottom: 'var(--space-sm)' }}>
                    Workflow Results
                  </h2>
                  <span className={`badge badge-${workflowResult.classification?.toLowerCase()}`}>
                    {workflowResult.classification}
                  </span>
                </div>

                <h3 style={{ marginBottom: 'var(--space-md)', color: 'var(--text-secondary)' }}>
                  Competing Responses
                </h3>
                <ConflictDashboard 
                  workerOutputs={workflowResult.worker_outputs}
                  selectedAgent={workflowResult.selected_agent}
                />

                <DecisionPanel result={workflowResult} />

                <FeedbackButtons 
                  runId={workflowResult.run_id}
                  onFeedbackSubmitted={handleFeedbackSubmitted}
                  disabled={false}
                />
              </div>
            )}

            {activeTab === 'history' && (
              <div className="history-list">
                {runHistory.length === 0 ? (
                  <div className="empty-state">
                    <span className="empty-state-icon">📜</span>
                    <p>No workflow runs yet</p>
                  </div>
                ) : (
                  runHistory.map(run => (
                    <div key={run.id} className="history-item slide-up">
                      <div className="history-item-header">
                        <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>
                          {new Date(run.created_at).toLocaleString()}
                        </span>
                        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                          <span className={`badge badge-${run.classification?.toLowerCase()}`}>
                            {run.classification}
                          </span>
                          {run.feedback && (
                            <span className={`badge ${run.feedback === 'accept' ? 'badge-concise' : 'badge-urgent'}`}>
                              {run.feedback === 'accept' ? '✓ Accepted' : '✗ Rejected'}
                            </span>
                          )}
                        </div>
                      </div>
                      <p className="history-item-preview">
                        {run.input_data?.substring(0, 100)}...
                      </p>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          <LogViewer logs={logs} />
        </main>
      </div>
    </div>
  );
}

export default App;
