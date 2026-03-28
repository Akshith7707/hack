"""
FlowForge System Test Suite
Comprehensive tests for backend functionality
"""
import asyncio
import json
from datetime import datetime

# Import all modules to test
from database import (
    init_db, create_agent, get_all_agents, get_agents_by_type,
    get_weights, update_weight, save_feedback
)
from llm_service import call_llm
from workflow_engine import run_workflow
from rl_engine import on_feedback, normalize_weights
from integrations import get_next_mock_email


def test_database():
    """Test database operations"""
    print("🔍 Testing Database...")
    
    # Initialize database
    init_db()
    print("✓ Database initialized")
    
    # Get all agents
    agents = get_all_agents()
    print(f"✓ Found {len(agents)} agents")
    
    # Test weights
    weights = get_weights()
    print(f"✓ Retrieved weights for {len(weights)} agents")
    
    return True


def test_weights_normalization():
    """Test RL weight normalization"""
    print("\n🔍 Testing Weight Normalization...")
    
    test_weights = {
        'agent1': 0.4,
        'agent2': 0.3,
        'agent3': 0.2
    }
    
    normalized = normalize_weights(test_weights)
    total = sum(normalized.values())
    
    assert abs(total - 1.0) < 0.001, f"Weights don't sum to 1.0: {total}"
    print(f"✓ Weights normalized correctly: {normalized}")
    print(f"✓ Sum: {total}")
    
    return True


def test_integrations():
    """Test mock email integration"""
    print("\n🔍 Testing Integrations...")
    
    email = get_next_mock_email()
    if email:
        print(f"✓ Retrieved mock email: {email['subject']}")
        return True
    else:
        print("⚠ No mock emails available")
        return False


async def test_llm_service():
    """Test LLM service"""
    print("\n🔍 Testing LLM Service...")
    
    try:
        response = await call_llm(
            system_prompt="You are a helpful assistant.",
            user_message="Say 'test successful' if you receive this.",
            timeout=10
        )
        print(f"✓ LLM responded: {response[:50]}...")
        return True
    except Exception as e:
        print(f"✗ LLM test failed: {str(e)}")
        return False


async def test_workflow():
    """Test workflow execution"""
    print("\n🔍 Testing Workflow Execution...")
    
    # Check if we have required agents
    classifiers = get_agents_by_type('classifier')
    workers = get_agents_by_type('worker')
    supervisors = get_agents_by_type('supervisor')
    decision = get_agents_by_type('decision')
    
    if not (classifiers and workers and supervisors and decision):
        print("⚠ Not all agent types available. Creating demo agents...")
        from database import create_agent
        import uuid
        
        if not classifiers:
            create_agent(
                str(uuid.uuid4()),
                "Test Classifier",
                "Classifier",
                "Classify inputs",
                "classifier"
            )
        
        if len(workers) < 3:
            styles = ['detailed', 'concise', 'friendly']
            for i, style in enumerate(styles):
                create_agent(
                    str(uuid.uuid4()),
                    f"Test Worker {style.title()}",
                    f"{style.title()} Executor",
                    f"Generate {style} responses",
                    "worker",
                    style
                )
        
        if not supervisors:
            create_agent(
                str(uuid.uuid4()),
                "Test Supervisor",
                "Supervisor",
                "Review and score outputs",
                "supervisor"
            )
        
        if not decision:
            create_agent(
                str(uuid.uuid4()),
                "Test Decision",
                "Decision Maker",
                "Select best output",
                "decision"
            )
    
    try:
        # Run a simple workflow
        result = await run_workflow("This is a test email about a meeting tomorrow.")
        print(f"✓ Workflow completed. Run ID: {result['run_id']}")
        print(f"✓ Classification: {result['classification'][:50]}...")
        print(f"✓ Worker outputs: {len(result['worker_outputs'])}")
        print(f"✓ Selected agent: {result['selected_agent']}")
        return True
    except Exception as e:
        print(f"✗ Workflow test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_feedback_system():
    """Test feedback and RL learning"""
    print("\n🔍 Testing Feedback System...")
    
    # Get worker agents (only workers have weights)
    workers = get_agents_by_type('worker')
    if not workers:
        print("⚠ No worker agents available for feedback test")
        return False
    
    test_agent = workers[0]
    agent_id = test_agent['id']
    
    # Get initial weight
    initial_weights = get_weights()
    initial_weight = initial_weights.get(agent_id, {}).get('weight', 0.33)
    print(f"Initial weight for {test_agent['name']}: {initial_weight:.4f}")
    
    # Simulate accept feedback
    on_feedback(agent_id, 'accept', score=8.5)
    
    # Check updated weight
    updated_weights = get_weights()
    new_weight = updated_weights.get(agent_id, {}).get('weight', 0.33)
    print(f"After accept: {new_weight:.4f}")
    
    if new_weight > initial_weight:
        print("✓ Weight increased after accept")
        return True
    else:
        print(f"✗ Weight did not increase after accept (expected > {initial_weight:.4f}, got {new_weight:.4f})")
        return False


def run_all_tests():
    """Run all tests"""
    async def _run_tests():
        print("=" * 60)
        print("🚀 FlowForge System Test Suite")
        print("=" * 60)
        
        results = []
        
        # Sync tests
        results.append(("Database", test_database()))
        results.append(("Weight Normalization", test_weights_normalization()))
        results.append(("Integrations", test_integrations()))
        results.append(("Feedback System", test_feedback_system()))
        
        # Async tests
        results.append(("LLM Service", await test_llm_service()))
        results.append(("Workflow", await test_workflow()))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Results")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{name:.<40} {status}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print("=" * 60)
        print(f"Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
        print("=" * 60)
        
        return failed == 0
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_run_tests())


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
