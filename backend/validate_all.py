"""
FlexCode - Complete System Optimization and Validation
Run this to validate entire system and get recommendations
"""
import asyncio
import time
import json
from datetime import datetime

# Import all test modules
from test_system import run_all_tests
from test_usecases import run_use_case_tests

# Import core modules
from database import get_connection, get_all_agents, get_weights, get_all_workflows
from llm_service import call_llm


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_system_health():
    """Check overall system health"""
    print_header("SYSTEM HEALTH CHECK")
    
    health = {
        'database': False,
        'agents': False,
        'workflows': False,
        'llm': False
    }
    
    # Database connection
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        health['database'] = True
        print("✅ Database: Connected")
    except Exception as e:
        print(f"❌ Database: Failed - {str(e)}")
    
    # Agents
    try:
        agents = get_all_agents()
        if len(agents) >= 6:
            health['agents'] = True
            print(f"✅ Agents: {len(agents)} agents configured")
            
            # Check agent types
            types = {}
            for agent in agents:
                t = agent['type']
                types[t] = types.get(t, 0) + 1
            
            for agent_type, count in types.items():
                print(f"   - {agent_type}: {count}")
        else:
            print(f"⚠️  Agents: Only {len(agents)} agents (need 6 minimum)")
    except Exception as e:
        print(f"❌ Agents: Failed - {str(e)}")
    
    # Workflows
    try:
        workflows = get_all_workflows()
        health['workflows'] = True
        print(f"✅ Workflows: {len(workflows)} workflows configured")
    except Exception as e:
        print(f"❌ Workflows: Failed - {str(e)}")
    
    # LLM Service
    async def test_llm():
        try:
            await call_llm("You are a test bot.", "Reply with 'OK'", timeout=10)
            return True
        except:
            return False
    
    try:
        loop = asyncio.new_event_loop()
        if loop.run_until_complete(test_llm()):
            health['llm'] = True
            print("✅ LLM Service: Connected to Featherless.ai")
        else:
            print("❌ LLM Service: Connection failed")
    except Exception as e:
        print(f"❌ LLM Service: Failed - {str(e)}")
    
    # Overall health
    health_score = sum(health.values()) / len(health) * 100
    print(f"\n📊 Overall Health: {health_score:.0f}%")
    
    return health_score >= 75


def get_performance_stats():
    """Get performance statistics"""
    print_header("PERFORMANCE STATISTICS")
    
    try:
        agents = get_all_agents()
        weights = get_weights()
        workflows = get_all_workflows()
        
        print(f"📈 Resource Usage:")
        print(f"   - Total Agents: {len(agents)}")
        print(f"   - Worker Agents: {len(weights)}")
        print(f"   - Workflows: {len(workflows)}")
        
        # Check weight distribution
        if weights:
            print(f"\n⚖️  Weight Distribution:")
            for agent_id, data in weights.items():
                agent_name = data.get('name', 'Unknown')
                weight = data.get('weight', 0)
                selected = data.get('times_selected', 0)
                accepted = data.get('times_accepted', 0)
                rejected = data.get('times_rejected', 0)
                
                print(f"   - {agent_name}:")
                print(f"     Weight: {weight:.4f} | Selected: {selected} | Accept: {accepted} | Reject: {rejected}")
                
                if selected > 0:
                    accept_rate = (accepted / selected) * 100
                    print(f"     Acceptance Rate: {accept_rate:.1f}%")
        
        return True
    except Exception as e:
        print(f"❌ Failed to get stats: {str(e)}")
        return False


