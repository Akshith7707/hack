import './NodePalette.css';

const NODE_TYPES = [
  {
    type: 'trigger',
    label: 'Trigger',
    icon: 'T',
    description: 'Start your workflow',
    color: '#10b981'
  },
  {
    type: 'agent',
    label: 'Agent',
    icon: 'A',
    description: 'AI agent processing',
    color: '#818cf8'
  },
  {
    type: 'competition',
    label: 'Competition',
    icon: 'C',
    description: 'Multiple agents compete',
    color: '#f59e0b'
  },
  {
    type: 'condition',
    label: 'Condition',
    icon: '?',
    description: 'Branch based on logic',
    color: '#8b5cf6'
  },
  {
    type: 'action',
    label: 'Action',
    icon: '!',
    description: 'Send to integration',
    color: '#ef4444'
  }
];

function NodePalette() {
  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="node-palette">
      <h3 className="palette-title">Nodes</h3>
      <div className="palette-items">
        {NODE_TYPES.map((node) => (
          <div
            key={node.type}
            className="palette-item"
            draggable
            onDragStart={(e) => onDragStart(e, node.type)}
          >
            <div
              className="palette-icon"
              style={{ background: `${node.color}20`, color: node.color }}
            >
              {node.icon}
            </div>
            <div className="palette-info">
              <div className="palette-label">{node.label}</div>
              <div className="palette-desc">{node.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default NodePalette;
