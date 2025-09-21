#!/usr/bin/env python3
"""
Comprehensive test of all Contextible dashboard commands
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🧪 Testing: {description}")
    print(f"Command: {cmd}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()[:200]}...")
            return True
        else:
            print(f"❌ FAILED: {description}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {description}")
        return False
    except Exception as e:
        print(f"💥 ERROR: {description} - {e}")
        return False

def main():
    """Run comprehensive dashboard command tests."""
    print("🚀 Contextible Dashboard Commands Test Suite")
    print("=" * 60)
    
    # Change to the correct directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Test commands
    test_commands = [
        # Core context commands
        ("python contextvault/contextible.py add 'I am a test user named TestUser'", "Add context command"),
        ("python contextvault/contextible.py list", "List context command"),
        ("python contextvault/contextible.py search test", "Search context command"),
        ("python contextvault/contextible.py analytics", "Analytics command"),
        
        # Model management commands
        ("python contextvault/contextible.py models list", "Models list command"),
        
        # System commands
        ("python contextvault/contextible.py status", "Status command"),
        
        # Test commands
        ("python contextvault/contextible.py test-all", "Test all command"),
    ]
    
    results = []
    
    for cmd, description in test_commands:
        success = run_command(cmd, description)
        results.append((description, success))
        time.sleep(1)  # Brief pause between commands
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {description}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Dashboard commands are working perfectly!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    import os
    sys.exit(main())
