import { useState } from 'react';
import { createWorkflow, updateWorkflow } from '../api';
import { DAGCanvas } from './dag';

function WorkflowEditor({ workflow, agents, onBack, onSave, integrations }) {
  const [name, setName] = useState(workflow?.name || 'New Workflow');
  const [description, setDescription] = useState(workflow?.description || '');
  const [triggerType, setTriggerType] = useState(workflow?.trigger_type || 'manual');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [editorMode, setEditorMode] = useState('visual'); // 'visual' or 'preview'
  const [dagNodes, setDagNodes] = useState(workflow?.nodes || []);
  const [dagEdges, setDagEdges] = useState(workflow?.edges || []);

  // Find agents by type
  const classifierAgent = agents.find(a => a.type === 'classifier');
  const workerAgents = agents.filter(a => a.type === 'worker');
  const supervisorAgent = agents.find(a => a.type === 'supervisor');
  const decisionAgent = agents.find(a => a.type === 'decision');

  // Build default FlexCode pipeline nodes
  const buildDefaultNodes = () => {
    const nodes = [
      {
        id: "trigger",
        type: "trigger",
        config: {
          integration: triggerType === 'webhook' ? 'webhook' : 'mock_email'
        }
      }
    ];

    // Add classifier if available
    if (classifierAgent) {
      nodes.push({
        id: "classify",
        type: "agent",
        config: {
          agent_id: classifierAgent.id,
          input: "$trigger.input"
        }
      });
    }

    // Add competition node with workers, supervisor, and decision
    if (workerAgents.length > 0 && supervisorAgent && decisionAgent) {
      nodes.push({
        id: "compete",
        type: "competition",
        config: {
          worker_agent_ids: workerAgents.slice(0, 3).map(a => a.id),
          supervisor_agent_id: supervisorAgent.id,
          decision_agent_id: decisionAgent.id,
          input: classifierAgent ? "$classify.output" : "$trigger.input"
        }
      });
    }

    // Add output node
    nodes.push({
      id: "output",
      type: "action",
      config: {
        action: "return_result",
        input: workerAgents.length > 0 ? "$compete.output" : "$classify.output"
      }
    });

    return nodes;
  };

  // Build default edges
  const buildDefaultEdges = () => {
    const edges = [];
    
    if (classifierAgent) {
      edges.push({ from: "trigger", to: "classify" });
      if (workerAgents.length > 0 && supervisorAgent && decisionAgent) {
        edges.push({ from: "classify", to: "compete" });
        edges.push({ from: "compete", to: "output" });
      } else {
        edges.push({ from: "classify", to: "output" });
      }
    } else {
      if (workerAgents.length > 0) {
        edges.push({ from: "trigger", to: "compete" });
        edges.push({ from: "compete", to: "output" });
      } else {
        edges.push({ from: "trigger", to: "output" });
      }
    }

    return edges;
  };

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Please enter a workflow name');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Use DAG nodes/edges if in visual mode, otherwise build defaults
      const nodesToSave = dagNodes.length > 0 ? dagNodes :
        (workflow?.nodes?.length > 0 ? workflow.nodes : buildDefaultNodes());
      const edgesToSave = dagEdges.length > 0 ? dagEdges :
        (workflow?.edges?.length > 0 ? workflow.edges : buildDefaultEdges());

      const workflowData = {
        name: name.trim(),
        description: description.trim(),
        trigger_type: triggerType,
        nodes: nodesToSave,
        edges: edgesToSave
      };

      console.log('Saving workflow:', workflowData);

      if (workflow?.id) {
        await updateWorkflow(workflow.id, workflowData);
      } else {
        await createWorkflow(workflowData);
      }

      setSuccess(true);
      await onSave();

      // Show success briefly then go back
      setTimeout(() => {
        onBack();
      }, 1000);
    } catch (err) {
      console.error('Failed to save workflow:', err);
      setError(err.message || 'Failed to save workflow');
    } finally {
      setSaving(false);
    }
  };

  const handleDagChange = (nodes, edges) => {
    setDagNodes(nodes);
    setDagEdges(edges);
  };

  return (
    <div className="workflow-editor">
      {/* Action Bar at Top */}
      <div className="editor-action-bar">
        <button className="btn-back" onClick={onBack}>
          ← Back to Workflows
        </button>
        <h2 className="editor-title">
          {workflow?.id ? '✏️ Edit Workflow' : '✨ Create New Workflow'}
        </h2>
        <button 
          className="btn-save-workflow" 
          onClick={handleSave} 
          disabled={saving || !name.trim()}
        >
          {saving ? '⏳ Saving...' : success ? '✅ Saved!' : '💾 Save Workflow'}
        </button>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="editor-message error">
          ❌ {error}
        </div>
      )}
      {success && (
        <div className="editor-message success">
          ✅ Workflow saved successfully! Redirecting...
        </div>
      )}

      <div className="editor-content">
        <div className="editor-sidebar">
          <h3>Configuration</h3>
          
          <div className="form-group">
            <label>Workflow Name *</label>
            <input 
              type="text" 
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g., Email Auto-Responder"
              className={!name.trim() ? 'input-error' : ''}
            />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea 
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="What does this workflow do?"
              rows={4}
            />
          </div>

          <div className="form-group">
            <label>Trigger Type</label>
            <select value={triggerType} onChange={e => setTriggerType(e.target.value)}>
              <option value="manual">Manual (Click to run)</option>
              <option value="webhook">Webhook (HTTP POST)</option>
              <option value="scheduled">Scheduled (Cron)</option>
              <option value="polling">Polling (Check API)</option>
            </select>
          </div>

          <div className="form-group">
            <label>Available Agents ({agents.length})</label>
            {agents.length === 0 ? (
              <p className="text-muted">No agents yet. Click "Quick Setup" first!</p>
            ) : (
              <div className="agent-list">
                {agents.map(agent => (
                  <div key={agent.id} className="agent-item">
                    <span className="agent-icon">
                      {agent.type === 'classifier' && '🔍'}
                      {agent.type === 'worker' && '⚙️'}
                      {agent.type === 'supervisor' && '👁️'}
                      {agent.type === 'decision' && '🎯'}
                    </span>
                    <span className="agent-name">{agent.name}</span>
                    {agent.style && (
                      <span className="agent-style">{agent.style}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Save button also at bottom of sidebar for visibility */}
          <button 
            className="btn-save-sidebar" 
            onClick={handleSave} 
            disabled={saving || !name.trim() || agents.length === 0}
          >
            {saving ? '⏳ Saving...' : success ? '✅ Saved!' : '💾 Create Workflow'}
          </button>
          
          {agents.length === 0 && (
            <p className="text-warning">⚠️ Setup demo agents first before creating a workflow</p>
          )}
        </div>

        <div className="editor-canvas">
          <div className="canvas-content">
            <div className="pipeline-header">
              <div className="pipeline-header-left">
                <h3>Pipeline</h3>
                <p className="text-muted">Design your workflow visually</p>
              </div>
              <div className="editor-mode-toggle">
                <button
                  className={`mode-btn ${editorMode === 'visual' ? 'active' : ''}`}
                  onClick={() => setEditorMode('visual')}
                >
                  Visual Editor
                </button>
                <button
                  className={`mode-btn ${editorMode === 'preview' ? 'active' : ''}`}
                  onClick={() => setEditorMode('preview')}
                >
                  Preview
                </button>
              </div>
            </div>

            {editorMode === 'visual' ? (
              <DAGCanvas
                initialNodes={dagNodes.length > 0 ? dagNodes : buildDefaultNodes().map((n, i) => ({
                  ...n,
                  position: { x: i * 200 + 50, y: 150 },
                  data: { label: n.id, config: n.config }
                }))}
                initialEdges={dagEdges.length > 0 ? dagEdges : buildDefaultEdges()}
                onChange={handleDagChange}
                agents={agents}
                integrations={integrations}
              />
            ) : (
              <>
                <div className="pipeline-visual">
              <div className="pipeline-node trigger-node">
                <div className="node-icon">📥</div>
                <div className="node-label">Trigger</div>
                <div className="node-detail">{triggerType}</div>
              </div>
              
              <div className="pipeline-connector">→</div>
              
              {classifierAgent && (
                <>
                  <div className="pipeline-node agent-node">
                    <div className="node-icon">🔍</div>
                    <div className="node-label">Analyzer</div>
                    <div className="node-detail">{classifierAgent.name}</div>
                  </div>
                  <div className="pipeline-connector">→</div>
                </>
              )}
              
              {workerAgents.length > 0 && (
                <>
                  <div className="pipeline-node competition-node">
                    <div className="node-icon">⚔️</div>
                    <div className="node-label">Competition</div>
                    <div className="node-detail">{workerAgents.length} Agents Battle</div>
                    <div className="node-workers">
                      {workerAgents.slice(0, 3).map((w, i) => (
                        <span key={w.id} className="worker-badge">{w.style || `Worker ${i+1}`}</span>
                      ))}
                    </div>
                  </div>
                  <div className="pipeline-connector">→</div>
                </>
              )}
              
              {supervisorAgent && (
                <>
                  <div className="pipeline-node supervisor-node">
                    <div className="node-icon">👁️</div>
                    <div className="node-label">Reviewer</div>
                    <div className="node-detail">Scores all outputs</div>
                  </div>
                  <div className="pipeline-connector">→</div>
                </>
              )}
              
              {decisionAgent && (
                <>
                  <div className="pipeline-node decision-node">
                    <div className="node-icon">🎯</div>
                    <div className="node-label">Decision</div>
                    <div className="node-detail">Picks winner + RL</div>
                  </div>
                  <div className="pipeline-connector">→</div>
                </>
              )}
              
              <div className="pipeline-node output-node">
                <div className="node-icon">📤</div>
                <div className="node-label">Output</div>
                <div className="node-detail">Best response</div>
              </div>
            </div>

            {agents.length === 0 && (
              <div className="pipeline-empty-state">
                <div className="empty-icon">⚠️</div>
                <h4>No Agents Available</h4>
                <p>Click the "🚀 Quick Setup" button in the navigation to create demo agents</p>
              </div>
            )}

            <div className="pipeline-info">
              <h4>How Competition Works</h4>
              <ol>
                <li><strong>Workers compete:</strong> {workerAgents.length || 3} agents generate responses in parallel</li>
                <li><strong>Supervisor scores:</strong> Each response gets a quality score (0-100)</li>
                <li><strong>Decision + RL:</strong> Best response picked using scores + learned weights</li>
                <li><strong>Learn from feedback:</strong> Accept/Reject updates agent weights over time</li>
              </ol>
            </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default WorkflowEditor;
