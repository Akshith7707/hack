# 🔥 FlexCode

> **Zapier for Autonomous AI Teams — Build AI-Powered Automations with No Code**

FlexCode is the **first no-code platform** where AI agents collaborate as a team, compete to give you the best response, and learn from your feedback using reinforcement learning.

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## ✨ What Makes FlexCode Different?

| Traditional Automation | FlexCode |
|------------------------|----------|
| One template, one response | 3 AI agents compete for best output |
| Static rules | Learns from feedback with RL |
| Breaks when edge cases appear | Adapts and improves over time |
| Connect apps only | Connect intelligent agents |

### The Magic
```
📥 Input arrives → 🔍 Classifier categorizes → ⚔️ 3 Agents compete 
→ 📊 Supervisor scores → 🏆 Best one selected → 👍 You give feedback → 🧠 System learns
```

---

## 🎯 Key Features

### 🤖 Competing AI Agents
Three agents with different styles (formal, friendly, concise) generate responses in parallel. A supervisor scores them objectively.

### 🧠 Reinforcement Learning
Click 👍 or 👎 on any output. The system learns your preferences and adjusts agent weights automatically.

### 🔌 Rich Integrations
- **Slack** — Send messages to channels
- **Discord** — Post to servers
- **Notion** — Create pages and databases
- **Stripe** — Handle payment events
- **Webhooks** — Connect any HTTP API

### 📊 Visual DAG Editor
Drag-and-drop workflow builder with nodes for triggers, agents, conditions, and actions.

### 🎨 Prompt Optimizer
AI-powered prompt refinement that learns from successful executions.

### 📚 Template Gallery
Pre-built workflows for common use cases — support triage, lead qualification, content moderation.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FLEXCODE ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   TRIGGERS   │────▶│   WORKFLOW   │────▶│   ACTIONS    │    │
│  │  • Webhook   │     │    ENGINE    │     │  • Slack     │    │
│  │  • Manual    │     │   (DAG)      │     │  • Discord   │    │
│  │  • Schedule  │     │              │     │  • Notion    │    │
│  └──────────────┘     └──────┬───────┘     │  • Stripe    │    │
│                              │             └──────────────┘    │
│         ┌────────────────────┼────────────────────┐            │
│         ▼                    ▼                    ▼            │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │  AGENT 1    │     │  AGENT 2    │     │  AGENT 3    │       │
│  │  (Formal)   │     │  (Friendly) │     │  (Concise)  │       │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘       │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             ▼                                   │
│                    ┌─────────────────┐                         │
│                    │   SUPERVISOR    │                         │
│                    │  (Score 1-100)  │                         │
│                    └────────┬────────┘                         │
│                             ▼                                   │
│                    ┌─────────────────┐                         │
│                    │  DECISION NODE  │                         │
│                    │  (RL-Weighted)  │                         │
│                    └────────┬────────┘                         │
│                             ▼                                   │
│                    ┌─────────────────┐                         │
│                    │ FEEDBACK LAYER  │◀── User: 👍 / 👎        │
│                    │  (Learn + Log)  │                         │
│                    └─────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
flexcode/
├── backend/
│   ├── main.py                 # FastAPI app with all routes
│   ├── database.py             # SQLite + CRUD operations
│   ├── llm_service.py          # Async LLM wrapper
│   ├── workflow_engine.py      # DAG execution engine
│   ├── rl_engine.py            # Reinforcement learning
│   ├── prompt_optimizer.py     # AI prompt refinement
│   ├── prompts.py              # Agent prompt templates
│   └── integrations/
│       ├── slack.py            # Slack integration
│       ├── discord.py          # Discord integration
│       ├── notion.py           # Notion integration
│       ├── stripe.py           # Stripe integration
│       └── webhook.py          # HTTP webhooks
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main layout
│   │   ├── App.css             # Dark glassmorphism theme
│   │   ├── api.js              # Backend API client
│   │   └── components/
│   │       ├── WorkflowDashboard.jsx
│   │       ├── WorkflowEditor.jsx
│   │       ├── RunResults.jsx
│   │       ├── RLInsights.jsx
│   │       ├── PromptOptimizer.jsx
│   │       ├── TemplateGallery.jsx
│   │       └── dag/            # Visual DAG editor
│   │           ├── DAGCanvas.jsx
│   │           ├── NodePalette.jsx
│   │           └── NodeConfigPanel.jsx
│   └── package.json
│
├── PITCH.md                    # 3-minute pitch script
├── COMPLETION.md               # System validation report
└── start.bat                   # Windows startup script
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+

