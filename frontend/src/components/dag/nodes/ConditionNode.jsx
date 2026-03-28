import { Handle, Position } from 'reactflow';
import './nodes.css';

function ConditionNode({ data, selected }) {
  return (
    <div className={`dag-node condition-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <div className="node-icon">?</div>
      <div className="node-content">
        <div className="node-label">{data.label || 'Condition'}</div>
        <div className="node-info">
          {data.config?.condition || 'if/else'}
        </div>
      </div>
      <Handle type="source" position={Position.Right} id="yes" style={{ top: '35%' }} />
      <Handle type="source" position={Position.Right} id="no" style={{ top: '65%' }} />
    </div>
  );
}

export default ConditionNode;
