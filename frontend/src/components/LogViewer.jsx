import { useEffect, useRef } from 'react';

export default function LogViewer({ logs }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  const getAgentEmoji = (type) => {
    switch (type) {
      case 'classifier': return '🏷️';
      case 'worker': return '✍️';
      case 'supervisor': return '👁️';
      case 'decision': return '🎯';
      default: return '🤖';
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  if (!logs || logs.length === 0) {
    return (
      <div className="log-viewer" ref={containerRef}>
        <div className="empty-state" style={{ padding: 'var(--space-xl)' }}>
          <span className="empty-state-icon">📋</span>
          <p>Run a workflow to see agent logs here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="log-viewer" ref={containerRef}>
      {logs.map((log, idx) => (
        <div key={idx} className="log-entry">
          <span className="log-avatar">{getAgentEmoji(log.agent_type)}</span>
          <div className="log-content">
            <div className="log-header">
              <span className="log-name">{log.agent_name}</span>
              <span className={`badge badge-${log.agent_type}`}>{log.agent_type}</span>
              <span className="log-time">{formatTime(log.timestamp)}</span>
            </div>
            <p className="log-output">
              {log.output_preview || log.output_full?.substring(0, 200) + '...'}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
