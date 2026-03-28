import { useState, useEffect, useRef } from 'react';
import { getExecution, getExecutions, submitExecutionFeedback } from '../api';

function RunResults({ execution, executions, weights, onSelectExecution, onRefresh }) {
  const [selectedExec, setSelectedExec] = useState(execution);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pipelineStage, setPipelineStage] = useState(0);
  const [isPolling, setIsPolling] = useState(false);
  const pollingRef = useRef(null);

  useEffect(() => {
    if (execution) {
      // Explicit execution selected (e.g., from History page)
      loadExecutionDetails(execution.id);
    } else {
      // No specific execution selected — we just navigated here from Execute Pipeline
      // Always start polling for the newest result
      startPollingForNew();
    }

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [execution]);

  const startPollingForNew = () => {
    setIsPolling(true);
    setPipelineStage(0);

    // Remember IDs we already know about so we only react to NEW ones
    const knownIds = new Set(executions.map(e => e.id));

    // Animate pipeline stages
    const stageTimer = setInterval(() => {
      setPipelineStage(prev => (prev < 4 ? prev + 1 : prev));
    }, 3000);

    pollingRef.current = setInterval(async () => {
      try {
        const latestExecs = await getExecutions(10);
        if (latestExecs.length > 0) {
          // Find a NEW execution we haven't seen before
          const newExec = latestExecs.find(e => !knownIds.has(e.id));
          
          if (newExec && (newExec.status === 'completed' || newExec.status === 'failed')) {
            clearInterval(pollingRef.current);
            clearInterval(stageTimer);
            setIsPolling(false);
            await onRefresh();
            loadExecutionDetails(newExec.id);
          } else if (!newExec) {
            // No new execution yet, keep waiting
          }
        }
      } catch (e) {
        // keep polling
      }
    }, 2000);
  };

  const startPolling = (execId) => {
    setIsPolling(true);
    setPipelineStage(0);

    const stageTimer = setInterval(() => {
      setPipelineStage(prev => (prev < 4 ? prev + 1 : prev));
    }, 3000);

    pollingRef.current = setInterval(async () => {
      try {
        const data = await getExecution(execId);
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(pollingRef.current);
          clearInterval(stageTimer);
          setIsPolling(false);
          setSelectedExec(data);
          await onRefresh();
        }
      } catch (e) {
        // keep polling
      }
    }, 2000);
  };

  const loadExecutionDetails = async (execId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getExecution(execId);
      setSelectedExec(data);
    } catch (err) {
      console.error('Failed to load execution:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (action) => {
    if (!selectedExec) return;
    
    try {
      await submitExecutionFeedback(selectedExec.id, action);
      setFeedbackSubmitted(true);
      await onRefresh();
      
      setTimeout(() => setFeedbackSubmitted(false), 2000);
    } catch (err) {
      console.error('Failed to submit feedback:', err);
      setError('Failed to submit feedback: ' + err.message);
    }
  };

  // ===== PIPELINE PROGRESS VIEW =====
  if (isPolling) {
    const stages = [
      { icon: '📥', label: 'Receiving Input', desc: 'Parsing trigger data...' },
      { icon: '🔍', label: 'Analyzing', desc: 'Classifier categorizing input...' },
      { icon: '⚔️', label: 'Agents Competing', desc: '3 agents generating responses in parallel...' },
      { icon: '📊', label: 'Scoring', desc: 'Reviewer evaluating all responses...' },
      { icon: '🏆', label: 'Picking Winner', desc: 'Decision agent selecting the best...' },
    ];

    return (
      <div className="run-results">
        <div className="pipeline-progress">
          <h1>⚡ Pipeline Running</h1>
          <p className="pipeline-subtitle">AI agents are competing to give you the best response</p>
          
          <div className="pipeline-stages">
            {stages.map((stage, idx) => (
              <div 
                key={idx} 
                className={`pipeline-stage ${idx < pipelineStage ? 'done' : ''} ${idx === pipelineStage ? 'active' : ''} ${idx > pipelineStage ? 'pending' : ''}`}
              >
                <div className="stage-indicator">
                  {idx < pipelineStage ? '✅' : idx === pipelineStage ? stage.icon : '⏳'}
                </div>
                <div className="stage-info">
                  <div className="stage-label">{stage.label}</div>
                  <div className="stage-desc">
                    {idx === pipelineStage ? stage.desc : idx < pipelineStage ? 'Complete' : 'Waiting...'}
                  </div>
                </div>
                {idx === pipelineStage && <div className="stage-pulse" />}
              </div>
            ))}
          </div>

          <div className="pipeline-timer">
            <div className="loading-spinner" />
            <span>This usually takes 15-30 seconds...</span>
          </div>
        </div>
      </div>
    );
  }

  // ===== EMPTY STATE =====
  if (!selectedExec && executions.length === 0) {
    return (
      <div className="run-results empty">
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <h3>No execution results yet</h3>
          <p>Run a workflow to see the AI agents compete!</p>
        </div>
      </div>
    );
  }

  const latestExec = selectedExec || executions[0];
  
  // Parse results - handle both object and string formats
  let results = {};
  if (latestExec?.results) {
    if (typeof latestExec.results === 'string') {
      try {
        results = JSON.parse(latestExec.results);
      } catch (e) {
        console.error('Failed to parse results:', e);
      }
    } else {
      results = latestExec.results;
    }
  }
  
  // Look for competition results under multiple possible keys
  const competitionResults = results.compete || results.competition || results.final || {};
  const allOutputs = competitionResults.all_outputs || [];
  const scores = competitionResults.scores || {};

  // Also check if we have outputs directly in results
  const hasCompetition = allOutputs.length > 0;

  return (
    <div className="run-results">
      <div className="results-header">
        <h1>🎯 Run Results</h1>
        <select 
          className="execution-selector"
          value={latestExec?.id || ''}
          onChange={(e) => {
            const exec = executions.find(ex => ex.id === e.target.value);
            if (exec) {
              loadExecutionDetails(exec.id);
            }
          }}
        >
          {executions.map(exec => (
            <option key={exec.id} value={exec.id}>
              {new Date(exec.started_at).toLocaleString()} - {exec.status}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="loading-banner">
          <div className="loading-spinner" />
          Loading execution details...
        </div>
      )}

      {error && (
        <div className="error-banner">
          ❌ {error}
        </div>
      )}

      {/* Status Banner */}
      <div className={`status-banner status-${latestExec?.status}`}>
        <span className="status-icon">
          {latestExec?.status === 'completed' && '✅'}
          {latestExec?.status === 'running' && '⏳'}
          {latestExec?.status === 'failed' && '❌'}
        </span>
        <span>Status: <strong>{latestExec?.status}</strong></span>
        {latestExec?.selected_agent_name && (
          <span className="winner-info">| Winner: <strong>{latestExec.selected_agent_name}</strong></span>
        )}
        <span className="status-time">
          {new Date(latestExec?.started_at).toLocaleString()}
        </span>
      </div>

      {/* Error details for failed executions */}
      {latestExec?.status === 'failed' && (
        <div className="error-details">
          <h3>❌ Execution Failed</h3>
          <p>The workflow encountered an error. Check the logs below for details.</p>
          {results.error && (
            <pre className="error-message">{results.error}</pre>
          )}
        </div>
      )}

      {/* The Arena - Competing Agents */}
      {hasCompetition && (
        <div className="arena-section">
          <h2>⚔️ The Arena - Competing Agents</h2>
          <div className="arena-grid">
            {allOutputs.map((output, idx) => {
              const isWinner = output.agent_id === latestExec.selected_agent_id ||
                               output.agent_name === latestExec.selected_agent_name;
              const score = scores[idx + 1] || output.score || 70;
              const agentWeight = weights.find(w => w.agent_id === output.agent_id);
              const weight = agentWeight?.weight || 0.33;

              return (
                <div 
                  key={output.agent_id || idx} 
                  className={`arena-card ${isWinner ? 'winner' : 'loser'}`}
                >
                  {isWinner && <div className="winner-badge">✨ Winner</div>}
                  
                  <div className="arena-card-header">
                    <h3>{output.agent_name || `Agent ${idx + 1}`}</h3>
                    <span className="agent-style-badge">{output.style || 'default'}</span>
                  </div>

                  <div className="arena-metrics">
                    <div className="metric">
                      <span className="metric-label">Score</span>
                      <span className="metric-value">{score}/100</span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">RL Weight</span>
                      <span className="metric-value">{(weight * 100).toFixed(0)}%</span>
                    </div>
                  </div>

                  <div className="arena-output">
                    {output.output || 'No output'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Decision Reasoning */}
      {competitionResults.reason && (
        <div className="decision-panel">
          <h3>🎯 Decision Reasoning</h3>
          <blockquote className="decision-quote">
            {competitionResults.reason}
          </blockquote>
        </div>
      )}

      {/* Final Output */}
      {(latestExec?.final_output || competitionResults.final_output) && (
        <div className="final-output-section">
          <h3>📤 Final Output</h3>
          <div className="final-output-box">
            {latestExec.final_output || competitionResults.final_output}
          </div>
        </div>
      )}

      {/* Feedback Buttons */}
      {latestExec?.status === 'completed' && latestExec?.selected_agent_id && !feedbackSubmitted && (
        <div className="feedback-section">
          <h3>🧠 Help the system learn</h3>
          <p>Was this response good? Your feedback trains the RL weights.</p>
          <div className="feedback-buttons">
            <button 
              className="btn-feedback btn-accept"
              onClick={() => handleFeedback('accept')}
            >
              👍 Accept - This was helpful!
            </button>
            <button 
              className="btn-feedback btn-reject"
              onClick={() => handleFeedback('reject')}
            >
              👎 Reject - Could be better
            </button>
          </div>
        </div>
      )}

      {feedbackSubmitted && (
        <div className="feedback-toast">
          ✓ Feedback recorded! RL weights have been updated.
        </div>
      )}

      {/* Execution Logs */}
      {latestExec?.logs && latestExec.logs.length > 0 && (
        <div className="logs-section">
          <h3>📜 Execution Logs</h3>
          <div className="logs-list">
            {latestExec.logs.map((log, idx) => (
              <div key={idx} className="log-entry">
                <span className="log-step">{log.step_order + 1}</span>
                <span className="log-agent">{log.agent_name || log.node_id}</span>
                <span className="log-type">{log.agent_type}</span>
                {log.score && (
                  <span className="log-score">Score: {log.score}</span>
                )}
                {log.duration_ms && (
                  <span className="log-duration">{log.duration_ms}ms</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default RunResults;
