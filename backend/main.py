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
    get_run_logs, get_all_runs, save_feedback,
    create_workflow, get_all_workflows, get_workflow, update_workflow, delete_workflow,
    get_execution, get_execution_logs, get_recent_executions, reset_agent_drift
)
from workflow_engine import run_workflow, get_run_log_stream, run_dag_workflow
from rl_engine import on_accept, on_reject, on_feedback, get_weight_summary, get_weights_with_history
from integrations import (
    get_next_mock_email, format_email_for_input, reset_mock_emails, 
    list_integrations, get_integration
)
from gmail_service import (
    gmail_service, get_gmail_status, authenticate_gmail, 
    disconnect_gmail, fetch_gmail_emails, format_email_for_workflow
)

app = FastAPI(
    title="FlexCode API",
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
    
    # Save feedback with agent_id
    save_feedback(
        run_id=request.run_id, 
        selected_agent=selected_agent, 
        action=request.action,
        agent_id=selected_agent
    )
    
    # Update RL weights with drift detection
    on_feedback(selected_agent, request.action)
    
    # Get updated weights
    weights = get_weight_summary()
    
    return {
        "message": f"Feedback '{request.action}' recorded",
        "weights": weights
    }


# Weights endpoints
@app.get("/api/weights")
async def get_agent_weights():
    return get_weight_summary()


@app.get("/api/weights/history")
async def get_weights_history():
    """Get weights with history for charting"""
    return get_weights_with_history()


# ============== WORKFLOW CRUD ==============

@app.get("/api/workflows")
async def list_workflows():
    """Get all workflows"""
    return get_all_workflows()


@app.post("/api/workflows")
async def create_new_workflow(request: Request):
    """Create a new workflow"""
    data = await request.json()
    workflow_id = str(uuid.uuid4())
    
    workflow = create_workflow(
        workflow_id=workflow_id,
        name=data.get('name', 'Untitled Workflow'),
        description=data.get('description'),
        trigger_type=data.get('trigger_type', 'manual'),
        nodes=data.get('nodes', []),
        edges=data.get('edges', [])
    )
    
    return workflow


@app.get("/api/workflows/{workflow_id}")
async def get_workflow_details(workflow_id: str):
    """Get workflow by ID"""
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@app.put("/api/workflows/{workflow_id}")
async def update_workflow_details(workflow_id: str, request: Request):
    """Update workflow"""
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    data = await request.json()
    update_workflow(workflow_id, **data)
    
    return get_workflow(workflow_id)


@app.delete("/api/workflows/{workflow_id}")
async def remove_workflow(workflow_id: str):
    """Delete workflow"""
    success = delete_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"message": "Workflow deleted successfully"}


@app.post("/api/workflows/{workflow_id}/run")
async def execute_stored_workflow(workflow_id: str, request: Request):
    """Execute a stored workflow"""
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    try:
        data = await request.json()
        trigger_data = data.get('trigger_data', data)
        # Ensure trigger_data has an 'input' key
        if isinstance(trigger_data, dict) and 'input' not in trigger_data:
            trigger_data['input'] = trigger_data.get('text', trigger_data.get('data', str(trigger_data)))
    except:
        trigger_data = {"input": "No input provided"}
    
    try:
        result = await run_dag_workflow(workflow_id, trigger_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


# ============== EXECUTION ENDPOINTS ==============

@app.get("/api/executions")
async def list_executions(limit: int = 20):
    """Get recent executions"""
    return get_recent_executions(limit)


@app.get("/api/executions/{execution_id}")
async def get_execution_details(execution_id: str):
    """Get execution by ID with logs"""
    execution = get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    logs = get_execution_logs(execution_id)
    return {**execution, "logs": logs}


@app.post("/api/executions/{execution_id}/feedback")
async def submit_execution_feedback(execution_id: str, request: Request):
    """Submit feedback for an execution"""
    execution = get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    data = await request.json()
    action = data.get('action', 'accept')
    agent_id = execution.get('selected_agent_id')
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="No agent selected for this execution")
    
    # Save feedback
    save_feedback(
        run_id=None,
        selected_agent=agent_id,
        action=action,
        agent_id=agent_id,
        execution_id=execution_id
    )
    
    # Update RL weights with drift detection
    on_feedback(agent_id, action, execution_id=execution_id)
    
    return {
        "message": f"Feedback '{action}' recorded",
        "weights": get_weight_summary()
    }


