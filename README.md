# 🔥 FlexCode

> **Zapier for Autonomous AI Teams — Build AI-Powered Automations with No Code**

FlexCode transforms your email workflows into a powerful, generalized automation platform where AI agents collaborate to complete tasks, learn from feedback, and integrate with real-world tools.

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)

---

## 🎯 What is FlexCode?

FlexCode is a **no-code platform** that lets you:

1. **Build workflows** using AI agents that collaborate autonomously
2. **Connect integrations** (Webhooks, Slack, Email, HTTP APIs)
3. **Learn from feedback** — agents improve over time with RL
4. **Automate anything** — not just emails, but any data processing task

### Demo Use Case

```
📧 Email arrives → 🤖 AI classifies it → 🔀 3 agents draft responses 
→ 👁️ Supervisor scores them → 🎯 Best one selected → 📤 Send via Slack
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FlexCode ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   TRIGGERS   │────▶│   WORKFLOW   │────▶│   ACTIONS    │    │
│  │  • Webhook   │     │    ENGINE    │     │  • Slack     │    │
│  │  • Manual    │     │   (DAG)      │     │  • Webhook   │    │
│  │  • Schedule  │     │              │     │  • HTTP      │    │
│  └──────────────┘     └──────┬───────┘     └──────────────┘    │
│                              │                                  │
│         ┌────────────────────┼────────────────────┐            │
│         ▼                    ▼                    ▼            │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   AGENT 1   │     │   AGENT 2   │     │   AGENT 3   │       │
│  │  Analyzer   │     │  Executor   │     │  Reviewer   │       │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘       │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
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
FlexCode/
├── backend/
│   ├── main.py              # FastAPI app with all routes
│   ├── models.py            # Pydantic schemas
│   ├── database.py          # SQLite setup + CRUD
│   ├── llm_service.py       # Async LLM wrapper
│   ├── prompts.py           # Generic agent prompts
│   ├── orchestrator.py      # Workflow execution engine
│   ├── rl_engine.py         # Reinforcement learning layer
│   ├── context_engine.py    # Context signal collector
│   ├── integrations.py      # Plugin-based integrations
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main layout
│   │   ├── App.css          # Dark glassmorphism design
│   │   ├── api.js           # Backend API client
│   │   └── components/      # React components
│   └── package.json
│
└── demo/
    └── sample_emails.json   # Demo data
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

```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload
# → http://localhost:8000

# Terminal 2 - Frontend  
cd frontend
npm run dev
# → http://localhost:5173
```

### First Run

1. Open http://localhost:5173
2. Click **"⚡ Quick Demo Setup"** to create agents
3. Select an email and click **"🚀 Run Workflow"**
4. Review outputs and provide feedback (👍/👎)

---

## 🔌 Integration System

FlexCode uses a **plugin-based architecture** for integrations:

### Available Integrations

| Integration | Triggers | Actions |
|------------|----------|---------|
| **Webhook** | Receive HTTP POST | Send HTTP request |
| **Mock Email** | Fetch demo emails | Send mock email |
| **Slack** | — | Send message to channel |

### Adding Custom Integrations

```python
from integrations import Integration

class NotionIntegration(Integration):
    name = "notion"
    description = "Notion workspace integration"
    
    async def trigger(self, config):
        # Fetch from Notion API
        pass
    
    async def action(self, config, data):
        # Create page in Notion
        pass
```

---

## 🤖 Agent System

### Agent Schema

```json
{
  "id": "uuid",
  "name": "Analyzer Agent",
  "role": "analyzer",
  "goal": "Extract key information from input",
  "type": "worker",
  "style": "detailed",
  "tools": ["http", "slack"],
  "memory": {},
  "feedback_history": []
}
```

### Agent Types

| Type | Purpose |
|------|---------|
| **Classifier** | Categorize input data |
| **Worker** | Generate outputs (3 variants) |
| **Supervisor** | Score and evaluate outputs |
| **Decision** | Select best output using RL |

---

## 🧠 Reinforcement Learning

FlexCode uses **practical RL** (not academic):

### How It Works

1. **Score**: Supervisor rates outputs 1-10
2. **Select**: Decision agent picks best using weights + scores
3. **Feedback**: User accepts (👍) or rejects (👎)
4. **Learn**: Weights update based on feedback

### Weight Update Rules

```python
LEARNING_RATE = 0.05
MIN_WEIGHT = 0.05

# On Accept: selected agent weight increases
# On Reject: selected agent weight decreases, others gain
```

### Data Stored

```json
{
  "input": "...",
  "output": "...",
  "agent_id": "abc123",
  "score": 8,
  "feedback": "accept",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 📊 API Reference

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents` | List all agents |
| `POST` | `/api/agents` | Create agent |
| `DELETE` | `/api/agents/{id}` | Delete agent |

### Workflows

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/workflow/run` | Execute workflow |
| `GET` | `/api/workflow/runs` | List past runs |
| `GET` | `/api/workflow/runs/{id}` | Get run details |

### Integrations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/integrations` | List integrations |
| `POST` | `/api/integrations/{name}/action` | Run action |
| `GET` | `/api/emails` | Fetch demo emails |

### Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/feedback` | Submit feedback |
| `GET` | `/api/weights` | Get RL weights |

---

## 🛣️ Roadmap

### MVP (Current)
- [x] Multi-agent pipeline
- [x] RL feedback system
- [x] Plugin-based integrations
- [x] React workflow UI

### V1 (Next)
- [ ] Visual DAG editor (drag-drop)
- [ ] More integrations (Notion, Discord, Stripe)
- [ ] Workflow templates
- [ ] Prompt optimization from feedback

### V2 (Future)
- [ ] Team collaboration
- [ ] Workflow marketplace
- [ ] Custom agent builders
- [ ] Enterprise SSO

---

## 🎬 Demo Narrative (YC Pitch)

> "Watch FlexCode automatically handle a failed Stripe payment:
>
> 1. **Webhook** receives failed payment event
> 2. **Analyzer Agent** extracts customer info + failure reason
> 3. **3 Worker Agents** draft recovery messages (formal, friendly, urgent)
> 4. **Supervisor** scores each draft
> 5. **Decision Agent** picks best one based on RL history
> 6. **Slack Action** posts to #payments channel
> 7. User clicks 👍 → system learns for next time
>
> No code. Just AI agents working together."

---

## ⚙️ Configuration

### LLM Settings

```python
# llm_service.py
BASE_URL = "https://api.featherless.ai/v1"
API_KEY = "your-api-key"
MODEL = "Qwen/Qwen2.5-7B-Instruct"
```

### Database

- **Type**: SQLite (file-based)
- **Location**: `backend/flexmail.db`

---

## 🎨 UI Design

- **Theme**: Dark (#0a0a0f)
- **Style**: Glassmorphism
- **Accent**: Indigo → Purple gradient
- **Font**: Inter

---

## 📝 License

MIT License — Built for hackathons and beyond.

---

## 🙏 Built With

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Featherless.ai](https://featherless.ai/)

**FlexCode** — Where AI agents become your team.
