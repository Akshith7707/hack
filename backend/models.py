from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum


class AgentType(str, Enum):
    CLASSIFIER = "classifier"
    WORKER = "worker"
    SUPERVISOR = "supervisor"
    DECISION = "decision"


class AgentStyle(str, Enum):
    DETAILED = "detailed"
    CONCISE = "concise"
    FRIENDLY = "friendly"


class AgentCreate(BaseModel):
    name: str
    role: str
    goal: str
    type: AgentType
    style: Optional[AgentStyle] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    goal: str
    type: str
    style: Optional[str] = None
    model: Optional[str] = None
    created_at: str
    weight: Optional[float] = None
    times_selected: Optional[int] = None
    times_accepted: Optional[int] = None
    times_rejected: Optional[int] = None


class WorkflowRunRequest(BaseModel):
    input_data: str


class FeedbackRequest(BaseModel):
    run_id: str
    action: str  # 'accept' or 'reject'


class WorkerOutput(BaseModel):
    agent_id: str
    agent_name: str
    style: str
    output: str
    score: Optional[int] = None


class ContextSignals(BaseModel):
    urgency: str
    time_period: str
    input_length: int
    historical_preference: Optional[str] = None
    recent_rejections: int


class WorkflowRunResponse(BaseModel):
    run_id: str
    classification: str
    worker_outputs: List[Dict[str, Any]]
    supervisor_review: str
    decision_output: str
    selected_agent: str
    final_output: str
    context_signals: Dict[str, Any]
    weights: Dict[str, Any]
    logs: List[Dict[str, Any]]


class WeightInfo(BaseModel):
    agent_id: str
    agent_name: str
    style: str
    weight: float
    times_selected: int
    times_accepted: int
    times_rejected: int


class MockEmail(BaseModel):
    id: int
    subject: str
    sender: str
    body: str
    urgency: str
