export default function ConflictDashboard({ workerOutputs, selectedAgent }) {
  if (!workerOutputs || workerOutputs.length === 0) return null;

  const getScoreClass = (score) => {
    if (score >= 80) return 'high';
    if (score >= 60) return 'medium';
    return 'low';
  };

  return (
    <div className="conflict-dashboard">
      {workerOutputs.map((output, idx) => {
        const isWinner = output.agent_id === selectedAgent || 
                         output.agent_name.toLowerCase().includes(selectedAgent?.toLowerCase() || '');
        
        return (
          <div 
            key={output.agent_id || idx}
            className={`conflict-card slide-up ${isWinner ? 'winner' : ''}`}
            style={{ animationDelay: `${idx * 0.1}s` }}
          >
            <div className="conflict-card-header">
              <div>
                <h4 style={{ marginBottom: 'var(--space-xs)' }}>{output.agent_name}</h4>
                <span className={`badge badge-${output.style}`}>{output.style}</span>
                {isWinner && <span className="winner-badge" style={{ marginLeft: 'var(--space-sm)' }}>WINNER</span>}
              </div>
              <div className={`conflict-card-score ${getScoreClass(output.score)}`}>
                {output.score}
              </div>
            </div>
            
            <div className="conflict-card-output">
              {output.output}
            </div>
          </div>
        );
      })}
    </div>
  );
}
