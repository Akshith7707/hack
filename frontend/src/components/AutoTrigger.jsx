import { useState, useEffect, useRef } from 'react';
import { getNextMockEmail, runWorkflow } from '../api';

export default function AutoTrigger({ agents, onWorkflowComplete, isRunning, setIsRunning }) {
  const [autoMode, setAutoMode] = useState(false);
  const [countdown, setCountdown] = useState(15);
  const intervalRef = useRef(null);
  const countdownRef = useRef(null);

  const hasRequiredAgents = () => {
    const types = agents.map(a => a.type);
    return types.includes('classifier') && 
           types.filter(t => t === 'worker').length >= 3 &&
           types.includes('supervisor') &&
           types.includes('decision');
  };

  const runAutoWorkflow = async () => {
    if (isRunning || !hasRequiredAgents()) return;
    
    try {
      const email = await getNextMockEmail();
      setIsRunning(true);
      const result = await runWorkflow(email.formatted);
      onWorkflowComplete(result);
    } catch (err) {
      console.error('Auto workflow failed:', err);
    } finally {
      setIsRunning(false);
    }
  };

  useEffect(() => {
    if (autoMode && !isRunning) {
      setCountdown(15);
      
      countdownRef.current = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            runAutoWorkflow();
            return 15;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
      }
    }

    return () => {
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
      }
    };
  }, [autoMode, isRunning]);

  const toggleAutoMode = () => {
    if (!hasRequiredAgents()) return;
    setAutoMode(!autoMode);
  };

  return (
    <div className="auto-trigger">
      <div 
        className={`toggle ${autoMode ? 'active' : ''}`}
        onClick={toggleAutoMode}
        style={{ opacity: hasRequiredAgents() ? 1 : 0.5, cursor: hasRequiredAgents() ? 'pointer' : 'not-allowed' }}
      >
        <div className="toggle-handle" />
      </div>
      <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
        Auto Mode
      </span>
      {autoMode && !isRunning && (
        <span className="countdown">
          Next run in {countdown}s
        </span>
      )}
      {autoMode && isRunning && (
        <span className="countdown" style={{ color: 'var(--accent-indigo)' }}>
          <span className="loading-spinner" style={{ width: '12px', height: '12px', marginRight: 'var(--space-sm)' }} />
          Processing...
        </span>
      )}
    </div>
  );
}