# ============== DRIFT MANAGEMENT ==============

@app.post("/api/agents/{agent_id}/reset-drift")
async def reset_drift(agent_id: str):
    """Reset drift flag for an agent"""
    agent = get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    reset_agent_drift(agent_id)
    
    return {"message": f"Drift flag reset for agent '{agent['name']}'"}


@app.get("/api/agents/{agent_id}/drift-status")
async def get_drift_status(agent_id: str):
    """Get drift status for an agent"""
    agent = get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent_id": agent_id,
        "agent_name": agent.get('name'),
        "drift_flag": bool(agent.get('drift_flag')),
        "drift_suggestion": agent.get('drift_suggestion')
    }


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
        # Get 5 mock emails
        emails = []
        for _ in range(5):
            email = get_next_mock_email()
            if email:
                emails.append(email)
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
    """Create all demo agents AND two working workflows with one click"""
    
    # Check if agents already exist
    existing = get_all_agents()
    if len(existing) >= 5:
        # Still create workflows if missing
        existing_workflows = get_all_workflows()
        if len(existing_workflows) == 0:
            _create_demo_workflows()
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
    reset_mock_emails()
    
    # Create the two demo workflows
    _create_demo_workflows()
    
    return {"message": "FlexCode agents and workflows created successfully", "agents": created}


def _create_demo_workflows():
    """Create two pre-built demo workflows"""
    existing = get_all_workflows()
    existing_names = [w['name'] for w in existing]
    
    # Workflow 1: Email Auto-Responder
    if "📧 Email Auto-Responder" not in existing_names:
        create_workflow(
            workflow_id=str(uuid.uuid4()),
            name="📧 Email Auto-Responder",
            description="Analyzes incoming emails, generates 3 competing response drafts, scores them, and picks the best one. Learns from your feedback over time.",
            trigger_type="manual",
            nodes=[
                {"id": "trigger", "type": "trigger", "config": {"integration": "mock_email"}},
                {"id": "classify", "type": "agent", "agent_type": "classifier", "config": {"input": "$trigger.input"}},
                {"id": "compete", "type": "competition", "config": {"input": "$classify.output", "parallel": True}},
            ],
            edges=[
                {"from": "trigger", "to": "classify"},
                {"from": "classify", "to": "compete"},
            ]
        )
    
    # Workflow 2: Customer Support Triage
    if "🎫 Customer Support Triage" not in existing_names:
        create_workflow(
            workflow_id=str(uuid.uuid4()),
            name="🎫 Customer Support Triage",
            description="Triages customer support tickets by priority, generates response options from 3 agents, and picks the most empathetic yet effective reply.",
            trigger_type="manual",
            nodes=[
                {"id": "trigger", "type": "trigger", "config": {"integration": "manual"}},
                {"id": "classify", "type": "agent", "agent_type": "classifier", "config": {"input": "$trigger.input"}},
                {"id": "compete", "type": "competition", "config": {"input": "$classify.output", "parallel": True}},
            ],
            edges=[
                {"from": "trigger", "to": "classify"},
                {"from": "classify", "to": "compete"},
            ]
        )


# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "FlexCode API"}


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


# ============== GMAIL INTEGRATION ==============

@app.get("/api/gmail/status")
async def gmail_status():
    """Get Gmail connection status"""
    return get_gmail_status()


