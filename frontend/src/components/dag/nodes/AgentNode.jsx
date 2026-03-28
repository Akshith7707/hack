import { Handle, Position } from 'reactflow';
import './nodes.css';

function AgentNode({ data, selected }) {
  return (
    <div className={`dag-node agent-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <div className="node-icon">A</div>
      <div className="node-content">
        <div className="node-label">{data.label || 'Agent'}</div>
        <div className="node-info">
          {data.config?.agent_type || data.config?.style || 'classifier'}
        </div>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export default AgentNode;
