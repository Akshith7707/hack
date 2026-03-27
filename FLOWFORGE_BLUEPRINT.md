# 🔥 FlowForge — YC Transformation Blueprint

> **"Zapier for Autonomous AI Teams"**

Transform FlexMail into a generalized no-code automation platform where AI agents collaborate, learn, and integrate with real-world tools.

---

## 1. System Refactor Plan

### Current State → Target State

```
CURRENT (FlexMail)                    TARGET (FlowForge)
─────────────────────                 ─────────────────────
Email Input                    →      Trigger Node (Webhook/Manual/Schedule)
Classifier Agent               →      Analyzer Node (generic)
3 Worker Agents                →      Executor Nodes (configurable)
Supervisor Agent               →      Reviewer Node
Decision Agent                 →      Decision Node (RL-weighted)
Email Output                   →      Action Node (Slack/HTTP/Email)
```

### Key Changes

| Component | Before | After |
|-----------|--------|-------|
| Input | Email-only | Any trigger (webhook, manual, cron) |
| Pipeline | Hardcoded 6-step | DAG with configurable nodes |
| Agents | Email-specific prompts | Generic role-based prompts |
| Output | Display only | Execute actions (Slack, HTTP, etc.) |
| Integrations | Gmail OAuth | Plugin system |

### Files to Refactor

```
backend/
├── orchestrator.py    → workflow_engine.py (DAG executor)
├── prompts.py         → prompts.py (generic templates)
├── models.py          → models.py (add Workflow, Node schemas)
├── database.py        → database.py (add workflows table)
├── integrations.py    → integrations/ (plugin folder)
└── main.py            → main.py (new workflow routes)
```

---

## 2. New Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         FLOWFORGE ARCHITECTURE                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      TRIGGER LAYER                               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  │
│  │  │ Webhook  │  │  Manual  │  │ Schedule │  │  Event   │        │  │
│  │  │ /trigger │  │  Input   │  │  (cron)  │  │ Listener │        │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │  │
│  └───────┼──────────────┼──────────────┼──────────────┼────────────┘  │
│          └──────────────┴──────────────┴──────────────┘               │
│                                   │                                    │
│                                   ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                     WORKFLOW ENGINE (DAG)                        │  │
│  │                                                                  │  │
│  │    ┌──────────┐      ┌──────────┐      ┌──────────┐            │  │
│  │    │ Analyzer │─────▶│ Executor │─────▶│ Reviewer │            │  │
│  │    │   Node   │      │  Node(s) │      │   Node   │            │  │
│  │    └──────────┘      └────┬─────┘      └────┬─────┘            │  │
│  │                           │                  │                   │  │
│  │                      ┌────┴────┐        ┌────┴────┐             │  │
│  │                      │ Branch? │        │ Score   │             │  │
│  │                      └────┬────┘        └────┬────┘             │  │
│  │                           ▼                  ▼                   │  │
│  │                    ┌──────────────────────────────┐             │  │
│  │                    │      DECISION NODE           │             │  │
│  │                    │  (RL weights + scores)       │             │  │
│  │                    └──────────────┬───────────────┘             │  │
│  └───────────────────────────────────┼─────────────────────────────┘  │
│                                      ▼                                 │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      ACTION LAYER                                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │  │
│  │  │  Slack   │  │  HTTP    │  │  Email   │  │  Notion  │        │  │
│  │  │  Post    │  │  Request │  │  Send    │  │  Create  │        │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                      │                                 │
│                                      ▼                                 │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    RL FEEDBACK LAYER                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │  │
│  │  │ Store Result │  │ User Feedback│  │ Update Weights│          │  │
│  │  │ + Score      │  │ (👍/👎)      │  │ + Prompts     │          │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. TRIGGER fires (webhook receives data)
        ↓
2. WORKFLOW ENGINE loads workflow definition (DAG)
        ↓
3. Execute nodes in topological order:
   - Analyzer: Extract key info from input
   - Executors: Generate outputs (parallel)
   - Reviewer: Score each output
   - Decision: Pick best using RL weights
        ↓
4. ACTION executes (send Slack message)
        ↓
