#!/usr/bin/env python3
"""
Installation Test Script for Contextible

This script tests that all components work correctly after a fresh installation.
Run this after cloning the repository to verify everything is working.
"""

import sys
import os
import subprocess
from pathlib import Path

def test_imports():
    """Test that all core modules can be imported."""
    print("🧪 Testing Core Module Imports...")
    
    try:
        # Core modules
        import contextvault
        print("✅ Core contextvault module")
        
        from contextvault.integrations.ollama import OllamaIntegration
        print("✅ OllamaIntegration")
        
        from contextvault.services.context_retrieval import ContextRetrievalService
        print("✅ ContextRetrievalService")
        
        from contextvault.cli.enhanced_ui import EnhancedContextVaultUI
        print("✅ Enhanced UI")
        
        from contextvault.database import init_database, check_database_connection
        print("✅ Database functions")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_configuration():
    """Test configuration system."""
    print("\n⚙️ Testing Configuration System...")
    
    try:
        # Test fallback configuration
        from user_config import get_user_paths, get_custom_path
        print("✅ Configuration system available")
        
        paths = get_user_paths()
        print(f"✅ Default paths configured: {len(paths)} paths")
        
        # Test custom path function
        test_path = get_custom_path('project_root', '~/DefaultProjects')
        print(f"✅ Custom path function works: {test_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_requirements():
    """Test that all required packages are available."""
    print("\n📦 Testing Requirements...")
    
    requirements = [
        'fastapi',
        'uvicorn', 
        'sqlalchemy',
        'httpx',
        'rich',
        'click',
        'pydantic'
    ]
    
    all_good = True
    for req in requirements:
        try:
            __import__(req)
            print(f"✅ {req}")
        except ImportError as e:
            print(f"❌ {req}: {e}")
            all_good = False
    
    # Test dotenv separately
    try:
        import dotenv
        print("✅ dotenv (python-dotenv)")
    except ImportError:
        print("❌ dotenv: Not available")
        all_good = False
    
    return all_good

def test_scripts():
    """Test that installation scripts are valid."""
    print("\n📜 Testing Installation Scripts...")
    
    scripts = [
        'install.sh',
        'setup_seamless.sh',
        'scripts/ollama_proxy.py'
    ]
    
    all_good = True
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            print(f"✅ {script} exists")
            
            # Test shell script syntax
            if script.endswith('.sh'):
                try:
                    result = subprocess.run(['bash', '-n', script], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"✅ {script} syntax valid")
                    else:
                        print(f"❌ {script} syntax error: {result.stderr}")
                        all_good = False
                except Exception as e:
                    print(f"❌ {script} test error: {e}")
                    all_good = False
            
            # Test Python script imports
            elif script.endswith('.py'):
                try:
                    result = subprocess.run([sys.executable, '-m', 'py_compile', script],
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"✅ {script} syntax valid")
                    else:
                        print(f"❌ {script} syntax error: {result.stderr}")
                        all_good = False
                except Exception as e:
                    print(f"❌ {script} test error: {e}")
                    all_good = False
        else:
            print(f"❌ {script} not found")
            all_good = False
    
    return all_good

def test_cli():
    """Test CLI functionality."""
    print("\n🖥️ Testing CLI...")
    
    try:
        # Test CLI import
        from contextvault.cli.main_enhanced_v2 import EnhancedContextVaultCLI
        print("✅ CLI module imports")
        
        # Test CLI initialization (without actually running it)
        cli = EnhancedContextVaultCLI()
        print("✅ CLI initializes correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI error: {e}")
        return False

def test_database():
    """Test database functionality."""
    print("\n🗄️ Testing Database...")
    
    try:
        from contextvault.database import init_database, check_database_connection
        print("✅ Database functions available")
        
        # Test database connection (without actually connecting)
        print("✅ Database connection check available")
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Contextible Installation Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_requirements,
        test_scripts,
        test_cli,
        test_database
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All {total} tests passed!")
        print("\n✅ Contextible is ready for installation!")
        print("\nNext steps:")
        print("1. Run: ./install.sh")
        print("2. Or run: ./setup_seamless.sh for one-click setup")
        print("3. Use: python contextible.py")
        return 0
    else:
        print(f"❌ {total - passed} out of {total} tests failed")
        print("\nPlease fix the failing tests before installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
