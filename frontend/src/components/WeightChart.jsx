export default function WeightChart({ weights }) {
  if (!weights || weights.length === 0) {
    return (
      <div className="empty-state" style={{ padding: 'var(--space-lg)' }}>
        <p style={{ fontSize: '0.875rem' }}>No worker weights yet</p>
      </div>
    );
  }

  const maxWeight = Math.max(...weights.map(w => w.weight));

  return (
    <div className="weight-chart">
      {weights.map((w, idx) => (
        <div key={w.agent_id || idx} className="weight-item slide-in" style={{ animationDelay: `${idx * 0.1}s` }}>
          <div className="weight-item-header">
            <span className="weight-item-name">
              <span className={`badge badge-${w.style}`} style={{ marginRight: 'var(--space-sm)' }}>
                {w.style}
              </span>
              {w.agent_name}
            </span>
            <span className="weight-item-value">
              {(w.weight * 100).toFixed(1)}%
            </span>
          </div>
          <div className="weight-bar" style={{ height: '8px' }}>
            <div 
              className="weight-bar-fill"
              style={{ 
                width: `${(w.weight / maxWeight) * 100}%`,
                background: w.weight === maxWeight 
                  ? 'var(--gradient-success)' 
                  : 'var(--gradient-primary)'
              }}
            />
          </div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            fontSize: '0.7rem',
            color: 'var(--text-muted)',
            marginTop: 'var(--space-xs)'
          }}>
            <span>Selected: {w.times_selected || 0}</span>
            <span style={{ color: 'var(--accent-green)' }}>✓ {w.times_accepted || 0}</span>
            <span style={{ color: 'var(--accent-red)' }}>✗ {w.times_rejected || 0}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