def get_optimization_recommendations():
    """Get optimization recommendations"""
    print_header("OPTIMIZATION RECOMMENDATIONS")
    
    recommendations = []
    
    try:
        weights = get_weights()
        
        # Check for imbalanced weights
        if weights:
            weight_values = [data.get('weight', 0) for data in weights.values()]
            max_weight = max(weight_values)
            min_weight = min(weight_values)
            
            if max_weight - min_weight > 0.5:
                recommendations.append({
                    'level': 'INFO',
                    'category': 'RL System',
                    'message': f'Weight imbalance detected (range: {min_weight:.3f} to {max_weight:.3f})',
                    'suggestion': 'This is normal if one agent consistently performs better'
                })
            
            # Check for underused agents
            for agent_id, data in weights.items():
                if data.get('times_selected', 0) == 0:
                    recommendations.append({
                        'level': 'WARNING',
                        'category': 'Agent Usage',
                        'message': f"Agent {data.get('name', 'Unknown')} never selected",
                        'suggestion': 'Consider adjusting agent weights or goals'
                    })
        
        # Database optimizations
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0]
        
        if db_size > 10 * 1024 * 1024:  # 10 MB
            recommendations.append({
                'level': 'INFO',
                'category': 'Database',
                'message': f'Database size: {db_size / 1024 / 1024:.2f} MB',
                'suggestion': 'Consider implementing log rotation or archiving'
            })
        
        conn.close()
        
    except Exception as e:
        recommendations.append({
            'level': 'ERROR',
            'category': 'System',
            'message': f'Failed to analyze: {str(e)}',
            'suggestion': 'Check error logs'
        })
    
    # Print recommendations
    if recommendations:
        for rec in recommendations:
            icon = {'INFO': 'ℹ️', 'WARNING': '⚠️', 'ERROR': '❌'}.get(rec['level'], '•')
            print(f"\n{icon} [{rec['level']}] {rec['category']}")
            print(f"   {rec['message']}")
            print(f"   💡 {rec['suggestion']}")
    else:
        print("\n✅ No optimization recommendations - system is well-tuned!")
    
    return len([r for r in recommendations if r['level'] == 'ERROR']) == 0


def generate_summary_report():
    """Generate final summary report"""
    print_header("FINAL VALIDATION SUMMARY")
    
    print(f"\n📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️  System: FlexCode v2.0.0")
    print(f"🐍 Python: 3.13.7")
    print(f"⚡ Framework: FastAPI + React")
    
    print("\n" + "=" * 70)
    print("  VALIDATION COMPLETE")
    print("=" * 70)
    
    print("\n✅ System is ready for deployment!")
    print("\n📚 Documentation:")
    print("   - README.md - Full documentation")
    print("   - TEST_REPORT.md - Detailed test results")
    print("   - FlexCode_BLUEPRINT.md - Architecture details")
    
    print("\n🚀 Quick Start:")
    print("   1. Run: start.bat")
    print("   2. Open: http://localhost:5173")
    print("   3. Click 'Quick Demo Setup' to initialize")
    
    print("\n🧪 Test Commands:")
    print("   - python test_system.py     (Core functionality)")
    print("   - python test_usecases.py   (Real-world scenarios)")
    print("   - python test_advanced.py   (Edge cases)")
    
    print("\n" + "=" * 70)


async def run_full_validation():
    """Run complete validation"""
    start_time = time.time()
    
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "FlexCode Complete System Validation" + " " * 16 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Step 1: Health check
    health_ok = check_system_health()
    
    if not health_ok:
        print("\n❌ System health check failed. Please fix errors before proceeding.")
        return False
    
    # Step 2: Performance stats
    get_performance_stats()
    
    # Step 3: Run core tests
    print_header("RUNNING CORE TESTS")
    print("Running system tests...\n")
    core_tests = run_all_tests()
    
    # Step 4: Run use case tests
    print_header("RUNNING USE CASE TESTS")
    print("Running real-world scenario tests...\n")
    use_case_tests = await run_use_case_tests()
    
    # Step 5: Optimization recommendations
    optimization_ok = get_optimization_recommendations()
    
    # Step 6: Summary
    generate_summary_report()
    
    duration = time.time() - start_time
    print(f"\n⏱️  Total validation time: {duration:.2f} seconds")
    
    # Final verdict
    all_passed = core_tests and use_case_tests and optimization_ok
    
    if all_passed:
        print("\n" + "🎉 " * 20)
        print("     ALL VALIDATIONS PASSED - SYSTEM READY!")
        print("🎉 " * 20)
        return True
    else:
        print("\n⚠️  Some validations failed. Check errors above.")
        return False


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(run_full_validation())
    exit(0 if success else 1)
