import asyncio
import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator

from database import (
    get_agents_by_type, get_agent_by_id, get_weights, 
    save_run, save_log_entry
)
from llm_service import call_llm
from prompts import (
    build_classifier_prompt, build_worker_prompt, 
    build_supervisor_prompt, build_decision_prompt,
    build_supervisor_input, build_decision_input
)
from context_engine import get_context_signals

# Store for SSE streaming
run_logs: Dict[str, List[Dict]] = {}


def parse_classification(response: str) -> str:
    """Extract category from classifier response"""
    match = re.search(r'CATEGORY:\s*(\w+)', response, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return "UNKNOWN"


def parse_supervisor_scores(response: str) -> Dict[int, int]:
    """Extract scores from supervisor response"""
    scores = {}
    for i in range(1, 4):
        match = re.search(rf'SCORE_{i}:\s*(\d+)', response)
        if match:
            scores[i] = int(match.group(1))
        else:
            scores[i] = 70  # Default score
    return scores


def parse_decision(response: str) -> Dict[str, str]:
    """Extract decision details from decision agent response"""
    result = {
        "selected": "",
        "final": "",
        "reason": ""
    }
    
    # Extract SELECTED
    match = re.search(r'SELECTED:\s*(.+?)(?=\n|FINAL:|$)', response, re.IGNORECASE)
    if match:
        result["selected"] = match.group(1).strip()
    
    # Extract FINAL - everything between FINAL: and REASON:
    match = re.search(r'FINAL:\s*(.+?)(?=REASON:|$)', response, re.IGNORECASE | re.DOTALL)
    if match:
        result["final"] = match.group(1).strip()
    
    # Extract REASON
    match = re.search(r'REASON:\s*(.+?)$', response, re.IGNORECASE | re.DOTALL)
    if match:
        result["reason"] = match.group(1).strip()
    
    return result


def add_log(run_id: str, agent_id: str, agent_name: str, agent_type: str, 
            input_text: str, output_text: str, step_order: int):
    """Add log entry and save to database"""
    log_entry = {
        "agent_id": agent_id,
        "agent_name": agent_name,
        "agent_type": agent_type,
        "input_preview": input_text[:100] + "..." if len(input_text) > 100 else input_text,
        "output_preview": output_text[:200] + "..." if len(output_text) > 200 else output_text,
        "output_full": output_text,
        "step_order": step_order,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if run_id not in run_logs:
        run_logs[run_id] = []
    run_logs[run_id].append(log_entry)
    
    # Save to database
    save_log_entry(run_id, agent_id, agent_name, agent_type, input_text, output_text, step_order)


def get_run_log_stream(run_id: str) -> List[Dict]:
    """Get logs for SSE streaming"""
    return run_logs.get(run_id, [])


async def run_workflow(input_data: str) -> Dict:
    """
    Main orchestrator - runs the full pipeline:
    1. Classifier categorizes input
    2. All 3 workers generate responses in parallel
    3. Supervisor scores all responses
    4. Decision agent picks the best
    """
    run_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    run_logs[run_id] = []
    
    step = 0
    
    # Step 1: Classification
    classifiers = get_agents_by_type("classifier")
    if not classifiers:
        raise ValueError("No classifier agent found. Please set up agents first.")
    
    classifier = classifiers[0]
    classifier_prompt = build_classifier_prompt()
    classification_response = await call_llm(classifier_prompt, input_data)
    classification = parse_classification(classification_response)
    
    step += 1
    add_log(run_id, classifier['id'], classifier['name'], "classifier", 
            input_data, classification_response, step)
    
    # Step 2: Get all workers and run in parallel
    workers = get_agents_by_type("worker")
    if len(workers) < 3:
        raise ValueError("Need at least 3 worker agents. Please set up agents first.")
    
    async def run_worker(worker: Dict) -> Dict:
        prompt = build_worker_prompt(worker['style'], worker['goal'])
        output = await call_llm(prompt, f"Classification: {classification}\n\nEmail:\n{input_data}")
        return {
            "agent_id": worker['id'],
            "agent_name": worker['name'],
            "style": worker['style'],
            "output": output
        }
    
    # Run all workers in parallel
    worker_results = await asyncio.gather(*[run_worker(w) for w in workers])
    worker_outputs = list(worker_results)
    
    # Log worker outputs
    for output in worker_outputs:
        step += 1
        add_log(run_id, output['agent_id'], output['agent_name'], "worker",
                input_data, output['output'], step)
    
    # Step 3: Supervisor review
    supervisors = get_agents_by_type("supervisor")
    if not supervisors:
        raise ValueError("No supervisor agent found. Please set up agents first.")
    
    supervisor = supervisors[0]
    supervisor_prompt = build_supervisor_prompt()
    supervisor_input = build_supervisor_input(worker_outputs)
    supervisor_response = await call_llm(supervisor_prompt, supervisor_input)
    
    step += 1
    add_log(run_id, supervisor['id'], supervisor['name'], "supervisor",
            supervisor_input[:500], supervisor_response, step)
    
    # Parse scores and add to worker outputs
    scores = parse_supervisor_scores(supervisor_response)
    for i, output in enumerate(worker_outputs):
        output['score'] = scores.get(i + 1, 70)
    
    # Step 4: Get context signals
    context_signals = get_context_signals(input_data, classification)
    
    # Step 5: Get RL weights
    weights = get_weights()
    
    # Step 6: Decision agent
    decision_agents = get_agents_by_type("decision")
    if not decision_agents:
        raise ValueError("No decision agent found. Please set up agents first.")
    
    decision_agent = decision_agents[0]
    decision_prompt = build_decision_prompt()
    decision_input = build_decision_input(worker_outputs, supervisor_response, weights, context_signals)
    decision_response = await call_llm(decision_prompt, decision_input)
    
    step += 1
    add_log(run_id, decision_agent['id'], decision_agent['name'], "decision",
            decision_input[:500], decision_response, step)
    
    # Step 7: Parse decision
    decision = parse_decision(decision_response)
    
    # Find the selected agent ID
    selected_agent_id = None
    for output in worker_outputs:
        if output['agent_name'].lower() in decision['selected'].lower() or \
           output['style'].lower() in decision['selected'].lower():
            selected_agent_id = output['agent_id']
            break
    
    # If no match found, use the highest scored one
    if not selected_agent_id:
        selected_agent_id = max(worker_outputs, key=lambda x: x.get('score', 0))['agent_id']
    
    # Step 8: Save run to database
    run_data = {
        "id": run_id,
        "input_data": input_data,
        "classification": classification,
        "worker_outputs": worker_outputs,
        "supervisor_review": supervisor_response,
        "decision_output": decision_response,
        "selected_agent": selected_agent_id,
        "final_output": decision['final'],
        "context_signals": context_signals,
        "created_at": created_at
    }
    save_run(run_data)
    
    # Return complete result
    return {
        "run_id": run_id,
        "classification": classification,
        "worker_outputs": worker_outputs,
        "supervisor_review": supervisor_response,
        "decision_output": decision_response,
        "selected_agent": selected_agent_id,
        "selected_agent_name": decision['selected'],
        "final_output": decision['final'],
        "decision_reason": decision['reason'],
        "context_signals": context_signals,
        "weights": {k: v for k, v in weights.items()},
        "logs": run_logs.get(run_id, [])
    }
