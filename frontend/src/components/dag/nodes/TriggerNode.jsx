import { Handle, Position } from 'reactflow';
import './nodes.css';

function TriggerNode({ data, selected }) {
  return (
    <div className={`dag-node trigger-node ${selected ? 'selected' : ''}`}>
      <div className="node-icon">T</div>
      <div className="node-content">
        <div className="node-label">{data.label || 'Trigger'}</div>
        <div className="node-info">
          {data.config?.integration || 'manual'}
        </div>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export default TriggerNode;
