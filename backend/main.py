import uuid
import json
import asyncio
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from models import (
    AgentCreate, AgentResponse, WorkflowRunRequest, 
    FeedbackRequest, WorkflowRunResponse
)
from database import (
    init_db, create_agent, get_all_agents, get_agents_by_type,
    get_agent_by_id, delete_agent, get_weights, get_run, 
    get_run_logs, get_all_runs, save_feedback
)
from workflow_engine import run_workflow, get_run_log_stream
from rl_engine import on_accept, on_reject, get_weight_summary
from integrations import (
    get_next_mock_email, format_email_for_input, reset_processed_emails, 
    fetch_latest_emails, list_integrations, get_integration
)

app = FastAPI(
    title="FlowForge API",
    description="Zapier for Autonomous AI Teams - No-code workflow automation with multi-agent AI",
    version="2.0.0"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()


# Agent endpoints
@app.get("/api/agents", response_model=List[AgentResponse])
async def list_agents():
    agents = get_all_agents()
    return agents


@app.post("/api/agents", response_model=AgentResponse)
async def create_new_agent(agent: AgentCreate):
    agent_id = str(uuid.uuid4())
    result = create_agent(
        agent_id=agent_id,
        name=agent.name,
        role=agent.role,
        goal=agent.goal,
        agent_type=agent.type.value,
        style=agent.style.value if agent.style else None
    )
    return result


@app.delete("/api/agents/{agent_id}")
async def remove_agent(agent_id: str):
    success = delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted successfully"}


# Workflow endpoints
@app.post("/api/workflow/run")
async def execute_workflow(request: WorkflowRunRequest):
    try:
        result = await run_workflow(request.input_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")


@app.get("/api/workflow/runs")
async def list_runs():
    runs = get_all_runs()
    return runs


@app.get("/api/workflow/runs/{run_id}")
async def get_run_details(run_id: str):
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    logs = get_run_logs(run_id)
    return {**run, "logs": logs}


# Feedback endpoint
@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    run = get_run(request.run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.get('feedback'):
        raise HTTPException(status_code=400, detail="Feedback already submitted for this run")
    
    selected_agent = run.get('selected_agent')
    
    # Save feedback
    save_feedback(request.run_id, selected_agent, request.action)
    
    # Update RL weights
    if request.action == 'accept':
        on_accept(selected_agent)
    elif request.action == 'reject':
        on_reject(selected_agent)
    
    # Get updated weights
    weights = get_weight_summary()
    
    return {
        "message": f"Feedback '{request.action}' recorded",
        "weights": weights
    }


# Weights endpoint
@app.get("/api/weights")
async def get_agent_weights():
    return get_weight_summary()


# Mock email endpoint
@app.get("/api/mock-email/next")
async def get_next_email():
    email = get_next_mock_email()
    if not email:
        raise HTTPException(status_code=404, detail="No more mock emails")
    return {
        **email,
        "formatted": format_email_for_input(email)
    }


# Gmail API endpoint - Fetch latest 5 emails
@app.get("/api/emails")
async def get_gmail_emails():
    """Fetch latest 5 emails (mock data for demo)"""
    try:
        emails = fetch_latest_emails(max_results=5)
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Integrations endpoints
@app.get("/api/integrations")
async def get_integrations():
    """List all available integrations"""
    return list_integrations()


@app.post("/api/integrations/{name}/action")
async def run_integration_action(name: str, config: dict, data: dict):
    """Run an integration action"""
    integration = get_integration(name)
    if not integration:
        raise HTTPException(status_code=404, detail=f"Integration '{name}' not found")
    try:
        result = await integration.action(config, data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# SSE stream for real-time logs
@app.get("/api/stream/{run_id}")
async def stream_logs(run_id: str):
    async def event_generator():
        last_count = 0
        max_wait = 60  # Max seconds to wait
        waited = 0
        
        while waited < max_wait:
            logs = get_run_log_stream(run_id)
            if len(logs) > last_count:
                for log in logs[last_count:]:
                    yield {
                        "event": "log",
                        "data": json.dumps(log)
                    }
                last_count = len(logs)
            
            # Check if workflow is complete (has decision log)
            if any(log.get('agent_type') == 'decision' for log in logs):
                yield {
                    "event": "complete",
                    "data": json.dumps({"status": "completed"})
                }
                break
            
            await asyncio.sleep(0.5)
            waited += 0.5
    
    return EventSourceResponse(event_generator())


# Demo setup endpoint
@app.post("/api/demo/setup")
async def setup_demo():
    """Create all demo agents with one click"""
    
    # Check if agents already exist
    existing = get_all_agents()
    if len(existing) >= 5:
        return {"message": "Agents already set up", "agents": existing}
    
    demo_agents = [
        {
            "name": "Analyzer",
            "role": "Analyzer",
            "goal": "Analyze and categorize incoming data by urgency and type",
            "type": "classifier",
            "style": None
        },
        {
            "name": "Detailed Agent",
            "role": "Executor",
            "goal": "Generate comprehensive, thorough responses that address all points",
            "type": "worker",
            "style": "detailed"
        },
        {
            "name": "Concise Agent",
            "role": "Executor", 
            "goal": "Generate brief, direct responses that get straight to the point",
            "type": "worker",
            "style": "concise"
        },
        {
            "name": "Friendly Agent",
            "role": "Executor",
            "goal": "Generate warm, empathetic responses that build rapport",
            "type": "worker",
            "style": "friendly"
        },
        {
            "name": "Reviewer",
            "role": "Reviewer",
            "goal": "Evaluate and score response drafts for quality",
            "type": "supervisor",
            "style": None
        },
        {
            "name": "Decision Agent",
            "role": "Decision",
            "goal": "Select the best response based on scores, preferences, and context",
            "type": "decision",
            "style": None
        }
    ]
    
    created = []
    for agent_data in demo_agents:
        agent_id = str(uuid.uuid4())
        agent = create_agent(
            agent_id=agent_id,
            name=agent_data["name"],
            role=agent_data["role"],
            goal=agent_data["goal"],
            agent_type=agent_data["type"],
            style=agent_data["style"]
        )
        created.append(agent)
    
    # Reset mock data
    reset_processed_emails()
    
    return {"message": "FlowForge agents created successfully", "agents": created}


# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "FlowForge API"}


# ============== WEBHOOK TRIGGER ==============

@app.post("/api/webhook/trigger")
async def webhook_trigger(request: Request):
    """
    Webhook endpoint for external triggers (Zapier-style)
    POST any JSON data to trigger a workflow
    """
    try:
        data = await request.json()
        
        # Convert to input string
        if isinstance(data, dict):
            input_text = json.dumps(data, indent=2)
        else:
            input_text = str(data)
        
        # Run workflow
        result = await run_workflow(input_text)
        
        return {
            "success": True,
            "run_id": result["run_id"],
            "classification": result.get("classification"),
            "selected_agent": result.get("selected_agent_name"),
            "output": result.get("final_output")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhook/{workflow_name}")
async def named_webhook_trigger(workflow_name: str, request: Request):
    """
    Named webhook endpoint for specific workflows
    Example: POST /api/webhook/payment-recovery
    """
    try:
        data = await request.json()
        
        # Add workflow context
        input_text = f"Workflow: {workflow_name}\n\nData:\n{json.dumps(data, indent=2)}"
        
        # Run workflow
        result = await run_workflow(input_text)
        
        return {
            "success": True,
            "workflow": workflow_name,
            "run_id": result["run_id"],
            "output": result.get("final_output")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
