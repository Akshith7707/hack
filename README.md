# 📧 FlexMail

> **Intelligent Email Response System with Multi-Agent AI & Reinforcement Learning**

FlexMail is a hackathon-ready application that uses multiple AI agents to generate, evaluate, and select the best email responses. It learns from user feedback to improve over time.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![Gmail API](https://img.shields.io/badge/Gmail%20API-EA4335?style=flat&logo=gmail&logoColor=white)

---

## 🎯 Features

- **Multi-Agent Pipeline**: Classifier → 3 Workers → Supervisor → Decision Agent
- **Reinforcement Learning**: User feedback (👍/👎) updates agent weights over time
- **Gmail Integration**: Fetch real emails via OAuth 2.0
- **Real-time Logs**: SSE streaming shows agent activity live
- **Auto Mode**: Automatically process emails every 15 seconds
- **Stunning UI**: Dark glassmorphism design with smooth animations

---

## 🏗️ Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      FRONTEND  (React + Vite)                    │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌────────┐ ┌────────┐  │
│  │  Agent   │ │ Workflow │ │ Conflict  │ │  Log   │ │ Feed-  │  │
│  │ Builder  │ │  Canvas  │ │ Dashboard │ │ Viewer │ │  back  │  │
│  └────┬─────┘ └────┬─────┘ └─────┬─────┘ └───┬────┘ └───┬────┘  │
│       └─────────────┴─────────────┴───────────┴──────────┘       │
│                              │  REST / SSE                        │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                      BACKEND  (FastAPI)                          │
│  ┌────────────┐  ┌──────────────────┐  ┌───────────────────────┐ │
│  │ Agent CRUD │  │   Orchestrator   │  │   Context Engine      │ │
│  │   API      │  │  (parallel fan   │  │  (time, urgency,      │ │
│  │            │  │   out + decide)  │  │   history signals)    │ │
│  └─────┬──────┘  └────────┬─────────┘  └──────────┬────────────┘ │
│        │                  │                        │              │
│  ┌─────┴──────────────────┴────────────────────────┴────────────┐ │
│  │              LLM Service (Featherless.ai)                    │ │
│  └──────────────────────────┬───────────────────────────────────┘ │
│                             │                                     │
│  ┌──────────────────────────┴───────────────────────────────────┐ │
│  │     RL Engine  (weight tracker + feedback loop)              │ │
│  └──────────────────────────┬───────────────────────────────────┘ │
│                             │                                     │
│  ┌──────────────────────────┴───────────────────────────────────┐ │
│  │     SQLite + Gmail API                                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Pipeline Flow

```
   📧 Email Arrives (Gmail API or Mock)
              │
              ▼
     ┌─────────────────┐
     │  🏷️ Classifier  │  → Categorizes: URGENT / FOLLOW-UP / INFORMATIONAL / SPAM
     └────────┬────────┘
              │
     ┌────────┴────────┬─────────────────┐
     ▼                 ▼                  ▼
┌──────────┐    ┌──────────┐     ┌──────────────┐
│ ✍️ Detail │    │ ✍️ Concise│     │ ✍️ Friendly  │   ← 3 WORKERS (parallel)
│  Agent   │    │  Agent   │     │   Agent      │     Different response styles
└────┬─────┘    └────┬─────┘     └──────┬───────┘
     │               │                  │
     └───────────────┼──────────────────┘
                     ▼
           ┌──────────────────┐
           │ 👁️ Supervisor    │  → Scores all 3 outputs (0-100)
           └────────┬─────────┘
                    ▼
           ┌──────────────────┐
           │ 🎯 Decision      │  → Picks best using:
           │    Agent         │     • Supervisor scores
           └────────┬─────────┘     • RL weights (user history)
                    │               • Context signals
                    ▼
           ┌──────────────────┐
           │  📤 Final Output │  → Displayed to user
           └────────┬─────────┘
                    ▼
           ┌──────────────────┐
           │ 👍👎 User Feedback│  → Updates RL weights
           │   (Accept/Reject)│     for next run
           └──────────────────┘
```

---

## 📁 Project Structure

```
flexmail/
├── backend/
│   ├── main.py              # FastAPI app with all routes
│   ├── models.py            # Pydantic schemas
│   ├── database.py          # SQLite setup + CRUD helpers
│   ├── llm_service.py       # Async OpenAI wrapper (Featherless.ai)
│   ├── prompts.py           # Agent prompt templates
│   ├── orchestrator.py      # Core pipeline (parallel workers)
│   ├── rl_engine.py         # Weight-based reinforcement learning
│   ├── context_engine.py    # Context signal collector
│   ├── integrations.py      # Gmail API + mock email loader
│   ├── credentials.json     # Gmail OAuth credentials
│   ├── token.json           # Auto-generated OAuth token
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main layout with tabs
│   │   ├── App.css          # Dark glassmorphism design system
│   │   ├── api.js           # Backend API client
│   │   ├── main.jsx         # React entry point
│   │   └── components/
│   │       ├── AgentBuilder.jsx      # Create new agents
│   │       ├── AgentCard.jsx         # Display agent info + weight
│   │       ├── WorkflowCanvas.jsx    # Pipeline visual + run button
│   │       ├── ConflictDashboard.jsx # 3-column competing responses
│   │       ├── DecisionPanel.jsx     # AI decision + reasoning
│   │       ├── FeedbackButtons.jsx   # Accept/Reject buttons
│   │       ├── WeightChart.jsx       # RL weight visualization
│   │       ├── LogViewer.jsx         # Real-time agent logs
│   │       └── AutoTrigger.jsx       # Auto-mode toggle
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
└── demo/
    └── sample_emails.json   # 10 mock emails for testing
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Gmail API credentials (credentials.json)

### Installation

```bash
# Clone or navigate to the project
cd "d:\c disk\OneDrive\Desktop\hack\flexmail"

# Backend setup
cd backend
pip install -r requirements.txt

# Frontend setup (new terminal)
cd frontend
npm install
```

### Running the Application

```bash
# Terminal 1 - Start Backend
cd backend
uvicorn main:app --reload
# Server runs at http://localhost:8000

# Terminal 2 - Start Frontend
cd frontend
npm run dev
# App runs at http://localhost:5173
```

### First Time Setup

1. Open http://localhost:5173
2. Click **"⚡ Quick Demo Setup"** to create all 6 agents
3. Click **"📬 Fetch Gmail"** (first time opens OAuth consent)
4. Select an email and click **"🚀 Run Workflow"**
5. Review the competing responses and click **👍 Accept** or **👎 Reject**

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents` | List all agents |
| `POST` | `/api/agents` | Create a new agent |
| `DELETE` | `/api/agents/{id}` | Delete an agent |
| `POST` | `/api/workflow/run` | Execute the full pipeline |
| `GET` | `/api/workflow/runs` | Get run history |
| `GET` | `/api/workflow/runs/{id}` | Get specific run details |
| `POST` | `/api/feedback` | Submit accept/reject feedback |
| `GET` | `/api/weights` | Get current RL weights |
| `GET` | `/api/emails` | Fetch 5 latest Gmail emails |
| `GET` | `/api/mock-email/next` | Get next mock email |
| `POST` | `/api/demo/setup` | Create all demo agents |
| `GET` | `/api/stream/{run_id}` | SSE stream for real-time logs |

---

## 🤖 Agent Types

| Type | Purpose | Count |
|------|---------|-------|
| **Classifier** | Categorizes emails (URGENT/FOLLOW-UP/INFORMATIONAL/SPAM) | 1 |
| **Worker** | Generates responses (detailed/concise/friendly styles) | 3 |
| **Supervisor** | Scores all worker outputs 0-100 | 1 |
| **Decision** | Picks best response using scores + RL + context | 1 |

---

## 🧠 Reinforcement Learning

The RL engine adjusts agent weights based on user feedback:

- **Accept (👍)**: Selected agent's weight increases by 5%
- **Reject (👎)**: Selected agent's weight decreases by 5%, redistributed to others
- Weights are normalized to sum to 100%
- Minimum weight clamped at 5% (agents never fully excluded)

```
Learning Rate: 0.05
Initial Weights: 33.3% each (detailed, concise, friendly)
```

---

## 📧 Gmail Integration

### Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials (Desktop app)
3. Download `credentials.json`
4. Place in `flexmail/backend/credentials.json`

### How It Works

- **Scope**: `gmail.readonly` (read-only access)
- **Auth Flow**: `run_local_server` (opens browser)
- **Token Storage**: Auto-saved to `token.json`
- **Fetches**: Latest 5 inbox emails (subject + snippet)

---

## 🎨 UI Design

- **Theme**: Dark (#0a0a0f background)
- **Style**: Glassmorphism with blur effects
- **Colors**: Indigo (#6366f1) to Purple (#8b5cf6) gradient
- **Font**: Inter (400, 500, 600, 700)
- **Animations**: Fade-in, slide-up, pulse, glow effects

---

## ⚙️ Configuration

### LLM Settings (llm_service.py)

```python
BASE_URL = "https://api.featherless.ai/v1"
API_KEY = "rc_8cad9e3f8bfc3ff04770f0c6889e3c4af225d4b6aa2dfba34e8fd9b3e21adf4a"
MODEL = "Qwen/Qwen2.5-7B-Instruct"
MAX_TOKENS = 1024
```

### Database

- **Type**: SQLite (file-based)
- **Location**: `flexmail/backend/flexmail.db`
- **Tables**: agents, agent_weights, workflow_runs, run_logs, feedback_log

---

## 📊 Sample Output

```json
{
  "run_id": "abc-123",
  "classification": "URGENT",
  "worker_outputs": [
    { "agent_name": "Detailed Responder", "style": "detailed", "score": 85, "output": "..." },
    { "agent_name": "Concise Responder", "style": "concise", "score": 78, "output": "..." },
    { "agent_name": "Friendly Responder", "style": "friendly", "score": 72, "output": "..." }
  ],
  "selected_agent": "Detailed Responder",
  "final_output": "...",
  "decision_reason": "Selected detailed response due to high score and urgent context",
  "context_signals": {
    "urgency": "URGENT",
    "time_period": "afternoon",
    "input_length": 45,
    "historical_preference": "Detailed Responder"
  }
}
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + Vite |
| Styling | Vanilla CSS (no Tailwind) |
| Backend | FastAPI (async Python) |
| Database | SQLite (raw sqlite3) |
| LLM | OpenAI SDK → Featherless.ai |
| Real-time | Server-Sent Events (SSE) |
| Email | Gmail API (OAuth 2.0) |

---

## 📝 License

MIT License - Built for hackathon demonstration purposes.

---

## 🙏 Acknowledgments

- [Featherless.ai](https://featherless.ai) for LLM API
- [Google Gmail API](https://developers.google.com/gmail/api)
- Built with ❤️ for hackathons
