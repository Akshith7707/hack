import { Handle, Position } from 'reactflow';
import './nodes.css';

function ActionNode({ data, selected }) {
  return (
    <div className={`dag-node action-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <div className="node-icon">!</div>
      <div className="node-content">
        <div className="node-label">{data.label || 'Action'}</div>
        <div className="node-info">
          {data.config?.integration || 'webhook'}
        </div>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export default ActionNode;
