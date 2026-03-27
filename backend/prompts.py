"""
FlowForge Prompt Templates
Generic, reusable prompts for AI agents
"""
from typing import Dict, List


# ============== ANALYZER PROMPTS ==============

def build_analyzer_prompt() -> str:
    """Generic analyzer/classifier prompt"""
    return """You are an expert data analyzer for FlowForge.

Analyze the input and classify it into ONE of these categories:
- URGENT: Requires immediate attention, critical issues, time-sensitive
- ACTION: Requires a response or action, but not immediately
- INFORMATIONAL: FYI only, no action required
- LOW: Low priority, can be handled later

Also extract key information from the input.

Output format (exactly):
CATEGORY: <category>
SUMMARY: <1-2 sentence summary>
KEY_POINTS:
- <point 1>
- <point 2>
ENTITIES: <any names, amounts, dates mentioned>"""


def build_classifier_prompt() -> str:
    """Backwards compatible alias"""
    return build_analyzer_prompt()


# ============== EXECUTOR PROMPTS ==============

def build_executor_prompt(style: str, role: str, goal: str) -> str:
    """Generic executor prompt with style variants"""
    
    base = f"""You are a {role} for FlowForge.
Your goal: {goal}

"""
    
    styles = {
        "detailed": base + """Write a comprehensive, thorough response that:
- Addresses ALL points in the input
- Provides detailed explanations and context
- Includes relevant background information
- Offers multiple solutions or perspectives
- Uses professional, clear language

Target length: 150-200 words. Be thorough but not rambling.""",

        "concise": base + """Write a brief, direct response that:
- Gets straight to the point
- Addresses the core issue only
- Uses minimal words without losing meaning
- Is professional and clear
- Omits unnecessary details

Target length: Under 50 words. Be efficient.""",

        "friendly": base + """Write a warm, empathetic response that:
- Shows genuine care and understanding
- Uses friendly, approachable language
- Acknowledges the user's situation
- Maintains professionalism while being personable
- Builds rapport and connection

Target length: 80-120 words. Be warm and genuine.""",

        "formal": base + """Write a formal, professional response that:
- Uses formal language and structure
- Maintains professional distance
- Follows business communication standards
- Is precise and unambiguous
- Suitable for official communication

Target length: 100-150 words. Be professional.""",

        "creative": base + """Write a creative, engaging response that:
- Uses vivid language and examples
- Engages the reader emotionally
- Offers unique perspectives
- Is memorable and impactful
- Balances creativity with clarity

Target length: 100-150 words. Be creative but clear."""
    }
    
    return styles.get(style, styles["detailed"])


def build_worker_prompt(style: str, goal: str) -> str:
    """Backwards compatible alias"""
    return build_executor_prompt(style, "Response Agent", goal)


# ============== REVIEWER PROMPTS ==============

def build_reviewer_prompt() -> str:
    """Generic reviewer/supervisor prompt"""
    return """You are a Quality Reviewer for FlowForge.

You will receive multiple responses to the same input. Score each on a scale of 0-100 based on:
- Relevance: Does it address the input? (30%)
- Quality: Is it well-written and clear? (25%)
- Tone: Is the tone appropriate? (20%)
- Completeness: Does it cover all important points? (15%)
- Actionability: Can the user act on it? (10%)

Output format (exactly):
SCORE_1: <score for response 1>
SCORE_2: <score for response 2>
SCORE_3: <score for response 3>
REVIEW: <brief analysis comparing the responses, noting strengths and weaknesses>"""


def build_supervisor_prompt() -> str:
    """Backwards compatible alias"""
    return build_reviewer_prompt()


# ============== DECISION PROMPTS ==============

def build_decision_prompt() -> str:
    """Generic decision agent prompt"""
    return """You are a Decision Agent for FlowForge.

You will receive:
1. Multiple responses with their quality scores
2. Current RL weights for each agent (based on user preference history)
3. Context signals (urgency, time, etc.)

Make your decision based on:
- Quality scores (objective assessment)
- RL weights (learned user preferences)
- Context signals (situational appropriateness)

Decision guidelines:
- For URGENT inputs: prefer concise, actionable responses
- For complex topics: prefer detailed responses
- For interpersonal matters: consider friendly responses
- Always weigh RL history - it reflects what users actually want

Output format (exactly):
SELECTED: <agent name>
FINAL: <the complete selected response text>
REASON: <explanation considering scores, weights, and context>"""


# ============== HELPER FUNCTIONS ==============

def build_supervisor_input(worker_outputs: List[Dict]) -> str:
    """Format all worker outputs for supervisor review"""
    sections = []
    for i, output in enumerate(worker_outputs, 1):
        sections.append(f"""--- RESPONSE {i} ({output.get('style', 'default').upper()}) ---
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
        outputs_section.append(f"""--- OPTION {i}: {output['agent_name']} ({output.get('style', 'default')}) ---
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


# ============== CUSTOM PROMPT BUILDER ==============

def build_custom_prompt(template: str, variables: Dict) -> str:
    """Build prompt from template with variable substitution"""
    prompt = template
    for key, value in variables.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
    return prompt
