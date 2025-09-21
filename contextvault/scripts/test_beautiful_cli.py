#!/usr/bin/env python3
"""
Test script for the beautiful ContextVault CLI
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.cli.components import ContextVaultUI
from contextvault.setup.wizard import SetupWizard
from contextvault.services.health import health_service


def test_ui_components():
    """Test the UI components."""
    print("🎨 Testing ContextVault UI Components")
    print("=" * 50)
    
    # Test welcome banner
    print("\n1. Welcome Banner:")
    ContextVaultUI.show_welcome_banner()
    
    # Test setup options
    print("\n2. Setup Options (simulated):")
    print("Would show interactive setup options here...")
    
    # Test progress steps
    print("\n3. Progress Steps:")
    ContextVaultUI.show_progress_step("Checking system", "In progress...", "working")
    ContextVaultUI.show_progress_step("Database init", "Completed", "success")
    ContextVaultUI.show_progress_step("Ollama test", "Failed", "error")
    
    # Test status dashboard
    print("\n4. Status Dashboard:")
    ContextVaultUI.show_status_dashboard()
    
    # Test health check
    print("\n5. Health Check:")
    ContextVaultUI.show_health_check()
    
    # Test messages
    print("\n6. Message Types:")
    ContextVaultUI.show_success_message("Operation completed successfully!")
    ContextVaultUI.show_warning_message("This is a warning message")
    ContextVaultUI.show_error_message("This is an error message")
    
    # Test brand colors
    print("\n7. Brand Colors:")
    from contextvault.cli.components import show_brand_colors
    show_brand_colors()


def test_setup_wizard():
    """Test the setup wizard components."""
    print("\n🔧 Testing Setup Wizard Components")
    print("=" * 50)
    
    wizard = SetupWizard()
    
    # Test system requirements check
    print("\n1. System Requirements Check:")
    wizard.check_system_requirements()
    
    # Test database initialization
    print("\n2. Database Initialization:")
    wizard.init_database()
    
    # Test Ollama detection
    print("\n3. Ollama Detection:")
    wizard.detect_ollama()
    
    # Test Ollama connectivity
    print("\n4. Ollama Connectivity:")
    wizard.test_ollama()
    
    # Test service checks
    print("\n5. Service Checks:")
    wizard.check_service("http://localhost:8000/health/", "API Server")
    wizard.check_service("http://localhost:11435/health", "Proxy Server")


def test_health_service():
    """Test the health service."""
    print("\n🏥 Testing Health Service")
    print("=" * 50)
    
    # Test quick status
    print("\n1. Quick Status:")
    status = health_service.get_quick_status()
    print(f"API Running: {status['services'].get('api', {}).get('running', False)}")
    print(f"Proxy Running: {status['services'].get('proxy', {}).get('running', False)}")
    print(f"Ollama Running: {status['services'].get('ollama', {}).get('running', False)}")
    print(f"Database Connected: {status.get('database', {}).get('connected', False)}")


def main():
    """Run all tests."""
    print("🧪 ContextVault Beautiful CLI Test Suite")
    print("=" * 60)
    
    try:
        test_ui_components()
        test_setup_wizard()
        test_health_service()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("🎉 The beautiful CLI components are working!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
