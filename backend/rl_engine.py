from typing import Dict, List
from database import get_weights, update_weight, increment_selected, increment_accepted, increment_rejected

LEARNING_RATE = 0.05
MIN_WEIGHT = 0.05


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normalize weights to sum to 1.0"""
    total = sum(weights.values())
    if total == 0:
        n = len(weights)
        return {k: 1.0/n for k in weights}
    return {k: v/total for k, v in weights.items()}


def on_accept(selected_agent_id: str):
    """
    Called when user accepts a response.
    Increases the selected agent's weight.
    """
    weights_data = get_weights()
    if not weights_data:
        return
    
    # Get current weights
    current_weights = {
        agent_id: data.get('weight', 0.33) if isinstance(data, dict) else 0.33
        for agent_id, data in weights_data.items()
    }
    
    # Increase selected agent's weight
    if selected_agent_id in current_weights:
        current_weights[selected_agent_id] += LEARNING_RATE
    
    # Normalize
    normalized = normalize_weights(current_weights)
    
    # Update database
    for agent_id, new_weight in normalized.items():
        update_weight(agent_id, new_weight)
    
    # Increment counters
    increment_selected(selected_agent_id)
    increment_accepted(selected_agent_id)


def on_reject(selected_agent_id: str):
    """
    Called when user rejects a response.
    Decreases the selected agent's weight and redistributes to others.
    """
    weights_data = get_weights()
    if not weights_data:
        return
    
    # Get current weights
    current_weights = {
        agent_id: data.get('weight', 0.33) if isinstance(data, dict) else 0.33
        for agent_id, data in weights_data.items()
    }
    
    # Decrease selected agent's weight
    if selected_agent_id in current_weights:
        decrease = LEARNING_RATE
        current_weights[selected_agent_id] = max(
            MIN_WEIGHT, 
            current_weights[selected_agent_id] - decrease
        )
        
        # Redistribute to other agents
        other_agents = [aid for aid in current_weights if aid != selected_agent_id]
        if other_agents:
            bonus = decrease / len(other_agents)
            for aid in other_agents:
                current_weights[aid] += bonus
    
    # Normalize
    normalized = normalize_weights(current_weights)
    
    # Clamp minimum weights
    for agent_id in normalized:
        normalized[agent_id] = max(MIN_WEIGHT, normalized[agent_id])
    
    # Re-normalize after clamping
    normalized = normalize_weights(normalized)
    
    # Update database
    for agent_id, new_weight in normalized.items():
        update_weight(agent_id, new_weight)
    
    # Increment counters
    increment_selected(selected_agent_id)
    increment_rejected(selected_agent_id)


def get_weight_summary() -> List[Dict]:
    """Get formatted weight information for all worker agents"""
    weights_data = get_weights()
    result = []
    
    for agent_id, data in weights_data.items():
        if isinstance(data, dict):
            result.append({
                "agent_id": agent_id,
                "agent_name": data.get('name', 'Unknown'),
                "style": data.get('style', 'unknown'),
                "weight": data.get('weight', 0.33),
                "times_selected": data.get('times_selected', 0),
                "times_accepted": data.get('times_accepted', 0),
                "times_rejected": data.get('times_rejected', 0)
            })
    
    return result
