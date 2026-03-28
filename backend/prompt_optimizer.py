"""
FlexCode Prompt Optimizer
Analyzes feedback patterns and suggests prompt improvements
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from database import (
    get_connection, get_agent_by_id, get_weights,
    save_prompt_suggestion, get_agent_feedback_history
)
from prompts import build_executor_prompt


# Thresholds for triggering optimization
OPTIMIZATION_THRESHOLD = 0.4  # If accept rate drops below 40%
MIN_FEEDBACK_COUNT = 10       # Need at least 10 feedback entries


def get_agent_performance_stats(agent_id: str) -> Dict:
    """Get comprehensive performance statistics for an agent"""
    conn = get_connection()
    cursor = conn.cursor()

    # Get weight data
    cursor.execute("""
        SELECT weight, times_selected, times_accepted, times_rejected, total_runs, avg_score
        FROM agent_weights WHERE agent_id = ?
    """, (agent_id,))
    weight_row = cursor.fetchone()

    # Get recent feedback with context
    cursor.execute("""
        SELECT * FROM feedback_log
        WHERE agent_id = ?
        ORDER BY timestamp DESC
        LIMIT 20
    """, (agent_id,))
    feedback_rows = cursor.fetchall()

    # Get execution logs for output analysis
    cursor.execute("""
        SELECT el.output_text, el.score, f.action
        FROM execution_logs el
        LEFT JOIN feedback_log f ON el.execution_id = f.execution_id
        WHERE el.agent_id = ? AND el.output_text IS NOT NULL
        ORDER BY el.timestamp DESC
        LIMIT 30
    """, (agent_id,))
    output_rows = cursor.fetchall()

    conn.close()

    # Compute stats
    if weight_row:
        selected = weight_row['times_selected'] or 1
        accepted = weight_row['times_accepted'] or 0
        rejected = weight_row['times_rejected'] or 0
        accept_rate = accepted / selected if selected > 0 else 0
    else:
        accept_rate = 0
        selected = 0
        accepted = 0
        rejected = 0

    # Separate accepted vs rejected outputs
    accepted_outputs = [dict(r) for r in output_rows if r['action'] == 'accept']
    rejected_outputs = [dict(r) for r in output_rows if r['action'] == 'reject']

    return {
        "agent_id": agent_id,
        "weight": weight_row['weight'] if weight_row else 0.33,
        "times_selected": selected,
        "times_accepted": accepted,
        "times_rejected": rejected,
        "accept_rate": accept_rate,
        "avg_score": weight_row['avg_score'] if weight_row else 0,
        "recent_feedback": [dict(r) for r in feedback_rows],
        "accepted_outputs": accepted_outputs[:10],
        "rejected_outputs": rejected_outputs[:10],
        "needs_optimization": accept_rate < OPTIMIZATION_THRESHOLD and selected >= MIN_FEEDBACK_COUNT
    }


def analyze_output_patterns(accepted_outputs: List[Dict], rejected_outputs: List[Dict]) -> Dict:
    """Analyze patterns in accepted vs rejected outputs"""
    if not accepted_outputs and not rejected_outputs:
        return {"analysis": "Insufficient data for analysis"}

    # Basic pattern analysis
    accepted_lengths = [len(o.get('output_text', '')) for o in accepted_outputs if o.get('output_text')]
    rejected_lengths = [len(o.get('output_text', '')) for o in rejected_outputs if o.get('output_text')]

    avg_accepted_length = sum(accepted_lengths) / len(accepted_lengths) if accepted_lengths else 0
    avg_rejected_length = sum(rejected_lengths) / len(rejected_lengths) if rejected_lengths else 0

    accepted_scores = [o.get('score', 0) for o in accepted_outputs if o.get('score')]
    rejected_scores = [o.get('score', 0) for o in rejected_outputs if o.get('score')]

    avg_accepted_score = sum(accepted_scores) / len(accepted_scores) if accepted_scores else 0
    avg_rejected_score = sum(rejected_scores) / len(rejected_scores) if rejected_scores else 0

    return {
        "accepted_count": len(accepted_outputs),
        "rejected_count": len(rejected_outputs),
        "avg_accepted_length": avg_accepted_length,
        "avg_rejected_length": avg_rejected_length,
        "avg_accepted_score": avg_accepted_score,
        "avg_rejected_score": avg_rejected_score,
        "length_preference": "longer" if avg_accepted_length > avg_rejected_length else "shorter"
    }


def generate_prompt_improvement(agent_id: str, llm_service=None) -> Optional[Dict]:
    """Generate a prompt improvement suggestion for an agent"""
    agent = get_agent_by_id(agent_id)
    if not agent:
        return None

    stats = get_agent_performance_stats(agent_id)

    if not stats['needs_optimization']:
        return None

    # Get current prompt
    style = agent.get('style', 'detailed')
    role = agent.get('role', 'Executor')
    goal = agent.get('goal', 'Help the user')
    current_prompt = agent.get('custom_prompt') or build_executor_prompt(style, role, goal)

    # Analyze output patterns
    pattern_analysis = analyze_output_patterns(
        stats['accepted_outputs'],
        stats['rejected_outputs']
    )

    # Generate suggestion based on analysis
    reasoning_parts = []
    prompt_additions = []

    if pattern_analysis.get('length_preference') == 'longer':
        reasoning_parts.append("Accepted outputs tend to be longer and more detailed")
        prompt_additions.append("Provide comprehensive, detailed responses")
    elif pattern_analysis.get('length_preference') == 'shorter':
        reasoning_parts.append("Accepted outputs tend to be shorter and more concise")
        prompt_additions.append("Keep responses concise and focused")

    if pattern_analysis.get('avg_accepted_score', 0) > 7:
        reasoning_parts.append(f"High-scoring outputs (avg {pattern_analysis['avg_accepted_score']:.1f}) are preferred")
        prompt_additions.append("Focus on quality and accuracy")

    # Build improved prompt
    improved_prompt = current_prompt
    if prompt_additions:
        improvement_section = "\n\n[Style Guidelines based on feedback]\n" + "\n".join(f"- {p}" for p in prompt_additions)
        improved_prompt = current_prompt + improvement_section

    reasoning = "; ".join(reasoning_parts) if reasoning_parts else "General optimization based on feedback patterns"

    # Save suggestion
    suggestion_id = str(uuid.uuid4())
    save_prompt_suggestion(
        suggestion_id=suggestion_id,
        agent_id=agent_id,
        current_prompt=current_prompt,
        suggested_prompt=improved_prompt,
        reasoning=reasoning
    )

    return {
        "suggestion_id": suggestion_id,
        "agent_id": agent_id,
        "current_prompt": current_prompt,
        "suggested_prompt": improved_prompt,
        "reasoning": reasoning,
        "performance_stats": {
            "accept_rate": stats['accept_rate'],
            "times_selected": stats['times_selected']
        },
        "pattern_analysis": pattern_analysis
    }


def auto_optimize_underperforming_agents() -> List[Dict]:
    """
    Background task to identify and generate suggestions for
    underperforming agents. Call periodically.
    """
    from database import get_agents_by_type, get_pending_suggestions

    suggestions_generated = []

    # Get all worker agents
    workers = get_agents_by_type('worker')

    for agent in workers:
        agent_id = agent['id']
        stats = get_agent_performance_stats(agent_id)

        if stats['needs_optimization']:
            # Check if we already have a pending suggestion
            pending = get_pending_suggestions(agent_id)
            if not pending:
                suggestion = generate_prompt_improvement(agent_id)
                if suggestion and 'error' not in suggestion:
                    suggestions_generated.append(suggestion)

    return suggestions_generated
