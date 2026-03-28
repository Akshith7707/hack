import { Handle, Position } from 'reactflow';
import './nodes.css';

function CompetitionNode({ data, selected }) {
  return (
    <div className={`dag-node competition-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <div className="node-icon">C</div>
      <div className="node-content">
        <div className="node-label">{data.label || 'Competition'}</div>
        <div className="node-info">
          {data.config?.worker_count || 3} agents compete
        </div>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export default CompetitionNode;