@app.post("/api/gmail/connect")
async def gmail_connect():
    """Initiate Gmail OAuth connection"""
    status = get_gmail_status()
    
    if not status["available"]:
        raise HTTPException(
            status_code=400, 
            detail="Gmail API libraries not installed. Run: pip install google-auth-oauthlib google-api-python-client"
        )
    
    if not status["has_credentials"]:
        raise HTTPException(
            status_code=400,
            detail="credentials.json not found. Download OAuth credentials from Google Cloud Console and save as backend/credentials.json"
        )
    
    if status["authenticated"]:
        return {"message": "Already connected", "email": status["user_email"]}
    
    # Try to authenticate (will open browser for OAuth)
    try:
        success = authenticate_gmail()
        if success:
            new_status = get_gmail_status()
            return {
                "message": "Gmail connected successfully",
                "email": new_status["user_email"]
            }
        else:
            raise HTTPException(status_code=400, detail="Authentication failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/gmail/disconnect")
async def gmail_disconnect():
    """Disconnect Gmail account"""
    success = disconnect_gmail()
    if success:
        return {"message": "Gmail disconnected"}
    raise HTTPException(status_code=500, detail="Failed to disconnect")


@app.get("/api/gmail/emails")
async def gmail_fetch_emails(max_results: int = 5):
    """Fetch latest emails from Gmail"""
    status = get_gmail_status()
    
    if not status["authenticated"]:
        # Return mock data if not authenticated
        emails = []
        for _ in range(max_results):
            email = get_next_mock_email()
            if email:
                emails.append(email)
        return {
            "source": "mock",
            "message": "Using mock data (Gmail not connected)",
            "emails": emails
        }
    
    emails = fetch_gmail_emails(max_results)
    return {
        "source": "gmail",
        "email": status["user_email"],
        "emails": emails
    }


@app.post("/api/gmail/process")
async def gmail_process_email(request: Request):
    """Process an email through the AI workflow"""
    data = await request.json()
    email_id = data.get("email_id")
    email_data = data.get("email")
    workflow_id = data.get("workflow_id")
    
    # Format email for workflow
    if email_data:
        input_text = format_email_for_workflow(email_data)
    else:
        raise HTTPException(status_code=400, detail="No email data provided")
    
    # Run through workflow
    if workflow_id:
        # Use specific workflow
        workflow = get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        result = await run_dag_workflow(workflow_id, {"input": input_text})
    else:
        # Use legacy workflow
        result = await run_workflow(input_text)
    
    return {
        "email_id": email_id,
        "input": input_text[:200] + "..." if len(input_text) > 200 else input_text,
        "result": result
    }


@app.post("/api/gmail/auto-process")
async def gmail_auto_process(request: Request):
    """Auto-process all unread emails through workflow"""
    data = await request.json()
    workflow_id = data.get("workflow_id")
    max_emails = data.get("max_emails", 3)
    
    status = get_gmail_status()
    
    # Get emails (Gmail or mock)
    if status["authenticated"]:
        emails = fetch_gmail_emails(max_emails)
        source = "gmail"
    else:
        emails = []
        for _ in range(max_emails):
            email = get_next_mock_email()
            if email:
                emails.append(email)
        source = "mock"
    
    results = []
    
    for email in emails:
        try:
            input_text = format_email_for_workflow(email)
            
            if workflow_id:
                result = await run_dag_workflow(workflow_id, {"input": input_text})
            else:
                result = await run_workflow(input_text)
            
            results.append({
                "email_id": email.get("id"),
                "subject": email.get("subject"),
                "status": "processed",
                "selected_agent": result.get("selected_agent_name"),
                "response_preview": result.get("final_output", "")[:200]
            })
        except Exception as e:
            results.append({
                "email_id": email.get("id"),
                "subject": email.get("subject"),
                "status": "error",
                "error": str(e)
            })
    
    return {
        "source": source,
        "processed": len([r for r in results if r["status"] == "processed"]),
        "errors": len([r for r in results if r["status"] == "error"]),
        "results": results
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
