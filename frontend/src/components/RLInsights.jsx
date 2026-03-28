import { resetAgentDrift } from '../api';

function RLInsights({ agents, weights, weightsHistory, executions }) {
  const handleResetDrift = async (agentId) => {
    if (!confirm('Reset drift flag for this agent?')) return;
    try {
      await resetAgentDrift(agentId);
      window.location.reload();
    } catch (err) {
      console.error('Failed to reset drift:', err);
    }
  };

  // Calculate insights
  const totalFeedback = weights.reduce((acc, w) => acc + (w.times_selected || 0), 0);
  const avgAcceptRate = weights.length > 0
    ? weights.reduce((acc, w) => acc + (w.accept_rate || 0), 0) / weights.length
    : 0;

  const topAgent = weights.reduce((best, current) => {
    return (current.accept_rate || 0) > (best.accept_rate || 0) ? current : best;
  }, weights[0] || {});

  return (
    <div className="rl-insights">
      <h1>🧠 RL Insights - Learning Dashboard</h1>

      {/* Key Stats */}
      <div className="insights-stats">
        <div className="insight-card">
          <div className="insight-icon">📊</div>
          <div className="insight-content">
            <div className="insight-value">{totalFeedback}</div>
            <div className="insight-label">Total Feedback</div>
          </div>
        </div>
        <div className="insight-card">
          <div className="insight-icon">✅</div>
          <div className="insight-content">
            <div className="insight-value">{(avgAcceptRate * 100).toFixed(0)}%</div>
            <div className="insight-label">Avg Accept Rate</div>
          </div>
        </div>
        <div className="insight-card gradient-bg">
          <div className="insight-icon">🏆</div>
          <div className="insight-content">
            <div className="insight-value">{topAgent?.agent_name || 'N/A'}</div>
            <div className="insight-label">Top Performer</div>
          </div>
        </div>
        <div className="insight-card">
          <div className="insight-icon">🎯</div>
          <div className="insight-content">
            <div className="insight-value">{agents.length}</div>
            <div className="insight-label">Active Agents</div>
          </div>
        </div>
      </div>

      {/* Key Insight Card */}
      {topAgent && topAgent.accept_rate > 0.5 && (
        <div className="key-insight-card">
          <div className="key-insight-icon">💡</div>
          <div className="key-insight-content">
            <h3>Key Insight</h3>
            <p>
              Your team has learned that <strong>{topAgent.agent_name}</strong> performs 
              best with a <strong>{(topAgent.accept_rate * 100).toFixed(0)}%</strong> acceptance 
              rate. The system will prefer this agent in similar contexts.
            </p>
          </div>
        </div>
      )}

      {/* Agent Leaderboard */}
      <div className="leaderboard-section">
        <h2>🏆 Agent Leaderboard</h2>
        <div className="leaderboard-table">
          <div className="leaderboard-header">
            <div className="col-rank">#</div>
            <div className="col-agent">Agent</div>
            <div className="col-weight">RL Weight</div>
            <div className="col-rate">Accept Rate</div>
            <div className="col-stats">Stats</div>
            <div className="col-actions">Actions</div>
          </div>
          
          {weights
            .sort((a, b) => (b.accept_rate || 0) - (a.accept_rate || 0))
            .map((agent, idx) => (
              <div key={agent.agent_id} className="leaderboard-row">
                <div className="col-rank">
                  <span className={`rank-badge rank-${idx + 1}`}>{idx + 1}</span>
                </div>
                <div className="col-agent">
                  <span className="agent-name">{agent.agent_name}</span>
                  {agent.style && <span className="agent-style">{agent.style}</span>}
                  {agent.drift_flag && (
                    <span className="drift-warning" title={agent.drift_suggestion}>
                      ⚠️ Drifting
                    </span>
                  )}
                </div>
                <div className="col-weight">
                  <div className="weight-bar">
                    <div 
                      className="weight-fill" 
                      style={{ width: `${(agent.weight || 0) * 100}%` }}
                    />
                  </div>
                  <span className="weight-value">{((agent.weight || 0) * 100).toFixed(1)}%</span>
                </div>
                <div className="col-rate">
                  <span className={`rate-badge rate-${agent.accept_rate > 0.7 ? 'high' : agent.accept_rate > 0.4 ? 'mid' : 'low'}`}>
                    {((agent.accept_rate || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="col-stats">
                  <span className="stat-item">
                    ✓ {agent.times_accepted || 0}
                  </span>
                  <span className="stat-item">
                    ✗ {agent.times_rejected || 0}
                  </span>
                  <span className="stat-item">
                    ∑ {agent.total_runs || 0}
                  </span>
                </div>
                <div className="col-actions">
                  {agent.drift_flag && (
                    <button 
                      className="btn-reset-drift"
                      onClick={() => handleResetDrift(agent.agent_id)}
                      title="Reset drift flag"
                    >
                      🔄
                    </button>
                  )}
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Weight Evolution Chart */}
      {weightsHistory && weightsHistory.history && (
        <div className="weight-evolution-section">
          <h2>📈 Weight Evolution Over Time</h2>
          <div className="chart-placeholder">
            <p>Weight evolution chart showing how each agent's weight changed over runs</p>
            <div className="chart-legend">
              {Object.keys(weightsHistory.history).map((agentId, idx) => {
                const agent = weights.find(w => w.agent_id === agentId);
                return (
                  <div key={agentId} className="legend-item">
                    <div 
                      className="legend-color" 
                      style={{ 
                        backgroundColor: `hsl(${idx * 60}, 70%, 60%)` 
                      }}
                    />
                    <span>{agent?.agent_name || agentId}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Feedback History Timeline */}
      <div className="feedback-history-section">
        <h2>📜 Recent Feedback History</h2>
        <div className="timeline">
          {executions.slice(0, 10).map(exec => (
            <div key={exec.id} className="timeline-item">
              <div className="timeline-dot" />
              <div className="timeline-content">
                <div className="timeline-time">
                  {new Date(exec.started_at).toLocaleString()}
                </div>
                <div className="timeline-agent">
                  {exec.selected_agent_name || 'Unknown Agent'}
                </div>
                <div className={`timeline-status status-${exec.status}`}>
                  {exec.status}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default RLInsights;