### Installation

```bash
# Clone the repo
git clone https://github.com/Akshith7707/hack.git
cd hack/flexmail

# Backend setup
cd backend
pip install -r requirements.txt

# Frontend setup (new terminal)
cd frontend
npm install
```

### Running

**Option 1: Using start script (Windows)**
```bash
./start.bat
```

**Option 2: Manual**
```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

### First Run

1. Open http://localhost:5173
2. Click **"⚡ Quick Setup"** to create demo agents
3. Go to **Workflows** → Click **Run** on any workflow
4. Paste sample input and click **Execute Pipeline**
5. Review the **Arena** where agents compete
6. Provide feedback (👍/👎) to train the RL system

---

## 🔌 Integrations

| Integration | Status | Capabilities |
|------------|--------|--------------|
| **Webhook** | ✅ Ready | Receive/Send HTTP requests |
| **Slack** | ✅ Ready | Send messages to channels |
| **Discord** | ✅ Ready | Post to servers/channels |
| **Notion** | ✅ Ready | Create pages, update databases |
| **Stripe** | ✅ Ready | Payment events, customer data |
| **Email** | ✅ Ready | Mock email triggers |

### Adding Custom Integrations

```python
from integrations.base import Integration

class MyIntegration(Integration):
    name = "my_service"
    
    async def trigger(self, config):
        # Fetch data from your service
        return data
    
    async def action(self, config, data):
        # Send data to your service
        return result
```

---

## 🧠 Reinforcement Learning

### How It Works

1. **Compete** — 3 agents generate outputs in parallel
2. **Score** — Supervisor rates each output 1-100
3. **Select** — Decision agent picks best using weights + scores
4. **Feedback** — User accepts 👍 or rejects 👎
5. **Learn** — Weights update based on feedback

### Weight Update

```python
LEARNING_RATE = 0.05

# On Accept: winner weight += LEARNING_RATE
# On Reject: winner weight -= LEARNING_RATE, others gain
```

### View RL Insights

Navigate to **RL Insights** tab to see:
- Current agent weights
- Weight history over time
- Win/loss statistics
- Feedback patterns

---

## 🎬 Demo & Pitch

See **[PITCH.md](PITCH.md)** for a complete 3-minute pitch script including:
- 30 sec introduction
- 2 min live demo (2 workflows)
- 30 sec vision statement

---

## 📊 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents` | List all agents |
| `POST` | `/api/agents` | Create new agent |
| `GET` | `/api/workflows` | List workflows |
| `POST` | `/api/workflows/{id}/run` | Execute workflow |
| `GET` | `/api/executions` | List past runs |
| `POST` | `/api/feedback` | Submit feedback |
| `GET` | `/api/weights` | Get RL weights |
| `GET` | `/health` | Health check |

### Full API docs: http://localhost:8000/docs

---

## 🛣️ Roadmap

### ✅ Completed
- [x] Multi-agent competition pipeline
- [x] RL feedback system
- [x] Visual DAG editor
- [x] 5+ integrations (Slack, Discord, Notion, Stripe, Webhook)
- [x] Template gallery
- [x] Prompt optimizer
- [x] Dark glassmorphism UI

### 🔜 Coming Soon
- [ ] Workflow marketplace
- [ ] Team collaboration
- [ ] Custom agent builder
- [ ] API keys & auth
- [ ] Scheduled triggers
- [ ] Enterprise SSO

---

## 🎨 UI Design

- **Theme**: Dark (#0d0d12)
- **Style**: Glassmorphism with subtle gradients
- **Accent**: Indigo → Purple gradient
- **Font**: Inter
- **Animations**: Scroll reveals, staggered cards

---

## 🙏 Built With

- [FastAPI](https://fastapi.tiangolo.com/) — Backend framework
- [React](https://react.dev/) — Frontend framework
- [Vite](https://vitejs.dev/) — Build tool
- [SQLite](https://sqlite.org/) — Database
- [Featherless.ai](https://featherless.ai/) — LLM API

---

## 📝 License

MIT License — Built for hackathons and beyond.

---

<div align="center">

**🔥 FlexCode** — Where AI agents become your team.

*Stop connecting apps. Start building intelligent teams.*

</div>
