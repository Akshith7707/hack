import { useState } from 'react';
import { createAgent } from '../api';

export default function AgentBuilder({ onAgentCreated }) {
  const [formData, setFormData] = useState({
    name: '',
    role: '',
    goal: '',
    type: 'worker',
    style: 'detailed'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const agentData = {
        name: formData.name,
        role: formData.role,
        goal: formData.goal,
        type: formData.type,
        style: formData.type === 'worker' ? formData.style : null
      };
      
      await createAgent(agentData);
      setFormData({ name: '', role: '', goal: '', type: 'worker', style: 'detailed' });
      onAgentCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="fade-in">
      <div className="form-group">
        <label>Agent Name</label>
        <input
          type="text"
          placeholder="e.g., Detailed Responder"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
        />
      </div>

      <div className="form-group">
        <label>Role</label>
        <input
          type="text"
          placeholder="e.g., Email Writer"
          value={formData.role}
          onChange={(e) => setFormData({ ...formData, role: e.target.value })}
          required
        />
      </div>

      <div className="form-group">
        <label>Goal</label>
        <textarea
          placeholder="What should this agent accomplish?"
          value={formData.goal}
          onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
          rows={2}
          required
        />
      </div>

      <div className="form-group">
        <label>Type</label>
        <select
          value={formData.type}
          onChange={(e) => setFormData({ ...formData, type: e.target.value })}
        >
          <option value="classifier">Classifier</option>
          <option value="worker">Worker</option>
          <option value="supervisor">Supervisor</option>
          <option value="decision">Decision</option>
        </select>
      </div>

      {formData.type === 'worker' && (
        <div className="form-group">
          <label>Style</label>
          <select
            value={formData.style}
            onChange={(e) => setFormData({ ...formData, style: e.target.value })}
          >
            <option value="detailed">Detailed</option>
            <option value="concise">Concise</option>
            <option value="friendly">Friendly</option>
          </select>
        </div>
      )}

      {error && <p style={{ color: 'var(--accent-red)', fontSize: '0.875rem' }}>{error}</p>}

      <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%' }}>
        {loading ? <span className="loading-spinner" /> : 'Create Agent'}
      </button>
    </form>
  );
}
