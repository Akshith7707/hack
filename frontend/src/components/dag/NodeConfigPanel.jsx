import { useState, useEffect } from 'react';
import './NodeConfigPanel.css';

function NodeConfigPanel({ node, onUpdate, onClose, agents, integrations }) {
  const [config, setConfig] = useState(node?.data?.config || {});
  const [label, setLabel] = useState(node?.data?.label || '');

  useEffect(() => {
    setConfig(node?.data?.config || {});
    setLabel(node?.data?.label || '');
  }, [node]);

  if (!node) return null;

  const handleSave = () => {
    onUpdate(node.id, {
      ...node.data,
      label,
      config
    });
  };

  const handleConfigChange = (key, value) => {
    setConfig({ ...config, [key]: value });
  };

  const renderConfigFields = () => {
    switch (node.type) {
      case 'trigger':
        return (
          <>
            <div className="config-field">
              <label>Integration</label>
              <select
                value={config.integration || 'manual'}
                onChange={(e) => handleConfigChange('integration', e.target.value)}
              >
                <option value="manual">Manual</option>
                <option value="webhook">Webhook</option>
                <option value="mock_email">Mock Email</option>
                {integrations?.map(int => (
                  <option key={int.name} value={int.name}>{int.name}</option>
                ))}
              </select>
            </div>
          </>
        );

      case 'agent':
        return (
          <>
            <div className="config-field">
              <label>Agent Type</label>
              <select
                value={config.agent_type || 'classifier'}
                onChange={(e) => handleConfigChange('agent_type', e.target.value)}
              >
                <option value="classifier">Classifier</option>
                <option value="worker">Worker</option>
                <option value="supervisor">Supervisor</option>
                <option value="decision">Decision</option>
              </select>
            </div>
            {config.agent_type === 'worker' && (
              <div className="config-field">
                <label>Style</label>
                <select
                  value={config.style || 'detailed'}
                  onChange={(e) => handleConfigChange('style', e.target.value)}
                >
                  <option value="detailed">Detailed</option>
                  <option value="concise">Concise</option>
                  <option value="friendly">Friendly</option>
                  <option value="formal">Formal</option>
                  <option value="creative">Creative</option>
                </select>
              </div>
            )}
            <div className="config-field">
              <label>Input Variable</label>
              <input
                type="text"
                value={config.input || '$trigger.input'}
                onChange={(e) => handleConfigChange('input', e.target.value)}
                placeholder="$trigger.input"
              />
            </div>
          </>
        );

      case 'competition':
        return (
          <>
            <div className="config-field">
              <label>Worker Count</label>
              <input
                type="number"
                min="2"
                max="5"
                value={config.worker_count || 3}
                onChange={(e) => handleConfigChange('worker_count', parseInt(e.target.value))}
              />
            </div>
            <div className="config-field">
              <label>Parallel Execution</label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={config.parallel !== false}
                  onChange={(e) => handleConfigChange('parallel', e.target.checked)}
                />
                Run agents in parallel
              </label>
            </div>
          </>
        );

      case 'condition':
        return (
          <>
            <div className="config-field">
              <label>Condition Expression</label>
              <input
                type="text"
                value={config.condition || ''}
                onChange={(e) => handleConfigChange('condition', e.target.value)}
                placeholder="e.g., $classify.urgency == 'high'"
              />
            </div>
          </>
        );

      case 'action':
        return (
          <>
            <div className="config-field">
              <label>Integration</label>
              <select
                value={config.integration || 'webhook'}
                onChange={(e) => handleConfigChange('integration', e.target.value)}
              >
                <option value="webhook">Webhook</option>
                <option value="slack">Slack</option>
                <option value="discord">Discord</option>
                <option value="notion">Notion</option>
                <option value="stripe">Stripe</option>
                <option value="http">HTTP</option>
              </select>
            </div>
            <div className="config-field">
              <label>Action Type</label>
              <input
                type="text"
                value={config.action_type || 'send_message'}
                onChange={(e) => handleConfigChange('action_type', e.target.value)}
                placeholder="e.g., send_message"
              />
            </div>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <div className="config-panel">
      <div className="config-header">
        <h3>Configure Node</h3>
        <button className="btn-close" onClick={onClose}>x</button>
      </div>

      <div className="config-body">
        <div className="config-field">
          <label>Label</label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="Node label"
          />
        </div>

        <div className="config-section">
          <h4>Settings</h4>
          {renderConfigFields()}
        </div>
      </div>

      <div className="config-footer">
        <button className="btn-save" onClick={handleSave}>
          Save Changes
        </button>
      </div>
    </div>
  );
}

export default NodeConfigPanel;
