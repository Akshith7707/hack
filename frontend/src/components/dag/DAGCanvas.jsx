import { useCallback, useRef, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  ReactFlowProvider,
} from 'reactflow';
import 'reactflow/dist/style.css';

import TriggerNode from './nodes/TriggerNode';
import AgentNode from './nodes/AgentNode';
import CompetitionNode from './nodes/CompetitionNode';
import ConditionNode from './nodes/ConditionNode';
import ActionNode from './nodes/ActionNode';
import NodePalette from './NodePalette';
import NodeConfigPanel from './NodeConfigPanel';
import './DAGCanvas.css';

const nodeTypes = {
  trigger: TriggerNode,
  agent: AgentNode,
  competition: CompetitionNode,
  condition: ConditionNode,
  action: ActionNode,
};

const defaultLabels = {
  trigger: 'Trigger',
  agent: 'Agent',
  competition: 'Competition',
  condition: 'Condition',
  action: 'Action',
};

const defaultConfigs = {
  trigger: { integration: 'manual' },
  agent: { agent_type: 'classifier', input: '$trigger.input' },
  competition: { worker_count: 3, parallel: true },
  condition: { condition: '' },
  action: { integration: 'webhook', action_type: 'send' },
};

function DAGCanvas({ initialNodes = [], initialEdges = [], onChange, agents, integrations }) {
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  const [nodes, setNodes, onNodesChange] = useNodesState(
    initialNodes.map(n => ({
      ...n,
      type: n.type || 'agent',
      data: n.data || { label: n.id, config: {} },
      position: n.position || { x: 100, y: 100 },
    }))
  );

  const [edges, setEdges, onEdgesChange] = useEdgesState(
    initialEdges.map(e => ({
      id: e.id || `${e.source || e.from}-${e.target || e.to}`,
      source: e.source || e.from,
      target: e.target || e.to,
      animated: true,
    }))
  );

  const onConnect = useCallback(
    (params) => {
      setEdges((eds) => addEdge({ ...params, animated: true }, eds));
    },
    [setEdges]
  );

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      if (!type || !reactFlowInstance) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode = {
        id: `${type}_${Date.now()}`,
        type,
        position,
        data: {
          label: defaultLabels[type],
          config: { ...defaultConfigs[type] },
        },
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [reactFlowInstance, setNodes]
  );

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const updateNodeData = useCallback((nodeId, newData) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId ? { ...node, data: newData } : node
      )
    );
    setSelectedNode(null);
  }, [setNodes]);

  const handleSave = useCallback(() => {
    const flowNodes = nodes.map(n => ({
      id: n.id,
      type: n.type,
      position: n.position,
      data: n.data,
    }));

    const flowEdges = edges.map(e => ({
      id: e.id,
      source: e.source,
      target: e.target,
    }));

    onChange?.(flowNodes, flowEdges);
  }, [nodes, edges, onChange]);

  const onNodesDelete = useCallback((deleted) => {
    if (selectedNode && deleted.find(n => n.id === selectedNode.id)) {
      setSelectedNode(null);
    }
  }, [selectedNode]);

  return (
    <div className="dag-canvas-container">
      <NodePalette />
      <div className="dag-canvas-wrapper" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          onNodesDelete={onNodesDelete}
          nodeTypes={nodeTypes}
          fitView
          snapToGrid
          snapGrid={[16, 16]}
          deleteKeyCode={['Backspace', 'Delete']}
        >
          <Background variant="dots" gap={16} size={1} color="var(--border-color)" />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              switch (node.type) {
                case 'trigger': return '#10b981';
                case 'agent': return '#818cf8';
                case 'competition': return '#f59e0b';
                case 'condition': return '#8b5cf6';
                case 'action': return '#ef4444';
                default: return '#6b7280';
              }
            }}
            style={{ background: 'var(--bg-secondary)' }}
          />
        </ReactFlow>
        <button className="btn-save-dag" onClick={handleSave}>
          Save Layout
        </button>
      </div>
      {selectedNode && (
        <NodeConfigPanel
          node={selectedNode}
          onUpdate={updateNodeData}
          onClose={() => setSelectedNode(null)}
          agents={agents}
          integrations={integrations}
        />
      )}
    </div>
  );
}

function DAGCanvasWrapper(props) {
  return (
    <ReactFlowProvider>
      <DAGCanvas {...props} />
    </ReactFlowProvider>
  );
}

export default DAGCanvasWrapper;
