"""Test runner script with comprehensive reporting."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}")
    print(f"Running: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print(f"\n✅ {description} - PASSED")
    else:
        print(f"\n❌ {description} - FAILED")
    
    return result.returncode == 0


def main():
    """Run all tests."""
    print("="*70)
    print("VIDEO CREATOR - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    results = {}
    
    # Test 1: Integration tests
    results['integration'] = run_command(
        [sys.executable, "-m", "pytest", "tests/test_integration.py", "-v"],
        "Integration Tests"
    )
    
    # Test 2: End-to-end tests
    results['e2e'] = run_command(
        [sys.executable, "-m", "pytest", "tests/test_end_to_end.py", "-v"],
        "End-to-End Tests"
    )
    
    # Test 3: Run test_video_workflow.py
    results['workflow'] = run_command(
        [sys.executable, "test_video_workflow.py"],
        "Workflow Validation"
    )
    
    # Test 4: Run test_ai_prompts.py (if API key available)
    results['ai_prompts'] = run_command(
        [sys.executable, "test_ai_prompts.py"],
        "AI Prompts Test"
    )
    
    # Test 5: MCP server imports
    results['mcp_servers'] = run_command(
        [sys.executable, "test_mcp_servers.py"],
        "MCP Server Tests"
    )
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name.replace('_', ' ').title()}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} test suites passed")
    print("="*70)
    
    if passed_count == total_count:
        print("\n🎉 All tests PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test suite(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
