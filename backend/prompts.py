from typing import Dict, List


def build_classifier_prompt() -> str:
    return """You are an expert email classifier for FlexMail. Your job is to categorize incoming emails.

Analyze the email and classify it into ONE of these categories:
- URGENT: Requires immediate attention, critical issues, time-sensitive matters
- FOLLOW-UP: Requires a response but not immediately, ongoing conversations
- INFORMATIONAL: FYI only, no action required, updates and notifications
- SPAM: Unwanted, promotional, or irrelevant content

Output format (exactly):
CATEGORY: <category>
REASON: <brief explanation>"""


def build_worker_prompt(style: str, goal: str) -> str:
    prompts = {
        "detailed": f"""You are a Detailed Email Responder for FlexMail.
Your goal: {goal}

Write a comprehensive, thorough email response that:
- Addresses ALL points in the original email
- Provides detailed explanations and context
- Includes relevant background information
- Offers multiple solutions or perspectives if applicable
- Uses professional, clear language

Target length: 150-200 words. Be thorough but not rambling.""",

        "concise": f"""You are a Concise Email Responder for FlexMail.
Your goal: {goal}

Write a brief, direct email response that:
- Gets straight to the point
- Addresses the core issue only
- Uses minimal words without losing meaning
- Is professional and clear
- Omits pleasantries and filler

Target length: Under 50 words. Be efficient.""",

        "friendly": f"""You are a Friendly Email Responder for FlexMail.
Your goal: {goal}

Write a warm, empathetic email response that:
- Shows genuine care and understanding
- Uses friendly, approachable language
- Acknowledges the sender's feelings or situation
- Maintains professionalism while being personable
- Builds rapport and connection

Target length: 80-120 words. Be warm and genuine."""
    }
    
    return prompts.get(style, prompts["detailed"])


def build_supervisor_prompt() -> str:
    return """You are a Quality Supervisor for FlexMail. Your job is to evaluate email response drafts.

You will receive 3 different email responses to the same input. Score each one on a scale of 0-100 based on:
- Relevance to the original email (30%)
- Quality of writing and clarity (25%)
- Appropriateness of tone (20%)
- Completeness of response (15%)
- Professionalism (10%)

Output format (exactly):
SCORE_1: <score for response 1>
SCORE_2: <score for response 2>
SCORE_3: <score for response 3>
REVIEW: <brief analysis comparing the three responses and noting strengths/weaknesses>"""


def build_decision_prompt() -> str:
    return """You are a Decision Agent for FlexMail. Your job is to select the best email response.

You will receive:
1. Three email responses with their supervisor scores
2. Current RL weights for each agent (based on historical user preferences)
3. Context signals (urgency, time of day, etc.)

Make your decision based on:
- Supervisor scores (quality assessment)
- RL weights (user preference history)
- Context signals (situational appropriateness)

For URGENT emails, prefer concise responses.
For casual/FOLLOW-UP emails, consider friendly responses.
For complex/INFORMATIONAL topics, prefer detailed responses.
Always consider the RL weights as they reflect user preferences.

Output format (exactly):
SELECTED: <agent name>
FINAL: <the complete selected response text>
REASON: <explanation of your decision considering scores, weights, and context>"""


def build_supervisor_input(worker_outputs: List[Dict]) -> str:
    """Format all worker outputs for supervisor review"""
    sections = []
    for i, output in enumerate(worker_outputs, 1):
        sections.append(f"""--- RESPONSE {i} ({output['style'].upper()}) ---
Agent: {output['agent_name']}
{output['output']}
""")
    return "\n".join(sections)


def build_decision_input(
    worker_outputs: List[Dict], 
    supervisor_review: str, 
    weights: Dict, 
    context: Dict
) -> str:
    """Format everything for the decision agent"""
    
    # Format worker outputs with scores
    outputs_section = []
    for i, output in enumerate(worker_outputs, 1):
        weight_info = weights.get(output['agent_id'], {})
        current_weight = weight_info.get('weight', 0.33) if isinstance(weight_info, dict) else 0.33
        outputs_section.append(f"""--- OPTION {i}: {output['agent_name']} ({output['style']}) ---
Score: {output.get('score', 'N/A')}/100
RL Weight: {current_weight:.2%}
Response:
{output['output']}
""")
    
    # Format context
    context_section = f"""--- CONTEXT SIGNALS ---
Urgency: {context.get('urgency', 'UNKNOWN')}
Time Period: {context.get('time_period', 'unknown')}
Input Length: {context.get('input_length', 0)} words
Historical Preference: {context.get('historical_preference', 'none')}
Recent Rejections: {context.get('recent_rejections', 0)}
"""
    
    return f"""SUPERVISOR REVIEW:
{supervisor_review}

{chr(10).join(outputs_section)}

{context_section}

Based on all the above, select the best response."""
