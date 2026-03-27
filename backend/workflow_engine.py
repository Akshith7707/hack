"""
FlowForge Workflow Engine
DAG-based workflow execution with parallel node support
"""
import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from database import get_agents_by_type, get_weights, save_run, save_log_entry
from llm_service import call_llm
from prompts import (
    build_analyzer_prompt, build_executor_prompt,
    build_reviewer_prompt, build_decision_prompt
)
from context_engine import get_context_signals
from integrations import get_integration


@dataclass
class NodeResult:
    """Result of a node execution"""
    node_id: str
    output: Any
    score: Optional[float] = None
    duration_ms: int = 0
    status: str = "success"
    error: Optional[str] = None


@dataclass
class WorkflowContext:
    """Shared context during workflow execution"""
    run_id: str
    trigger_data: Dict
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    logs: List[Dict] = field(default_factory=list)
    step: int = 0


# Store for SSE streaming
run_logs: Dict[str, List[Dict]] = {}


def get_run_log_stream(run_id: str) -> List[Dict]:
    """Get logs for SSE streaming"""
    return run_logs.get(run_id, [])


class WorkflowEngine:
    """Execute workflows as directed acyclic graphs (DAGs)"""
    
    def __init__(self):
        self.context: Optional[WorkflowContext] = None
    
    async def execute(self, input_data: str, workflow_config: Optional[Dict] = None) -> Dict:
        """
        Execute workflow with given input
        
        Default workflow (backwards compatible):
        Analyzer → 3 Executors (parallel) → Reviewer → Decision → Action
        """
        run_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        self.context = WorkflowContext(
            run_id=run_id,
            trigger_data={"input": input_data}
        )
        run_logs[run_id] = []
        
        try:
            # Step 1: Analyzer (classification)
            classification = await self._run_analyzer(input_data)
            
            # Step 2: Executors (parallel workers)
            executor_outputs = await self._run_executors(input_data, classification)
            
            # Step 3: Reviewer (scoring)
            scores = await self._run_reviewer(input_data, executor_outputs)
            
            # Apply scores to outputs
            for i, output in enumerate(executor_outputs):
                output['score'] = scores.get(i + 1, 70)
            
            # Step 4: Context signals
            context_signals = get_context_signals(input_data, classification)
            
            # Step 5: Get RL weights
            weights = get_weights()
            
            # Step 6: Decision
            decision = await self._run_decision(
                input_data, executor_outputs, scores, weights, context_signals
            )
            
            # Build result
            result = {
                "run_id": run_id,
                "classification": classification,
                "worker_outputs": executor_outputs,
                "supervisor_review": decision.get("review", ""),
                "decision_output": decision.get("raw", ""),
                "selected_agent": decision.get("selected_agent_id"),
                "selected_agent_name": decision.get("selected"),
                "final_output": decision.get("final"),
                "decision_reason": decision.get("reason"),
                "context_signals": context_signals,
                "weights": {k: v for k, v in weights.items()},
                "logs": run_logs.get(run_id, [])
            }
            
            # Save to database
            self._save_run(result, input_data, created_at)
            
            return result
            
        except Exception as e:
            raise Exception(f"Workflow execution failed: {str(e)}")
    
    async def _run_analyzer(self, input_data: str) -> str:
        """Run analyzer agent (classification)"""
        agents = get_agents_by_type("classifier")
        if not agents:
            raise ValueError("No analyzer/classifier agent found")
        
        agent = agents[0]
        prompt = build_analyzer_prompt()
        response = await call_llm(prompt, input_data)
        
        # Parse classification
        classification = self._parse_classification(response)
        
        self._add_log(agent, input_data, response, "analyzer")
        return classification
    
    async def _run_executors(self, input_data: str, classification: str) -> List[Dict]:
        """Run executor agents in parallel"""
        agents = get_agents_by_type("worker")
        if len(agents) < 1:
            raise ValueError("No executor/worker agents found")
        
        async def run_single(agent: Dict) -> Dict:
            prompt = build_executor_prompt(
                style=agent.get('style', 'balanced'),
                role=agent.get('role', 'Assistant'),
                goal=agent.get('goal', 'Help the user')
            )
            context_input = f"Category: {classification}\n\nInput:\n{input_data}"
            output = await call_llm(prompt, context_input)
            
            self._add_log(agent, input_data, output, "executor")
            
            return {
                "agent_id": agent['id'],
                "agent_name": agent['name'],
                "style": agent.get('style', 'balanced'),
                "output": output
            }
        
        # Execute all in parallel
        results = await asyncio.gather(*[run_single(a) for a in agents])
        return list(results)
    
    async def _run_reviewer(self, input_data: str, outputs: List[Dict]) -> Dict[int, int]:
        """Run reviewer agent to score outputs"""
        agents = get_agents_by_type("supervisor")
        if not agents:
            # Return default scores if no reviewer
            return {i+1: 70 for i in range(len(outputs))}
        
        agent = agents[0]
        prompt = build_reviewer_prompt()
        
        # Format outputs for review
        review_input = f"ORIGINAL INPUT:\n{input_data}\n\nRESPONSES TO REVIEW:\n"
        for i, out in enumerate(outputs):
            review_input += f"\nRESPONSE_{i+1} ({out['style']}):\n{out['output']}\n"
        
        response = await call_llm(prompt, review_input)
        scores = self._parse_scores(response, len(outputs))
        
        self._add_log(agent, review_input[:500], response, "reviewer")
        
        return scores
    
    async def _run_decision(
        self, 
        input_data: str,
        outputs: List[Dict],
        scores: Dict[int, int],
        weights: Dict,
        context: Dict
    ) -> Dict:
        """Run decision agent to select best output"""
        agents = get_agents_by_type("decision")
        if not agents:
            # Auto-select highest scored
            best_idx = max(scores, key=scores.get)
            best = outputs[best_idx - 1]
            return {
                "selected": best['agent_name'],
                "selected_agent_id": best['agent_id'],
                "final": best['output'],
                "reason": "Auto-selected highest score"
            }
        
        agent = agents[0]
        prompt = build_decision_prompt()
        
        # Format decision input
        decision_input = self._format_decision_input(outputs, scores, weights, context)
        response = await call_llm(prompt, decision_input)
        
        result = self._parse_decision(response, outputs)
        result["raw"] = response
        
        self._add_log(agent, decision_input[:500], response, "decision")
        
        return result
    
    def _add_log(self, agent: Dict, input_text: str, output_text: str, node_type: str):
        """Add log entry"""
        self.context.step += 1
        
        log_entry = {
            "agent_id": agent['id'],
            "agent_name": agent['name'],
            "agent_type": node_type,
            "input_preview": input_text[:100] + "..." if len(input_text) > 100 else input_text,
            "output_preview": output_text[:200] + "..." if len(output_text) > 200 else output_text,
            "output_full": output_text,
            "step_order": self.context.step,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        run_logs[self.context.run_id].append(log_entry)
        self.context.logs.append(log_entry)
        
        # Save to database
        save_log_entry(
            self.context.run_id, agent['id'], agent['name'], node_type,
            input_text, output_text, self.context.step
        )
    
    def _parse_classification(self, response: str) -> str:
        """Extract category from analyzer response"""
        import re
        match = re.search(r'CATEGORY:\s*(\w+)', response, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return "GENERAL"
    
    def _parse_scores(self, response: str, count: int) -> Dict[int, int]:
        """Extract scores from reviewer response"""
        import re
        scores = {}
        for i in range(1, count + 1):
            match = re.search(rf'SCORE_{i}:\s*(\d+)', response)
            if match:
                scores[i] = min(100, max(0, int(match.group(1))))
            else:
                scores[i] = 70
        return scores
    
    def _parse_decision(self, response: str, outputs: List[Dict]) -> Dict:
        """Parse decision agent response"""
        import re
        
        result = {"selected": "", "final": "", "reason": "", "selected_agent_id": None}
        
        # Extract SELECTED
        match = re.search(r'SELECTED:\s*(.+?)(?=\n|FINAL:|$)', response, re.IGNORECASE)
        if match:
            result["selected"] = match.group(1).strip()
        
        # Extract FINAL
        match = re.search(r'FINAL:\s*(.+?)(?=REASON:|$)', response, re.IGNORECASE | re.DOTALL)
        if match:
            result["final"] = match.group(1).strip()
        
        # Extract REASON
        match = re.search(r'REASON:\s*(.+?)$', response, re.IGNORECASE | re.DOTALL)
        if match:
            result["reason"] = match.group(1).strip()
        
        # Find matching agent ID
        for out in outputs:
            if (out['agent_name'].lower() in result['selected'].lower() or
                out['style'].lower() in result['selected'].lower()):
                result["selected_agent_id"] = out['agent_id']
                break
        
        # Fallback to highest score
        if not result["selected_agent_id"] and outputs:
            best = max(outputs, key=lambda x: x.get('score', 0))
            result["selected_agent_id"] = best['agent_id']
        
        return result
    
    def _format_decision_input(
        self, outputs: List[Dict], scores: Dict, weights: Dict, context: Dict
    ) -> str:
        """Format input for decision agent"""
        lines = ["SCORES AND WEIGHTS:"]
        for i, out in enumerate(outputs):
            agent_weights = weights.get(out['agent_id'], {})
            w = agent_weights.get('weight', 0.33) if isinstance(agent_weights, dict) else 0.33
            lines.append(f"- {out['agent_name']}: {scores.get(i+1, 70)}/100 (weight: {w*100:.1f}%)")
        
        lines.append(f"\nCONTEXT SIGNALS:")
        lines.append(f"- Urgency: {context.get('urgency', 'normal')}")
        lines.append(f"- Time: {context.get('time_period', 'unknown')}")
        if context.get('historical_preference'):
            lines.append(f"- User preference: {context['historical_preference']}")
        
        lines.append("\nRESPONSES:")
        for out in outputs:
            lines.append(f"\n[{out['agent_name']}]:")
            lines.append(out['output'])
        
        return "\n".join(lines)
    
    def _save_run(self, result: Dict, input_data: str, created_at: str):
        """Save workflow run to database"""
        run_data = {
            "id": result["run_id"],
            "input_data": input_data,
            "classification": result.get("classification"),
            "worker_outputs": result.get("worker_outputs", []),
            "supervisor_review": result.get("supervisor_review"),
            "decision_output": result.get("decision_output"),
            "selected_agent": result.get("selected_agent"),
            "final_output": result.get("final_output"),
            "context_signals": result.get("context_signals", {}),
            "created_at": created_at
        }
        save_run(run_data)


# Singleton instance
engine = WorkflowEngine()


async def run_workflow(input_data: str) -> Dict:
    """Execute workflow (backwards compatible function)"""
    return await engine.execute(input_data)
