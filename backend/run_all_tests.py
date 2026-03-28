"""
Final System Validation - Simplified
"""
import subprocess
import sys

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def run_test_suite(script_name):
    """Run a test suite and return success status"""
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=180
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⚠️  Test timed out after 180 seconds")
        return False
    except Exception as e:
        print(f"❌ Failed to run: {str(e)}")
        return False

def main():
    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "FlexCode Complete System Validation" + " " * 16 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = []
    
    # Run system tests
    print_header("SYSTEM TESTS")
    print("Running core functionality tests...")
    results.append(("System Tests", run_test_suite("test_system.py")))
    
    # Run use case tests
    print_header("USE CASE TESTS")
    print("Running real-world scenario tests...")
    results.append(("Use Case Tests", run_test_suite("test_usecases.py")))
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:.<40} {status}")
    
    print("\n" + "=" * 70)
    
    if passed == len(results):
        print("\n🎉 " * 20)
        print("     ALL VALIDATIONS PASSED - SYSTEM READY!")
        print("🎉 " * 20)
        print("\n📚 Next Steps:")
        print("   1. Run: start.bat (to start the servers)")
        print("   2. Open: http://localhost:5173")
        print("   3. Read: TEST_REPORT.md for details")
        return True
    else:
        print(f"\n⚠️  {failed} test suite(s) failed. Check output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
