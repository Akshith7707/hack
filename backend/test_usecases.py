"""
Real-World Use Case Tests
Test FlowForge with realistic scenarios
"""
import asyncio
from workflow_engine import run_workflow
from database import get_all_agents
from rl_engine import on_feedback


async def test_customer_support_email():
    """Test handling customer support email"""
    print("🔍 Test Case 1: Customer Support Email")
    print("-" * 50)
    
    email = """
    Subject: Urgent - Cannot Access My Account
    
    Hi Support Team,
    
    I've been trying to log into my account for the past hour but keep 
    getting an "Invalid credentials" error. I'm sure my password is correct.
    This is very urgent as I need to submit my report by end of day.
    
    Can you please help ASAP?
    
    Thanks,
    John Smith
    """
    
    result = await run_workflow(email)
    
    print(f"✓ Classified as: {result['classification'][:30]}...")
    print(f"✓ Generated {len(result['worker_outputs'])} response options")
    print(f"✓ Selected agent: {result['selected_agent'][:30]}...")
    print(f"✓ Final output preview: {result['final_output'][:100]}...")
    
    return True


async def test_sales_inquiry():
    """Test handling sales inquiry"""
    print("\n🔍 Test Case 2: Sales Inquiry")
    print("-" * 50)
    
    email = """
    Subject: Pricing for Enterprise Plan
    
    Hello,
    
    We're a company with 500 employees looking to adopt your platform.
    Could you provide pricing details for the Enterprise plan?
    
    Also, do you offer custom integrations and dedicated support?
    
    Best regards,
    Sarah Johnson
    VP of Engineering
    """
    
    result = await run_workflow(email)
    
    print(f"✓ Classified as: {result['classification'][:30]}...")
    print(f"✓ Generated {len(result['worker_outputs'])} response options")
    print(f"✓ Best option score: {max([w.get('score', 0) for w in result['worker_outputs']])}/10")
    
    return True


async def test_bug_report():
    """Test handling bug report"""
    print("\n🔍 Test Case 3: Bug Report")
    print("-" * 50)
    
    email = """
    Subject: Bug - Dashboard not loading
    
    Hi Team,
    
    The dashboard page has been showing a blank screen since this morning.
    Browser console shows: "TypeError: Cannot read property 'data' of undefined"
    
    Steps to reproduce:
    1. Login
    2. Click Dashboard
    3. Page goes blank
    
    This is affecting our entire team.
    
    Tech specs:
    - Chrome 120
    - Windows 11
    - Account: enterprise-trial
    """
    
    result = await run_workflow(email)
    
    print(f"✓ Classified as: {result['classification'][:30]}...")
    print(f"✓ Context signals: {result['context_signals']}")
    
    return True


async def test_feedback_learning():
    """Test that system learns from feedback"""
    print("\n🔍 Test Case 4: Learning from Feedback")
    print("-" * 50)
    
    # Run same workflow twice
    email = "Quick question about API rate limits."
    
    result1 = await run_workflow(email)
    selected_agent_1 = result1['selected_agent']
    
    # Simulate positive feedback
    workers = [a for a in get_all_agents() if a['type'] == 'worker']
    if workers:
        on_feedback(workers[0]['id'], 'accept', score=9.0)
        print(f"✓ Submitted positive feedback for {workers[0]['name']}")
    
    # Run again
    result2 = await run_workflow(email)
    selected_agent_2 = result2['selected_agent']
    
    print(f"✓ First run selected: {selected_agent_1[:30]}...")
    print(f"✓ Second run selected: {selected_agent_2[:30]}...")
    print("✓ System is learning from feedback")
    
    return True


async def test_different_urgency_levels():
    """Test handling different urgency levels"""
    print("\n🔍 Test Case 5: Urgency Detection")
    print("-" * 50)
    
    urgent = "URGENT: Production server is down! Need help NOW!"
    normal = "When you have a moment, could you clarify the pricing tiers?"
    
    result_urgent = await run_workflow(urgent)
    result_normal = await run_workflow(normal)
    
    print(f"✓ Urgent email context: {result_urgent['context_signals'].get('urgency', 'unknown')}")
    print(f"✓ Normal email context: {result_normal['context_signals'].get('urgency', 'unknown')}")
    
    return True


async def run_use_case_tests():
    """Run all real-world use case tests"""
    print("=" * 60)
    print("🌍 Real-World Use Case Test Suite")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Customer Support", await test_customer_support_email()))
        results.append(("Sales Inquiry", await test_sales_inquiry()))
        results.append(("Bug Report", await test_bug_report()))
        results.append(("Feedback Learning", await test_feedback_learning()))
        results.append(("Urgency Detection", await test_different_urgency_levels()))
    except Exception as e:
        print(f"\n✗ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("📊 Use Case Test Results")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:.<40} {status}")
    
    print("=" * 60)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(run_use_case_tests())
    exit(0 if success else 1)
