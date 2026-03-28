import { useState, useEffect, useCallback } from 'react';
import { 
  getAgents, getWeights, getWeightsWithHistory, setupDemo, 
  getRunHistory, getWorkflows, getExecutions 
} from './api';
import WorkflowDashboard from './components/WorkflowDashboard';
import WorkflowEditor from './components/WorkflowEditor';
import RunResults from './components/RunResults';
import RLInsights from './components/RLInsights';
import EmailAutomation from './components/EmailAutomation';
import './App.css';

// Scroll reveal observer for animations
const useScrollReveal = () => {
  useEffect(() => {
    const reveals = document.querySelectorAll('.reveal');
    
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('active');
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    );
    
    reveals.forEach((reveal) => observer.observe(reveal));
    
    return () => reveals.forEach((reveal) => observer.unobserve(reveal));
  }, []);
};

function App() {
  const [currentPage, setCurrentPage] = useState('workflows'); // workflows, editor, results, insights, emails
  const [agents, setAgents] = useState([]);
  const [weights, setWeights] = useState([]);
  const [weightsHistory, setWeightsHistory] = useState(null);
  const [workflows, setWorkflows] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [setupLoading, setSetupLoading] = useState(false);

  // Enable scroll reveal animations
  useScrollReveal();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [agentsData, weightsData, workflowsData, executionsData] = await Promise.all([
        getAgents().catch(() => []),
        getWeights().catch(() => []),
        getWorkflows().catch(() => []),
        getExecutions().catch(() => [])
      ]);
      
      setAgents(agentsData);
      setWeights(weightsData);
      setWorkflows(workflowsData);
      setExecutions(executionsData);
    } catch (err) {
      console.error('Failed to load data:', err);
    }
  };

  const loadWeightsHistory = async () => {
    try {
      const data = await getWeightsWithHistory();
      setWeightsHistory(data);
    } catch (err) {
      console.error('Failed to load weights history:', err);
    }
  };

  const handleSetupDemo = async () => {
    setSetupLoading(true);
    try {
      await setupDemo();
      await loadData();
    } catch (err) {
      console.error('Demo setup failed:', err);
    } finally {
      setSetupLoading(false);
    }
  };

  const handleCreateWorkflow = () => {
    setSelectedWorkflow(null);
    setCurrentPage('editor');
  };

  const handleEditWorkflow = (workflow) => {
    setSelectedWorkflow(workflow);
    setCurrentPage('editor');
  };

  const handleViewExecution = (execution) => {
    setSelectedExecution(execution);
    setCurrentPage('results');
  };

  const handleWorkflowExecuted = async () => {
    // Switch to results page immediately to show progress
    setCurrentPage('results');
    setSelectedExecution(null); // will auto-select latest
    // Refresh data to get the new execution
    await loadData();
  };

  const handleViewInsights = () => {
    loadWeightsHistory();
    setCurrentPage('insights');
  };

  return (
    <div className="app">
      {/* Top Navigation */}
      <nav className="top-nav">
        <div className="nav-brand">
          <span className="brand-icon">⚡</span>
          <span className="brand-name">FlexCode</span>
          <span className="brand-tagline">Zapier + Reinforcement Learning</span>
        </div>
        
        <div className="nav-tabs">
          <button 
            className={`nav-tab ${currentPage === 'workflows' ? 'active' : ''}`}
            onClick={() => setCurrentPage('workflows')}
          >
            <span className="nav-icon">🔄</span>
            Workflows
          </button>
          <button 
            className={`nav-tab ${currentPage === 'emails' ? 'active' : ''}`}
            onClick={() => setCurrentPage('emails')}
          >
            <span className="nav-icon">📧</span>
            Email Automation
          </button>
          <button 
            className={`nav-tab ${currentPage === 'results' ? 'active' : ''}`}
            onClick={() => setCurrentPage('results')}
          >
            <span className="nav-icon">📊</span>
            Run Results
          </button>
          <button 
            className={`nav-tab ${currentPage === 'insights' ? 'active' : ''}`}
            onClick={handleViewInsights}
          >
            <span className="nav-icon">🧠</span>
            RL Insights
          </button>
          <button 
            className={`nav-tab ${currentPage === 'history' ? 'active' : ''}`}
            onClick={() => {
              loadData();
              setCurrentPage('history');
            }}
          >
            <span className="nav-icon">📜</span>
            History
          </button>
        </div>

        {agents.length === 0 && (
          <button 
            className="btn-setup-demo"
            onClick={handleSetupDemo}
            disabled={setupLoading}
          >
            {setupLoading ? 'Setting up...' : '🚀 Quick Setup'}
          </button>
        )}
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {currentPage === 'workflows' && (
          <WorkflowDashboard
            workflows={workflows}
            executions={executions}
            onCreateWorkflow={handleCreateWorkflow}
            onEditWorkflow={handleEditWorkflow}
            onRefresh={loadData}
            onWorkflowExecuted={handleWorkflowExecuted}
          />
        )}

        {currentPage === 'editor' && (
          <WorkflowEditor
            workflow={selectedWorkflow}
            agents={agents}
            onBack={() => setCurrentPage('workflows')}
            onSave={loadData}
          />
        )}

        {currentPage === 'results' && (
          <RunResults
            execution={selectedExecution}
            executions={executions}
            weights={weights}
            onSelectExecution={handleViewExecution}
            onRefresh={loadData}
          />
        )}

        {currentPage === 'insights' && (
          <RLInsights
            agents={agents}
            weights={weights}
            weightsHistory={weightsHistory}
            executions={executions}
          />
        )}

        {currentPage === 'history' && (
          <div className="history-page">
            <h1>Execution History</h1>
            <div className="executions-list">
              {executions.map(exec => (
                <div 
                  key={exec.id} 
                  className="execution-card"
                  onClick={() => handleViewExecution(exec)}
                >
                  <div className="exec-header">
                    <span className={`status-badge status-${exec.status}`}>
                      {exec.status}
                    </span>
                    <span className="exec-time">
                      {new Date(exec.started_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="exec-workflow">{exec.workflow_name || 'Manual Run'}</div>
                  {exec.selected_agent_name && (
                    <div className="exec-agent">
                      Selected: {exec.selected_agent_name}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
