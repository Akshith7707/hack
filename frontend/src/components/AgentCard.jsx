import { deleteAgent } from '../api';

export default function AgentCard({ agent, onDelete }) {
  const handleDelete = async () => {
    if (confirm(`Delete ${agent.name}?`)) {
      await deleteAgent(agent.id);
      onDelete();
    }
  };

  const weightPercent = agent.weight ? (agent.weight * 100).toFixed(1) : null;

  return (
    <div className={`agent-card ${agent.type} slide-up`}>
      <button 
        className="btn btn-icon btn-ghost agent-card-delete"
        onClick={handleDelete}
        title="Delete agent"
      >
        ✕
      </button>
      
      <div className="agent-card-header">
        <span className="agent-card-name">{agent.name}</span>
        <div className="agent-card-badges">
          <span className={`badge badge-${agent.type}`}>{agent.type}</span>
          {agent.style && (
            <span className={`badge badge-${agent.style}`}>{agent.style}</span>
          )}
        </div>
      </div>
      
      <p className="agent-card-goal">{agent.goal}</p>
      
      {weightPercent && (
        <div className="weight-bar">
          <div 
            className="weight-bar-fill"
            style={{ width: `${weightPercent}%` }}
          />
        </div>
      )}
      
      {weightPercent && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          marginTop: 'var(--space-xs)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)'
        }}>
          <span>Weight: {weightPercent}%</span>
          <span>
            ✓{agent.times_accepted || 0} / ✗{agent.times_rejected || 0}
          </span>
        </div>
      )}
    </div>
  );
}
