export default function DecisionPanel({ result }) {
  if (!result) return null;

  const contextSignals = result.context_signals || {};

  return (
    <div className="decision-panel slide-up">
      <div className="decision-header">
        <span style={{ fontSize: '2rem' }}>🧠</span>
        <h3 className="decision-title">AI Decision</h3>
        <span className={`badge badge-${contextSignals.urgency?.toLowerCase() || 'informational'}`}>
          {contextSignals.urgency || 'UNKNOWN'}
        </span>
      </div>

      <div style={{ marginBottom: 'var(--space-lg)' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Selected Agent:</span>
        <span style={{ 
          marginLeft: 'var(--space-sm)', 
          color: 'var(--accent-cyan)',
          fontWeight: 600
        }}>
          {result.selected_agent_name}
        </span>
      </div>

      <div className="decision-output">
        <p>{result.final_output}</p>
      </div>

      <div className="decision-reason">
        <strong style={{ color: 'var(--text-primary)' }}>Reasoning:</strong>
        <p style={{ marginTop: 'var(--space-sm)' }}>{result.decision_reason}</p>
      </div>

      <div className="context-signals">
        <span className="badge" style={{ background: 'var(--bg-primary)' }}>
          🕐 {contextSignals.time_period || 'unknown'}
        </span>
        <span className="badge" style={{ background: 'var(--bg-primary)' }}>
          📝 {contextSignals.input_length || 0} words
        </span>
        {contextSignals.historical_preference && (
          <span className="badge" style={{ background: 'var(--bg-primary)' }}>
            ⭐ Prefers: {contextSignals.historical_preference}
          </span>
        )}
        {contextSignals.recent_rejections > 0 && (
          <span className="badge" style={{ background: 'rgba(239, 68, 68, 0.2)', color: 'var(--accent-red)' }}>
            ⚠️ {contextSignals.recent_rejections} recent rejections
          </span>
        )}
      </div>
    </div>
  );
}
