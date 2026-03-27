from datetime import datetime
from typing import Dict, Optional
from database import get_weights, get_recent_rejection_count


def get_time_period() -> str:
    """Get time period based on current hour"""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


def get_historical_preference() -> Optional[str]:
    """Get the agent with highest RL weight"""
    weights = get_weights()
    if not weights:
        return None
    
    max_agent = max(weights.items(), key=lambda x: x[1].get('weight', 0) if isinstance(x[1], dict) else 0)
    return max_agent[1].get('name') if isinstance(max_agent[1], dict) else None


def get_context_signals(input_data: str, classification: str) -> Dict:
    """
    Collect all context signals for decision making
    """
    return {
        "urgency": classification,
        "time_period": get_time_period(),
        "input_length": len(input_data.split()),
        "historical_preference": get_historical_preference(),
        "recent_rejections": get_recent_rejection_count(5)
    }