5. FEEDBACK stored → weights updated
```

---

## 3. Agent Abstraction

### New Agent Schema

```json
{
  "id": "agent_abc123",
  "name": "Payment Recovery Agent",
  "type": "executor",
  
  "role": "Write recovery messages for failed payments",
  "goal": "Maximize payment recovery rate",
  "backstory": "Expert at empathetic customer communication",
  
  "tools": ["slack", "email", "http"],
  "model": "gpt-4",
  "temperature": 0.7,
  
  "prompt_template": "You are a {{role}}. Your goal is {{goal}}.\n\nInput: {{input}}\n\nGenerate a response.",
  
  "memory": {
    "context_window": 5,
    "recent_inputs": [],
    "recent_outputs": []
  },
  
  "feedback_history": {
    "total_runs": 150,
    "accepted": 120,
    "rejected": 30,
    "avg_score": 7.8,
    "weight": 0.42
  },
  
  "config": {
    "style": "friendly",
    "max_tokens": 500,
    "retry_on_fail": true
  },
  
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-20T15:30:00Z"
}
```

### Agent Types

| Type | Purpose | Example |
|------|---------|---------|
| `analyzer` | Extract/classify input | "Categorize this as urgent/normal" |
| `executor` | Generate output | "Write a response" |
| `reviewer` | Score outputs | "Rate this 1-10" |
| `decision` | Pick best option | "Select best based on scores" |
| `transformer` | Modify data | "Format for Slack" |

---

## 4. Integration Layer (Plugin System)

### Base Interface

```python
# integrations/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class Integration(ABC):
    """Base class for all integrations"""
    name: str
    description: str
    auth_type: str = "none"  # none, api_key, oauth
    
    @abstractmethod
    async def trigger(self, config: Dict) -> List[Dict]:
        """Fetch data from source (for triggers)"""
        pass
    
    @abstractmethod
    async def action(self, config: Dict, data: Dict) -> Dict:
        """Send data to destination (for actions)"""
        pass
    
    def validate_config(self, config: Dict) -> bool:
        """Validate configuration"""
        return True
```

### Example: Webhook Integration

```python
# integrations/webhook.py
class WebhookIntegration(Integration):
    name = "webhook"
    description = "HTTP webhooks for triggers and actions"
    
    async def trigger(self, config: Dict) -> List[Dict]:
        # Called when webhook endpoint receives data
        return config.get("payload", [])
    
    async def action(self, config: Dict, data: Dict) -> Dict:
        url = config["url"]
        method = config.get("method", "POST")
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, json=data)
            return {"status": response.status_code, "body": response.text}
