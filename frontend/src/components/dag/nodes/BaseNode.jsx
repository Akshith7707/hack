import { Handle, Position } from 'reactflow';
import './nodes.css';

function BaseNode({ data, selected, icon, className, children }) {
  return (
    <div className={`dag-node ${className} ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <div className="node-icon">{icon}</div>
      <div className="node-content">
        <div className="node-label">{data.label}</div>
        {children}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export default BaseNode;
