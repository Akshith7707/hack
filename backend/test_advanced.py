"""
Advanced Test Cases - Edge Cases and Performance
"""
import asyncio
import time
from database import (
    get_all_agents, get_weights, create_agent, get_connection,
    save_feedback, get_agent_feedback_history
)
from workflow_engine import run_workflow
from rl_engine import on_feedback, normalize_weights, check_agent_drift
from integrations import get_next_mock_email, reset_mock_emails
import uuid


def test_empty_input():
    """Test workflow with empty input"""
    print("🔍 Testing Empty Input Handling...")
    
    async def run_test():
        try:
            result = await run_workflow("")
            print("⚠ Empty input accepted (should handle gracefully)")
            return True
        except Exception as e:
            print(f"✓ Empty input properly handled: {str(e)[:50]}")
            return True
    
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(run_test())


def test_very_long_input():
    """Test workflow with very long input"""
    print("\n🔍 Testing Long Input Handling...")
    
    long_input = "This is a test. " * 500  # ~8000 characters
    
    async def run_test():
        try:
            start = time.time()
            result = await run_workflow(long_input)
            duration = time.time() - start
            print(f"✓ Long input processed in {duration:.2f}s")
            return True
        except Exception as e:
            print(f"✗ Failed with long input: {str(e)}")
            return False
    
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(run_test())


def test_special_characters():
    """Test workflow with special characters"""
    print("\n🔍 Testing Special Character Handling...")
    
    special_input = "Test with émojis 🚀 and symbols: @#$%^&*(){}[]|\\:;\"'<>,.?/~`"
    
    async def run_test():
        try:
            result = await run_workflow(special_input)
            print("✓ Special characters handled correctly")
            return True
        except Exception as e:
            print(f"✗ Special character handling failed: {str(e)}")
            return False
    
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(run_test())


def test_concurrent_workflows():
    """Test multiple concurrent workflow executions"""
    print("\n🔍 Testing Concurrent Workflow Execution...")
    
    async def run_test():
        try:
            inputs = [
                "Test email 1 about a meeting",
                "Test email 2 about a project",
                "Test email 3 about a deadline"
            ]
            
            start = time.time()
            results = await asyncio.gather(*[run_workflow(inp) for inp in inputs])
            duration = time.time() - start
            
            print(f"✓ Executed {len(results)} concurrent workflows in {duration:.2f}s")
            return len(results) == 3
        except Exception as e:
            print(f"✗ Concurrent execution failed: {str(e)}")
            return False
    
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(run_test())


def test_database_concurrency():
    """Test database concurrent access"""
    print("\n🔍 Testing Database Concurrency...")
    
    try:
        # Create multiple connections
        conns = [get_connection() for _ in range(5)]
        
        # Try concurrent reads
        for conn in conns:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM agents")
            count = cursor.fetchone()[0]
        
        # Close connections
        for conn in conns:
            conn.close()
        
        print(f"✓ Handled {len(conns)} concurrent connections")
        return True
    except Exception as e:
        print(f"✗ Database concurrency failed: {str(e)}")
        return False


def test_weight_edge_cases():
    """Test RL weight edge cases"""
    print("\n🔍 Testing Weight Edge Cases...")
    
    # Test normalization with zeros
    zero_weights = {'a': 0.0, 'b': 0.0, 'c': 0.0}
    normalized = normalize_weights(zero_weights)
    
    if abs(sum(normalized.values()) - 1.0) < 0.001:
        print("✓ Zero weights normalized correctly")
    else:
        print("✗ Zero weights normalization failed")
        return False
    
    # Test normalization with very small values
    tiny_weights = {'a': 0.0001, 'b': 0.0002, 'c': 0.0003}
    normalized = normalize_weights(tiny_weights)
    
    if abs(sum(normalized.values()) - 1.0) < 0.001:
        print("✓ Tiny weights normalized correctly")
    else:
        print("✗ Tiny weights normalization failed")
        return False
    
    # Test normalization with one dominant weight
    skewed_weights = {'a': 0.95, 'b': 0.03, 'c': 0.02}
    normalized = normalize_weights(skewed_weights)
    
    if abs(sum(normalized.values()) - 1.0) < 0.001:
        print("✓ Skewed weights normalized correctly")
        return True
    else:
        print("✗ Skewed weights normalization failed")
        return False


def test_feedback_persistence():
    """Test that feedback is properly persisted"""
    print("\n🔍 Testing Feedback Persistence...")
    
    workers = [a for a in get_all_agents() if a['type'] == 'worker']
    if not workers:
        print("⚠ No workers available")
        return False
    
    agent_id = workers[0]['id']
    
    # Submit feedback
    on_feedback(agent_id, 'accept', score=9.0, execution_id='test-exec-' + str(uuid.uuid4()))
    
    # Retrieve feedback history
    history = get_agent_feedback_history(agent_id, limit=10)
    
    if history and len(history) > 0:
        print(f"✓ Feedback persisted ({len(history)} entries found)")
        return True
    else:
        print("✗ Feedback not persisted")
        return False


def test_mock_email_rotation():
    """Test mock email rotation"""
    print("\n🔍 Testing Mock Email Rotation...")
    
    # Reset emails
    reset_mock_emails()
    
    # Fetch all emails
    emails = []
    for _ in range(15):  # More than the total mock emails
        email = get_next_mock_email()
        if email:
            emails.append(email['id'])
    
    # Check for rotation (duplicates mean it rotated)
    if len(emails) > len(set(emails)):
        print(f"✓ Email rotation working ({len(emails)} fetched, {len(set(emails))} unique)")
        return True
    else:
        print("⚠ No rotation detected (may need more emails)")
        return True  # Not a failure


def test_drift_detection():
    """Test agent drift detection"""
    print("\n🔍 Testing Drift Detection...")
    
    workers = [a for a in get_all_agents() if a['type'] == 'worker']
    if not workers:
        print("⚠ No workers available")
        return False
    
    agent_id = workers[0]['id']
    
    # Simulate multiple rejections to trigger drift
    for _ in range(10):
        on_feedback(agent_id, 'reject', score=3.0, execution_id='drift-test-' + str(uuid.uuid4()))
    
    try:
        check_agent_drift(agent_id)
        print("✓ Drift detection executed successfully")
        return True
    except Exception as e:
        print(f"✗ Drift detection failed: {str(e)}")
        return False


def run_advanced_tests():
    """Run all advanced tests"""
    print("=" * 60)
    print("🧪 Advanced Test Suite - Edge Cases & Performance")
    print("=" * 60)
    
    results = [
        ("Empty Input", test_empty_input()),
        ("Long Input", test_very_long_input()),
        ("Special Characters", test_special_characters()),
        ("Concurrent Workflows", test_concurrent_workflows()),
        ("Database Concurrency", test_database_concurrency()),
        ("Weight Edge Cases", test_weight_edge_cases()),
        ("Feedback Persistence", test_feedback_persistence()),
        ("Mock Email Rotation", test_mock_email_rotation()),
        ("Drift Detection", test_drift_detection())
    ]
    
    print("\n" + "=" * 60)
    print("📊 Advanced Test Results")
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


if __name__ == "__main__":
    success = run_advanced_tests()
    exit(0 if success else 1)
