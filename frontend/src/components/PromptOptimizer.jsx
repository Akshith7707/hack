import { useState, useEffect } from 'react';
import {
  getAgentPerformance,
  getPendingSuggestions,
  applySuggestion,
  rejectSuggestion,
  getPromptHistory
} from '../api';
import './PromptOptimizer.css';

function PromptOptimizer({ agent, onUpdate }) {
  const [stats, setStats] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('stats');

  useEffect(() => {
    if (agent?.id) {
      loadData();
    }
  }, [agent?.id]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsData, suggestionsData, historyData] = await Promise.all([
        getAgentPerformance(agent.id),
        getPendingSuggestions(agent.id),
        getPromptHistory(agent.id)
      ]);
      setStats(statsData);
      setSuggestions(suggestionsData);
      setHistory(historyData);
    } catch (err) {
      console.error('Failed to load optimization data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async (suggestionId) => {
    try {
      await applySuggestion(suggestionId);
      setSuggestions(suggestions.filter(s => s.id !== suggestionId));
      onUpdate?.();
      loadData();
    } catch (err) {
      console.error('Failed to apply suggestion:', err);
    }
  };

  const handleReject = async (suggestionId) => {
    try {
      await rejectSuggestion(suggestionId);
      setSuggestions(suggestions.filter(s => s.id !== suggestionId));
    } catch (err) {
      console.error('Failed to reject suggestion:', err);
    }
  };

  if (!agent) {
    return (
      <div className="prompt-optimizer empty">
        <p>Select an agent to view optimization options</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="prompt-optimizer loading">
        <p>Loading performance data...</p>
      </div>
    );
  }

  return (
    <div className="prompt-optimizer">
      <div className="optimizer-header">
        <h3>Prompt Optimization</h3>
        <p className="agent-name">{agent.name}</p>
      </div>

      <div className="optimizer-tabs">
        <button
          className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          Performance
        </button>
        <button
          className={`tab-btn ${activeTab === 'suggestions' ? 'active' : ''}`}
          onClick={() => setActiveTab('suggestions')}
        >
          Suggestions {suggestions.length > 0 && `(${suggestions.length})`}
        </button>
        <button
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          History
        </button>
      </div>

      <div className="optimizer-content">
        {activeTab === 'stats' && stats && (
          <div className="stats-tab">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value">
                  {(stats.accept_rate * 100).toFixed(1)}%
                </div>
                <div className="stat-label">Accept Rate</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats.times_selected}</div>
                <div className="stat-label">Times Selected</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats.times_accepted}</div>
                <div className="stat-label">Accepted</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats.times_rejected}</div>
                <div className="stat-label">Rejected</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats.weight?.toFixed(2)}</div>
                <div className="stat-label">RL Weight</div>
              </div>
            </div>

            {stats.needs_optimization && (
              <div className="optimization-alert">
                <span className="alert-icon">!</span>
                <div className="alert-content">
                  <strong>Optimization Recommended</strong>
                  <p>This agent's accept rate is below 40%. Consider reviewing and improving its prompt.</p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'suggestions' && (
          <div className="suggestions-tab">
            {suggestions.length === 0 ? (
              <div className="empty-state">
                <p>No pending suggestions</p>
                <p className="hint">Suggestions are generated based on feedback patterns</p>
              </div>
            ) : (
              suggestions.map(suggestion => (
                <div key={suggestion.id} className="suggestion-card">
                  <div className="suggestion-header">
                    <span className="suggestion-date">
                      {new Date(suggestion.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="prompt-comparison">
                    <div className="prompt-column">
                      <h5>Current Prompt</h5>
                      <pre>{suggestion.current_prompt}</pre>
                    </div>
                    <div className="prompt-column suggested">
                      <h5>Suggested Prompt</h5>
                      <pre>{suggestion.suggested_prompt}</pre>
                    </div>
                  </div>

                  {suggestion.reasoning && (
                    <div className="suggestion-reasoning">
                      <h5>Why this change?</h5>
                      <p>{suggestion.reasoning}</p>
                    </div>
                  )}

                  <div className="suggestion-actions">
                    <button
                      className="btn-apply"
                      onClick={() => handleApply(suggestion.id)}
                    >
                      Apply Change
                    </button>
                    <button
                      className="btn-reject"
                      onClick={() => handleReject(suggestion.id)}
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div className="history-tab">
            {history.length === 0 ? (
              <div className="empty-state">
                <p>No prompt history</p>
              </div>
            ) : (
              history.map((version, index) => (
                <div key={version.id} className="history-item">
                  <div className="history-header">
                    <span className="version-badge">v{version.version}</span>
                    <span className="version-date">
                      {new Date(version.created_at).toLocaleString()}
                    </span>
                    {version.is_active && (
                      <span className="active-badge">Active</span>
                    )}
                  </div>
                  <pre className="version-prompt">{version.prompt_text}</pre>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default PromptOptimizer;
