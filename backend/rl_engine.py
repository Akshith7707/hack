from typing import Dict, List, Optional
from database import (
    get_weights, update_weight, increment_selected, increment_accepted, 
    increment_rejected, increment_total_runs, set_agent_drift, 
    get_agent_feedback_history, save_weight_history, get_connection
)

LEARNING_RATE = 0.05
MIN_WEIGHT = 0.05
DRIFT_THRESHOLD = 0.15  # 15% drop triggers drift flag
DRIFT_CHECK_INTERVAL = 10  # Check every N runs


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normalize weights to sum to 1.0"""
    total = sum(weights.values())
    if total == 0:
        n = len(weights)
        return {k: 1.0/n for k in weights}
    return {k: v/total for k, v in weights.items()}


def on_feedback(agent_id: str, feedback: str, score: float = None, execution_id: str = None):
    """
    Unified feedback handler with drift detection.
    Called after every user feedback.
    """
    from database import save_feedback as db_save_feedback
    
    weights_data = get_weights()
    if not weights_data:
        return
    
    # Get current weights
    current_weights = {
        aid: data.get('weight', 0.33) if isinstance(data, dict) else 0.33
        for aid, data in weights_data.items()
    }
    
    # Apply RL update
    if feedback == 'accept':
        if agent_id in current_weights:
            # Accept: weight += LR * (1 - weight)
            current_weights[agent_id] += LEARNING_RATE * (1 - current_weights[agent_id])
        increment_accepted(agent_id)
    elif feedback == 'reject':
        if agent_id in current_weights:
            # Reject: weight = max(MIN, weight - LR * weight)
            current_weights[agent_id] = max(
                MIN_WEIGHT,
                current_weights[agent_id] - LEARNING_RATE * current_weights[agent_id]
            )
            # Redistribute to others
            other_agents = [aid for aid in current_weights if aid != agent_id]
            if other_agents:
                bonus = LEARNING_RATE / len(other_agents)
                for aid in other_agents:
                    current_weights[aid] += bonus
        increment_rejected(agent_id)
    
    # Normalize
    normalized = normalize_weights(current_weights)
    
    # Clamp minimum weights
    for aid in normalized:
        normalized[aid] = max(MIN_WEIGHT, normalized[aid])
    normalized = normalize_weights(normalized)
    
    # Update database
    for aid, new_weight in normalized.items():
        update_weight(aid, new_weight)
    
    # Increment counters
    increment_selected(agent_id)
    increment_total_runs(agent_id)
    
    # Get total runs for this agent
    agent_data = weights_data.get(agent_id, {})
    total_runs = agent_data.get('total_runs', 0) + 1 if isinstance(agent_data, dict) else 1
    
    # Save feedback to database for history tracking
    db_save_feedback(
        run_id=None,
        execution_id=execution_id,
        agent_id=agent_id,
        selected_agent=agent_id,
        action=feedback,
        score=score,
        context=None
    )
    
    # Save weight history for charting
    save_weight_history(agent_id, normalized.get(agent_id, 0.33), total_runs)
    
    # Check drift every N runs
    if total_runs % DRIFT_CHECK_INTERVAL == 0:
        check_agent_drift(agent_id)


def check_agent_drift(agent_id: str):
    """
    Compare recent accept rate vs lifetime accept rate.
    If drop >= 15%, flag as drifting and generate suggestion.
    """
    from llm_service import call_llm_sync
    
    # Get last 10 feedback entries for this agent
    recent_feedback = get_agent_feedback_history(agent_id, limit=10)
    
    if len(recent_feedback) < 5:
        return  # Not enough data
    
    recent_accept_rate = sum(1 for f in recent_feedback if f.get('action') == 'accept') / len(recent_feedback)
    
    # Get lifetime stats
    weights_data = get_weights()
    agent_data = weights_data.get(agent_id, {})
    
    if not isinstance(agent_data, dict):
        return
    
    accepted = agent_data.get('times_accepted', 0)
    total = agent_data.get('times_selected', 0)
    
    if total < 10:
        return  # Not enough lifetime data
    
    lifetime_rate = accepted / total
    
    # Check if drifting (recent rate is significantly lower than lifetime)
    if lifetime_rate - recent_accept_rate >= DRIFT_THRESHOLD:
        # Agent is drifting - generate improvement suggestion
        try:
            suggestion = call_llm_sync(
                f"Agent '{agent_id}' accept rate dropped from {lifetime_rate:.0%} to {recent_accept_rate:.0%}. "
                f"Suggest one specific prompt improvement in 20 words or less."
            )
            set_agent_drift(agent_id, True, suggestion)
        except Exception:
            set_agent_drift(agent_id, True, "Consider adjusting prompt tone or response length")


def on_accept(selected_agent_id: str):
    """
    Called when user accepts a response.
    Backwards compatible wrapper.
    """
    on_feedback(selected_agent_id, 'accept')


def on_reject(selected_agent_id: str):
    """
    Called when user rejects a response.
    Backwards compatible wrapper.
    """
    on_feedback(selected_agent_id, 'reject')


def get_weight_summary() -> List[Dict]:
    """Get formatted weight information for all worker agents"""
    weights_data = get_weights()
    result = []
    
    # Also get agent info to include drift status
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, drift_flag, drift_suggestion FROM agents WHERE type = 'worker'")
    agent_rows = {row['id']: dict(row) for row in cursor.fetchall()}
    conn.close()
    
    for agent_id, data in weights_data.items():
        if isinstance(data, dict):
            agent_info = agent_rows.get(agent_id, {})
            
            times_selected = data.get('times_selected', 0)
            times_accepted = data.get('times_accepted', 0)
            
            result.append({
                "agent_id": agent_id,
                "agent_name": data.get('name', 'Unknown'),
                "style": data.get('style', 'unknown'),
                "weight": data.get('weight', 0.33),
                "times_selected": times_selected,
                "times_accepted": times_accepted,
                "times_rejected": data.get('times_rejected', 0),
                "total_runs": data.get('total_runs', 0),
                "accept_rate": times_accepted / times_selected if times_selected > 0 else 0,
                "drift_flag": bool(agent_info.get('drift_flag', False)),
                "drift_suggestion": agent_info.get('drift_suggestion')
            })
    
    return result


def get_weights_with_history() -> Dict:
    """Get weights with historical data for charting"""
    from database import get_weight_history
    
    summary = get_weight_summary()
    history = get_weight_history(limit=200)
    
    # Group history by agent
    history_by_agent = {}
    for entry in history:
        aid = entry['agent_id']
        if aid not in history_by_agent:
            history_by_agent[aid] = []
        history_by_agent[aid].append({
            "weight": entry['weight'],
            "run_number": entry['run_number'],
            "timestamp": entry['timestamp']
        })
    
    return {
        "current": summary,
        "history": history_by_agent
    }