```

### Example: Slack Integration

```python
# integrations/slack.py
class SlackIntegration(Integration):
    name = "slack"
    description = "Send messages to Slack"
    auth_type = "webhook"
    
    async def trigger(self, config: Dict) -> List[Dict]:
        # Would use Slack Events API
        return []
    
    async def action(self, config: Dict, data: Dict) -> Dict:
        webhook_url = config["webhook_url"]
        message = data.get("message", str(data))
        
        payload = {
            "text": message,
            "channel": config.get("channel", "#general")
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            return {"status": "sent" if response.status_code == 200 else "failed"}
```

### Integration Registry

```python
# integrations/__init__.py
INTEGRATIONS = {
    "webhook": WebhookIntegration(),
    "slack": SlackIntegration(),
    "http": HTTPIntegration(),
    "email": EmailIntegration(),
}

def get_integration(name: str) -> Integration:
    return INTEGRATIONS.get(name)
```

---

## 5. Reinforcement Learning Layer

### Design Philosophy

> **Simple, practical, production-friendly** — NOT academic RL

### Core Concept

```
┌─────────────────────────────────────────────────────────────────┐
│                      RL FEEDBACK LOOP                           │
│                                                                 │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐              │
│   │  Input   │────▶│  Agent   │────▶│  Output  │              │
│   └──────────┘     │  runs    │     └────┬─────┘              │
│                    └──────────┘          │                     │
│                                          ▼                     │
│                                   ┌──────────────┐             │
│                                   │   Reviewer   │             │
│                                   │  scores 1-10 │             │
│                                   └──────┬───────┘             │
│                                          │                     │
│         ┌────────────────────────────────┼──────────────────┐  │
│         │                                ▼                  │  │
│         │                        ┌──────────────┐          │  │
│         │                        │    Store     │          │  │
│         │                        │ input/output │          │  │
│         │                        │ /score       │          │  │
│         │                        └──────┬───────┘          │  │
│         │                               │                  │  │
│         │    ┌──────────────────────────┴───────────────┐  │  │
│         │    ▼                                          ▼  │  │
│         │ ┌──────────────┐                  ┌──────────────┐│  │
│         │ │User Feedback │                  │ Auto-improve ││  │
│         │ │   👍 / 👎    │                  │   prompts    ││  │
│         │ └──────┬───────┘                  └──────────────┘│  │
│         │        │                                          │  │
│         │        ▼                                          │  │
│         │ ┌──────────────┐                                  │  │
│         │ │Update Weights│                                  │  │
│         │ │ agent.weight │                                  │  │
│         │ └──────────────┘                                  │  │
│         └───────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Weight Update Algorithm

```python
# rl_engine.py
LEARNING_RATE = 0.05
MIN_WEIGHT = 0.05

def on_feedback(agent_id: str, feedback: str, score: float):
    """Update agent weight based on feedback"""
    weights = get_all_weights()
    current = weights[agent_id]
    
    if feedback == "accept":
        # Boost this agent
        delta = LEARNING_RATE * (1 - current)
        weights[agent_id] = current + delta
    else:
        # Penalize this agent
        delta = LEARNING_RATE * current
        weights[agent_id] = max(MIN_WEIGHT, current - delta)
    
    # Normalize to sum = 1.0
    total = sum(weights.values())
    for aid in weights:
        weights[aid] /= total
    
    save_weights(weights)
```

### Feedback Storage Schema

```sql
CREATE TABLE feedback_log (
    id INTEGER PRIMARY KEY,
    run_id TEXT,
    agent_id TEXT,
    input_text TEXT,
    output_text TEXT,
    score REAL,           -- Reviewer score (1-10)
    feedback TEXT,        -- accept/reject
    timestamp TEXT
);
```

### Future: Prompt Optimization

```python
def optimize_prompt(agent_id: str):
    """Use high-scoring examples to improve prompt"""
    # Get top 10 accepted outputs
    best = get_best_outputs(agent_id, limit=10)
    
    # Analyze patterns
    patterns = analyze_patterns(best)
    
    # Update prompt template
    agent = get_agent(agent_id)
    agent.prompt_template += f"\n\nStyle guide based on successful outputs:\n{patterns}"
    save_agent(agent)
```

---

## 6. Workflow Execution Engine

### Workflow Definition (DAG)

```json
{
  "id": "workflow_123",
  "name": "Payment Recovery Flow",
  "trigger": {
    "type": "webhook",
    "config": { "path": "/stripe-webhook" }
  },
  "nodes": [
    {
      "id": "analyze",
      "type": "agent",
      "agent_id": "analyzer_001",
      "inputs": ["$trigger.data"],
      "next": ["draft_formal", "draft_friendly", "draft_urgent"]
    },
    {
      "id": "draft_formal",
      "type": "agent",
      "agent_id": "executor_formal",
      "inputs": ["$analyze.output"],
      "next": ["review"]
    },
    {
      "id": "draft_friendly",
      "type": "agent",
      "agent_id": "executor_friendly",
      "inputs": ["$analyze.output"],
      "next": ["review"]
    },
    {
      "id": "draft_urgent",
      "type": "agent",
      "agent_id": "executor_urgent",
      "inputs": ["$analyze.output"],
      "next": ["review"]
    },
    {
      "id": "review",
      "type": "agent",
      "agent_id": "reviewer_001",
      "inputs": ["$draft_formal.output", "$draft_friendly.output", "$draft_urgent.output"],
      "next": ["decide"]
    },
    {
      "id": "decide",
      "type": "decision",
      "inputs": ["$review.scores"],
      "next": ["send_slack"]
    },
    {
      "id": "send_slack",
      "type": "action",
      "integration": "slack",
      "config": {
        "webhook_url": "{{env.SLACK_WEBHOOK}}",
        "channel": "#payments"
      },
      "inputs": ["$decide.selected_output"]
    }
  ]
}
```

### Execution Engine

```python
# workflow_engine.py
import asyncio
from collections import defaultdict

class WorkflowEngine:
    def __init__(self, workflow: dict):
        self.workflow = workflow
        self.results = {}
        self.status = {}
    
    async def execute(self, trigger_data: dict) -> dict:
        """Execute workflow as DAG"""
        self.results["$trigger"] = {"data": trigger_data}
        
        # Build dependency graph
        graph = self._build_graph()
        
        # Topological execution with parallel support
        while not self._all_complete():
            ready = self._get_ready_nodes(graph)
            if not ready:
                break
            
            # Execute ready nodes in parallel
            tasks = [self._execute_node(node) for node in ready]
            await asyncio.gather(*tasks)
        
        return self.results
    
    async def _execute_node(self, node: dict):
        """Execute a single node"""
        node_id = node["id"]
        self.status[node_id] = "running"
        
        # Resolve inputs
        inputs = self._resolve_inputs(node.get("inputs", []))
        
        if node["type"] == "agent":
            result = await self._run_agent(node["agent_id"], inputs)
        elif node["type"] == "action":
            result = await self._run_action(node["integration"], node["config"], inputs)
        elif node["type"] == "decision":
            result = await self._run_decision(inputs)
        
        self.results[f"${node_id}"] = {"output": result}
        self.status[node_id] = "complete"
```

### Features

- ✅ **Parallel execution**: Nodes without dependencies run concurrently
- ✅ **Variable resolution**: `$node.output` references
- ✅ **Branching**: Multiple `next` nodes
- ✅ **Conditional logic**: Add `condition` to nodes
- ✅ **Retries**: `retry_count` per node

---

## 7. Generic Prompt Templates

### Analyzer Agent

```python
ANALYZER_PROMPT = """You are an expert data analyzer.

TASK: Extract key information from the input and categorize it.

INPUT:
{{input}}

Respond in this format:
CATEGORY: [urgent/normal/low]
SUMMARY: [1-2 sentence summary]
KEY_POINTS:
- [point 1]
- [point 2]
ENTITIES: [list any names, amounts, dates mentioned]
"""
```

### Executor Agent

```python
EXECUTOR_PROMPT = """You are a {{style}} communication expert.

ROLE: {{role}}
GOAL: {{goal}}

CONTEXT:
{{context}}

INPUT:
{{input}}

Generate a response that:
1. Addresses the core issue
2. Matches the {{style}} tone
3. Is actionable and clear

RESPONSE:
"""
```

### Reviewer Agent

```python
REVIEWER_PROMPT = """You are a quality reviewer.

Review each response and score it from 1-10.

ORIGINAL INPUT:
{{input}}

RESPONSES TO REVIEW:
{% for i, response in enumerate(responses) %}
RESPONSE_{{i+1}}:
{{response}}

{% endfor %}

Score each response on:
- Relevance (does it address the input?)
- Quality (is it well-written?)
- Actionability (can the user act on it?)

OUTPUT FORMAT:
SCORE_1: [1-10]
SCORE_2: [1-10]
SCORE_3: [1-10]
REASONING: [brief explanation]
"""
```

### Decision Agent

```python
DECISION_PROMPT = """You are the final decision maker.

SCORES:
{% for agent, score in scores.items() %}
- {{agent}}: {{score}}/10 (weight: {{weights[agent]}}%)
{% endfor %}

CONTEXT SIGNALS:
- Urgency: {{context.urgency}}
- Time: {{context.time_period}}
- User preference history: {{context.historical_preference}}

RESPONSES:
{% for agent, response in responses.items() %}
[{{agent}}]:
{{response}}

{% endfor %}

Select the best response considering scores AND weights.

OUTPUT:
SELECTED: [agent name]
FINAL: [the selected response, possibly refined]
REASON: [why this was chosen]
"""
```

---

## 8. Database Schema

```sql
-- Workflows (DAG definitions)
CREATE TABLE workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    trigger_type TEXT,        -- webhook, manual, schedule
    trigger_config TEXT,      -- JSON
    nodes TEXT,               -- JSON array of nodes
    is_active BOOLEAN DEFAULT true,
    created_at TEXT,
    updated_at TEXT
);

-- Agents (AI workers)
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,       -- analyzer, executor, reviewer, decision
    role TEXT,
    goal TEXT,
    prompt_template TEXT,
    tools TEXT,               -- JSON array
    model TEXT DEFAULT 'gpt-4',
    config TEXT,              -- JSON
    created_at TEXT
);

-- Agent weights (RL state)
CREATE TABLE agent_weights (
    agent_id TEXT PRIMARY KEY,
    weight REAL DEFAULT 0.33,
    total_runs INTEGER DEFAULT 0,
    accepted INTEGER DEFAULT 0,
    rejected INTEGER DEFAULT 0,
    avg_score REAL DEFAULT 0,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Workflow executions
CREATE TABLE executions (
    id TEXT PRIMARY KEY,
    workflow_id TEXT,
    trigger_data TEXT,        -- JSON
    status TEXT,              -- running, completed, failed
    results TEXT,             -- JSON (all node outputs)
    selected_agent TEXT,
    final_output TEXT,
    started_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
);

-- Execution logs (per node)
CREATE TABLE execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT,
    node_id TEXT,
    agent_id TEXT,
    input_text TEXT,
    output_text TEXT,
    score REAL,
    duration_ms INTEGER,
    timestamp TEXT
);

-- Feedback log (RL training data)
CREATE TABLE feedback_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT,
    agent_id TEXT,
    feedback TEXT,            -- accept, reject
    input_hash TEXT,          -- for deduplication
    output_text TEXT,
    score REAL,
    timestamp TEXT
);

-- Integrations config
CREATE TABLE integration_configs (
    id TEXT PRIMARY KEY,
    integration_name TEXT,
    config TEXT,              -- JSON (encrypted for secrets)
    created_at TEXT
);
```

---

## 9. Frontend Refactor

### Current → Target

| Current | Target |
|---------|--------|
| Tab-based layout | Sidebar + Canvas layout |
| Email list | Workflow list |
| Static pipeline visual | Drag-drop DAG editor |
| Agent cards | Node configuration panel |

### Phase 1: MVP UI

```
┌──────────────────────────────────────────────────────────┐
│  FlowForge                              [+ New Workflow] │
├────────────┬─────────────────────────────────────────────┤
│            │                                             │
│  WORKFLOWS │            WORKFLOW CANVAS                  │
│  ─────────│                                             │
│  > Payment │    ┌─────┐    ┌─────┐    ┌─────┐          │
│    Recovery│    │Trig │───▶│Agent│───▶│Slack│          │
│  > Support │    └─────┘    └─────┘    └─────┘          │
│    Ticket  │                                             │
│  > Lead    │    ─────────────────────────────            │
│    Scoring │    NODE PROPERTIES                          │
│            │    Name: [Analyzer Agent    ]               │
│            │    Type: [agent ▼           ]               │
│            │    Prompt: [______________ ]                │
│            │                                             │
│  ─────────│    ─────────────────────────────            │
│  AGENTS    │    EXECUTION LOG                            │
│  ─────────│    [12:01] Trigger received                 │
│  • Analyzer│    [12:02] Analyzer: "Urgent payment..."   │
│  • Formal  │    [12:03] Executor: "Dear customer..."    │
│  • Friendly│    [12:04] Selected: Friendly (score: 8)   │
│  • Reviewer│                                             │
│            │    [👍 Accept] [👎 Reject]                  │
└────────────┴─────────────────────────────────────────────┘
```

### Key Components

```jsx
// components/WorkflowList.jsx - Sidebar list of workflows
// components/WorkflowCanvas.jsx - Visual DAG editor
// components/NodePanel.jsx - Configure selected node
// components/AgentConfig.jsx - Configure agent properties
// components/ExecutionLog.jsx - Real-time logs
// components/FeedbackPanel.jsx - Accept/reject with history
```

### Libraries to Add

```bash
npm install reactflow        # DAG visualization
npm install @dnd-kit/core    # Drag and drop
```

---

## 10. MVP vs YC Roadmap

### MVP (This Week) ✅

| Feature | Status | Priority |
|---------|--------|----------|
| Generic workflow engine | 🔨 Build | P0 |
| Plugin-based integrations | 🔨 Build | P0 |
| Generic agent prompts | 🔨 Build | P0 |
| Basic workflow UI | 🔨 Build | P0 |
| Webhook trigger | 🔨 Build | P0 |
| Slack action | 🔨 Build | P0 |
| RL feedback loop | ✅ Exists | P0 |

**Demo-ready in 3-4 hours.**

### V1 (Post-Funding)

| Feature | Timeline | Impact |
|---------|----------|--------|
| Visual DAG editor (ReactFlow) | Week 1 | High |
| More integrations (Notion, Discord, Stripe) | Week 2 | High |
| Scheduled triggers (cron) | Week 2 | Medium |
| Prompt optimization from feedback | Week 3 | High |
| Workflow templates marketplace | Week 4 | Medium |
| Team collaboration | Month 2 | High |
| Usage analytics dashboard | Month 2 | Medium |

### V2 (Series A)

- Multi-tenant SaaS
- Enterprise SSO
- Custom LLM fine-tuning
- Workflow versioning
- Audit logs
- SOC2 compliance

---

## 11. Demo Narrative (YC Pitch)

### The Hook (10 seconds)

> "FlowForge is Zapier for AI teams. Instead of connecting apps, you connect AI agents that work together, learn from feedback, and improve over time."

### The Demo (60 seconds)

```
"Watch this: A Stripe webhook just fired — a customer's payment failed.

1. [Webhook triggers] FlowForge receives the event
2. [Analyzer runs] AI extracts: customer name, amount, failure reason
3. [3 Agents draft] Formal, Friendly, and Urgent recovery messages
4. [Reviewer scores] Each draft is rated for tone and effectiveness
5. [Decision picks] Based on RL weights, Friendly wins (score: 8.5)
6. [Slack sends] Message posted to #payments channel

Now I click 'Accept' — the Friendly agent's weight increases.
Next time? FlowForge will prefer Friendly automatically.

No code. No training. Just AI agents learning from human feedback."
```

### The Ask

> "We're building the infrastructure for autonomous AI workflows. 
> $500K to hire 2 engineers and launch paid beta in 3 months.
> Our vision: Every company has an AI team that works 24/7."

### Key Metrics to Track

- Workflows created
- Executions per day
- Feedback rate (% of runs with feedback)
- Agent accuracy (accept rate)
- Time saved per workflow

---

## Quick Start Implementation

### Step 1: Rename Project

```bash
# Rename folder
mv flexmail flowforge

# Update package.json
sed -i 's/flexmail/flowforge/g' frontend/package.json

# Update Python imports
sed -i 's/FlexMail/FlowForge/g' backend/*.py
```

### Step 2: Create Workflow Engine

```python
# backend/workflow_engine.py
# (See Section 6 for full implementation)
```

### Step 3: Add Webhook Endpoint

```python
# In main.py
@app.post("/api/webhook/{workflow_id}")
async def webhook_trigger(workflow_id: str, request: Request):
    data = await request.json()
    result = await engine.execute(workflow_id, data)
    return result
```

### Step 4: Update Frontend

```jsx
// Update App.jsx title
<h1>🔥 FlowForge</h1>

// Add workflow list sidebar
// Add canvas for DAG visualization
```

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `backend/workflow_engine.py` | Create | DAG execution engine |
| `backend/integrations/` | Create | Plugin folder |
| `backend/prompts.py` | Modify | Generic templates |
| `backend/models.py` | Modify | Add Workflow schema |
| `backend/database.py` | Modify | Add workflow tables |
| `backend/main.py` | Modify | Add workflow routes |
| `frontend/src/App.jsx` | Modify | New layout |
| `README.md` | Modify | FlowForge branding |

---

**Ready to implement? Start with the workflow engine!**
