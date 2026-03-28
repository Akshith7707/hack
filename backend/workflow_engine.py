"""
FlowForge Workflow Engine
DAG-based workflow execution with parallel node support
"""
import asyncio
import uuid
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from database import (
    get_agents_by_type, get_weights, save_run, save_log_entry,
    create_execution, update_execution, save_execution_log,
    get_workflow
)
from llm_service import call_llm, call_llm_with_retry, LLMTimeoutError
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


class DAGEngine:
    """Execute JSON-defined workflows as DAGs"""
    
    def __init__(self):
        self.context: Dict[str, Any] = {}
        self.execution_id: Optional[str] = None
        self.logs: List[Dict] = []
        self.workflow_id: Optional[str] = None
    
    async def execute_workflow(self, workflow_id: str, trigger_data: Dict = None) -> Dict:
        """
        Execute a stored workflow by ID
        """
        workflow = get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found")
        
        return await self.execute_dag(
            nodes=workflow.get('nodes', []),
            edges=workflow.get('edges', []),
            trigger_data=trigger_data or {},
            workflow_id=workflow_id
        )
    
    def _normalize_trigger_data(self, trigger_data: Dict) -> Dict:
        """
        Normalize trigger data to ensure consistent format.
        Always ensures there's an 'input' field.
        """
        if not trigger_data:
            return {"input": ""}
        
        # If trigger_data already has 'input', use it
        if 'input' in trigger_data:
            return trigger_data
        
        # If trigger_data has other content, serialize it as input
        if trigger_data:
            # Try common field names
            for key in ['text', 'message', 'body', 'content', 'data']:
                if key in trigger_data:
                    return {"input": str(trigger_data[key]), **trigger_data}
            
            # Otherwise, use the whole dict as context and create a summary as input
            return {"input": json.dumps(trigger_data), **trigger_data}
        
        return {"input": ""}
    
    async def execute_dag(self, nodes: List[Dict], edges: List[Dict], trigger_data: Dict = None, workflow_id: str = None) -> Dict:
        """
        Execute a DAG with topological ordering and parallel support
        """
        self.execution_id = str(uuid.uuid4())
        
        # Normalize trigger data - ensure it always has an 'input' key
        td = trigger_data or {}
        if isinstance(td, str):
            td = {"input": td}
        elif isinstance(td, dict) and 'input' not in td:
            # If no 'input' key, serialize the whole thing as input
            td['input'] = td.get('text', td.get('data', json.dumps(td) if td else 'No input provided'))
        
        self.context = {"trigger": td}
        self.logs = []
        
        # Create execution record with workflow_id
        create_execution(
            execution_id=self.execution_id,
            workflow_id=workflow_id,
            trigger_data=json.dumps(td) if td else None
        )
        
        # Build adjacency list and in-degree count
        adj = {n['id']: [] for n in nodes}
        in_degree = {n['id']: 0 for n in nodes}
        node_map = {n['id']: n for n in nodes}
        
        for edge in edges:
            adj[edge['from']].append(edge['to'])
            in_degree[edge['to']] += 1
        
        # Topological sort with level grouping (for parallel execution)
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        executed = set()
        final_result = {}
        
        while queue:
            # All nodes in current queue can run in parallel
            tasks = []
            current_batch = list(queue)
            queue = []
            
            for node_id in current_batch:
                node = node_map[node_id]
                tasks.append(self._execute_node(node))
            
            # Run batch in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, node_id in enumerate(current_batch):
                result = results[i]
                
                if isinstance(result, Exception):
                    # Node failed
                    self.context[node_id] = {"error": str(result)}
                    update_execution(self.execution_id, status="failed", 
                                     completed_at=datetime.utcnow().isoformat())
                    return {"status": "error", "error": str(result), "node_id": node_id}
                
                self.context[node_id] = result
                executed.add(node_id)
                final_result = result  # Keep track of last result
                
                # Decrement in-degree for downstream nodes
                for next_id in adj[node_id]:
                    in_degree[next_id] -= 1
                    if in_degree[next_id] == 0:
                        queue.append(next_id)
        
        # Update execution status
        update_execution(
            self.execution_id,
            status="completed",
            results=self.context,
            selected_agent_id=final_result.get('selected_agent_id'),
            selected_agent_name=final_result.get('selected_agent_name'),
            final_output=final_result.get('final_output') or final_result.get('output'),
            completed_at=datetime.utcnow().isoformat()
        )
        
        return {
            "execution_id": self.execution_id,
            "status": "completed",
            "results": self.context,
            "final": final_result,
            "logs": self.logs
        }
    
    async def _execute_node(self, node: Dict, retry: int = 0) -> Dict:
        """Execute a single node with retry support"""
        node_type = node.get('type', 'unknown')
        node_id = node['id']
        config = node.get('config', {})
        
        start_time = time.time()
        
        try:
            if node_type == 'trigger':
                result = await self._execute_trigger(node)
            elif node_type == 'agent':
                result = await self._execute_agent(node)
            elif node_type == 'competition':
                result = await self._execute_competition(node)
            elif node_type == 'condition':
                result = await self._execute_condition(node)
            elif node_type == 'action':
                result = await self._execute_action(node)
            else:
                result = {"output": f"Unknown node type: {node_type}"}
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Save execution log
            save_execution_log(
                execution_id=self.execution_id,
                node_id=node_id,
                agent_id=node.get('agent_id', node_id),
                agent_name=node.get('name', node_id),
                agent_type=node_type,
                input_text=json.dumps(config)[:500],
                output_text=json.dumps(result)[:1000],
                score=result.get('score'),
                duration_ms=duration_ms,
                step_order=len(self.logs)
            )
            
            self.logs.append({
                "node_id": node_id,
                "type": node_type,
                "duration_ms": duration_ms,
                "result": result
            })
            
            return result
            
        except LLMTimeoutError as e:
            if retry < 2:  # Max 2 retries
                return await self._execute_node(node, retry + 1)
            raise e
        except Exception as e:
            if retry < 1:  # 1 retry for general errors
                await asyncio.sleep(1)  # Brief delay before retry
                return await self._execute_node(node, retry + 1)
            raise e
    
    async def _execute_trigger(self, node: Dict) -> Dict:
        """Execute trigger node - returns trigger data with guaranteed 'input' key"""
        data = self.context.get('trigger', {})
        # Ensure 'input' key exists for downstream nodes
        if 'input' not in data:
            data['input'] = json.dumps(data) if data else 'No input provided'
        return data
    
    async def _execute_agent(self, node: Dict) -> Dict:
        """Execute single agent node"""
        agent_type = node.get('agent_type', node.get('config', {}).get('agent_type', 'worker'))
        agents = get_agents_by_type(agent_type)
        
        if not agents:
            return {"error": f"No agents of type '{agent_type}' found", "output": f"No agents of type '{agent_type}' found"}
        
        agent = agents[0]
        # Try multiple input resolution paths
        input_ref = node.get('input', node.get('config', {}).get('input', '$trigger.input'))
        input_text = self._resolve_variables(input_ref)
        
        # Fallback: if resolution returned empty, use trigger input directly
        if not input_text or input_text == input_ref:
            trigger = self.context.get('trigger', {})
            input_text = trigger.get('input', json.dumps(trigger))
        
        # Build prompt based on agent type
        if agent_type == 'classifier':
            prompt = build_analyzer_prompt()
        else:
            prompt = build_executor_prompt(
                style=agent.get('style', 'balanced'),
                role=agent.get('role', 'Assistant'),
                goal=agent.get('goal', 'Help the user')
            )
        
        output = await call_llm_with_retry(prompt, input_text)
        
        return {
            "agent_id": agent['id'],
            "agent_name": agent['name'],
            "output": output
        }
    
    async def _execute_competition(self, node: Dict) -> Dict:
        """Execute competition node - multiple agents compete, supervisor scores, decision picks"""
        # Resolve input from config or direct attribute
        input_ref = node.get('input', node.get('config', {}).get('input', '$trigger.input'))
        input_text = self._resolve_variables(input_ref)
        
        # Fallback: if resolution failed, look through context for usable input
        if not input_text or input_text == input_ref:
            for key in ['classify', 'analyzer', 'trigger']:
                ctx = self.context.get(key, {})
                if isinstance(ctx, dict):
                    val = ctx.get('output', ctx.get('input', ''))
                    if val and isinstance(val, str) and len(val) > 5:
                        input_text = val
                        break
            if not input_text:
                trigger = self.context.get('trigger', {})
                input_text = trigger.get('input', json.dumps(trigger))
        
        # Get classification if available
        classify_result = self.context.get('classify', {})
        classification = classify_result.get('output', '') if isinstance(classify_result, dict) else ''
        
        print(f"[COMPETITION] Input: '{input_text[:100]}...'" if len(input_text) > 100 else f"[COMPETITION] Input: '{input_text}'")
        print(f"[COMPETITION] Classification: {classification}")
        
        # Get all worker agents
        workers = get_agents_by_type("worker")
        if not workers:
            return {"error": "No worker agents found", "output": "No workers available"}
        
        print(f"[COMPETITION] Running {len(workers)} workers in parallel")
        
        # Run all workers in parallel
        async def run_worker(agent: Dict) -> Dict:
            try:
                prompt = build_executor_prompt(
                    style=agent.get('style', 'balanced'),
                    role=agent.get('role', 'Assistant'),
                    goal=agent.get('goal', 'Help the user')
                )
                context_input = f"Category: {classification}\n\nInput:\n{input_text}" if classification else input_text
                output = await call_llm_with_retry(prompt, context_input)
                print(f"[WORKER] {agent['name']} completed")
                return {
                    "agent_id": agent['id'],
                    "agent_name": agent['name'],
                    "style": agent.get('style', 'balanced'),
                    "output": output
                }
            except Exception as e:
                print(f"[WORKER] {agent['name']} error: {e}")
                return {
                    "agent_id": agent['id'],
                    "agent_name": agent['name'],
                    "style": agent.get('style', 'balanced'),
                    "output": f"Error: {str(e)}",
                    "error": True
                }
        
        outputs = await asyncio.gather(*[run_worker(a) for a in workers])
        outputs = [o for o in outputs if not o.get('error')]  # Filter out errors
        
        if not outputs:
            return {"error": "All workers failed", "output": ""}
        
        print(f"[COMPETITION] {len(outputs)} workers completed successfully")
        
        # Run reviewer to score all outputs
        supervisors = get_agents_by_type("supervisor")
        if supervisors:
            prompt = build_reviewer_prompt()
            review_input = f"ORIGINAL INPUT:\n{input_text}\n\nRESPONSES TO REVIEW:\n"
            for i, out in enumerate(outputs):
                review_input += f"\nRESPONSE_{i+1} ({out['style']}):\n{out['output']}\n"
            
            review_response = await call_llm_with_retry(prompt, review_input)
            scores = self._parse_scores(review_response, len(outputs))
        else:
            scores = {i+1: 70 for i in range(len(outputs))}
        
        # Apply scores to outputs
        for i, out in enumerate(outputs):
            out['score'] = scores.get(i+1, 70)
        
        # Get RL weights and run decision
        weights = get_weights()
        context_signals = get_context_signals(input_text, classification or "GENERAL")
        
        decision_agents = get_agents_by_type("decision")
        if decision_agents:
            prompt = build_decision_prompt()
            decision_input = self._format_decision_input(outputs, scores, weights, context_signals)
            decision_response = await call_llm_with_retry(prompt, decision_input)
            decision = self._parse_decision(decision_response, outputs)
        else:
            # Auto-select highest score
            best_idx = max(scores, key=scores.get)
            best = outputs[best_idx - 1]
            decision = {
                "selected": best['agent_name'],
                "selected_agent_id": best['agent_id'],
                "final": best['output'],
                "reason": "Auto-selected highest score"
            }
        
        return {
            "selected_agent_id": decision.get("selected_agent_id"),
            "selected_agent_name": decision.get("selected"),
            "final_output": decision.get("final"),
            "reason": decision.get("reason"),
            "all_outputs": outputs,
            "scores": scores
        }
    
    async def _execute_condition(self, node: Dict) -> Dict:
        """Execute condition node - evaluates expression and returns branch"""
        expression = node.get('expression', 'true')
        resolved = self._resolve_variables(expression)
        
        # Simple evaluation (avoid full eval() for security)
        result = resolved.lower() in ('true', '1', 'yes') if isinstance(resolved, str) else bool(resolved)
        
        return {"result": result, "branch": "then" if result else "else"}
    
    async def _execute_action(self, node: Dict) -> Dict:
        """Execute action node - calls integration"""
        integration_type = node.get('integration', 'webhook')
        config = node.get('config', {})
        
        # Resolve variables in config
        resolved_config = {}
        for key, value in config.items():
            resolved_config[key] = self._resolve_variables(value) if isinstance(value, str) else value
        
        # Get integration
        integration = get_integration(integration_type)
        if not integration:
            return {"error": f"Integration '{integration_type}' not found"}
        
        # Execute action
        result = await asyncio.to_thread(
            integration.action, 
            resolved_config.get('data', {}), 
            resolved_config
        )
        
        return result
    
    def _resolve_variables(self, template: str) -> str:
        """
        Resolve $node_id.field variables in template
        Examples:
            $trigger.input → context['trigger']['input']
            $analyzer.output → context['analyzer']['output']
        """
        if not template or not isinstance(template, str):
            return str(template) if template else ""
        
        # If template is just a variable reference, extract it fully
        pattern = r'\$(\w+)\.(\w+)'
        
        def replacer(match):
            node_id = match.group(1)
            field = match.group(2)
            
            node_result = self.context.get(node_id, {})
            print(f"[VAR] Resolving ${node_id}.{field} from context keys: {list(self.context.keys())}")
            
            if isinstance(node_result, dict):
                value = node_result.get(field)
                if value is not None:
                    result = str(value) if not isinstance(value, str) else value
                    print(f"[VAR] Resolved ${node_id}.{field} = '{result[:100]}...' " if len(str(result)) > 100 else f"[VAR] Resolved ${node_id}.{field} = '{result}'")
                    return result
                else:
                    # Try nested access if field not found directly
                    print(f"[VAR] Field '{field}' not found in {node_id}, available: {list(node_result.keys())}")
                    # Return empty string if not found, but log it
                    return ""
            elif isinstance(node_result, str):
                # If node_result is a string and field is 'output' or 'input', return the string
                if field in ('output', 'input'):
                    return node_result
            
            print(f"[VAR] Could not resolve ${node_id}.{field}")
            return ""
        
        resolved = re.sub(pattern, replacer, template)
        
        # If the entire template was a single variable that resolved to empty, 
        # and we have the node result as a string, use that
        if not resolved and re.match(r'^\$\w+\.\w+$', template):
            parts = template[1:].split('.')
            node_result = self.context.get(parts[0], {})
            if isinstance(node_result, str):
                return node_result
        
        return resolved
    
    def _parse_scores(self, response: str, count: int) -> Dict[int, int]:
        """Extract scores from reviewer response"""
        scores = {}
        for i in range(1, count + 1):
            # Try SCORE_N: format (scale 1-10, multiply by 10)
            match = re.search(rf'SCORE_{i}:\s*(\d+)', response)
            if match:
                raw_score = int(match.group(1))
                # If score is 1-10, scale to 0-100
                if raw_score <= 10:
                    scores[i] = raw_score * 10
                else:
                    scores[i] = min(100, max(0, raw_score))
            else:
                scores[i] = 70
        return scores
    
    def _parse_decision(self, response: str, outputs: List[Dict]) -> Dict:
        """Parse decision agent response"""
        result = {"selected": "", "final": "", "reason": "", "selected_agent_id": None}
        
        match = re.search(r'SELECTED:\s*(.+?)(?=\n|FINAL:|$)', response, re.IGNORECASE)
        if match:
            result["selected"] = match.group(1).strip()
        
        match = re.search(r'FINAL:\s*(.+?)(?=REASON:|$)', response, re.IGNORECASE | re.DOTALL)
        if match:
            result["final"] = match.group(1).strip()
        
        match = re.search(r'REASON:\s*(.+?)$', response, re.IGNORECASE | re.DOTALL)
        if match:
            result["reason"] = match.group(1).strip()
        
        for out in outputs:
            if (out['agent_name'].lower() in result['selected'].lower() or
                out['style'].lower() in result['selected'].lower()):
                result["selected_agent_id"] = out['agent_id']
                break
        
        if not result["selected_agent_id"] and outputs:
            best = max(outputs, key=lambda x: x.get('score', 0))
            result["selected_agent_id"] = best['agent_id']
        
        return result
    
    def _format_decision_input(self, outputs: List[Dict], scores: Dict, weights: Dict, context: Dict) -> str:
        """Format input for decision agent"""
        lines = ["SCORES AND WEIGHTS:"]
        for i, out in enumerate(outputs):
            agent_weights = weights.get(out['agent_id'], {})
            w = agent_weights.get('weight', 0.33) if isinstance(agent_weights, dict) else 0.33
            lines.append(f"- {out['agent_name']}: {scores.get(i+1, 70)}/100 (weight: {w*100:.1f}%)")
        
        lines.append(f"\nCONTEXT SIGNALS:")
        lines.append(f"- Urgency: {context.get('urgency', 'normal')}")
        lines.append(f"- Time: {context.get('time_period', 'unknown')}")
        
        lines.append("\nRESPONSES:")
        for out in outputs:
            lines.append(f"\n[{out['agent_name']}]:")
            lines.append(out['output'])
        
        return "\n".join(lines)


# DAG engine singleton
dag_engine = DAGEngine()


async def run_dag_workflow(workflow_id: str, trigger_data: Dict = None) -> Dict:
    """Execute a stored workflow"""
    return await dag_engine.execute_workflow(workflow_id, trigger_data)
