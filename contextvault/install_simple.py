#!/usr/bin/env python3
"""
Super Simple Installation Script for Contextible
For non-technical users - just run this one command!
"""

import sys
import os
import subprocess
from pathlib import Path

def print_header():
    """Print a friendly header."""
    print("🚀 Contextible - AI Memory & Context Layer")
    print("=" * 50)
    print("Making your AI remember everything about you!")
    print()

def check_python():
    """Check if Python is available."""
    print("🐍 Checking Python...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Please install Python first.")
        print("   Download from: https://python.org")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} found")
    return True

def install_dependencies():
    """Install required packages."""
    print("\n📦 Installing dependencies...")
    try:
        # Install core dependencies only
        packages = [
            "fastapi==0.104.1",
            "uvicorn==0.24.0", 
            "sqlalchemy==2.0.23",
            "httpx==0.25.2",
            "rich==13.7.0",
            "click==8.1.7",
            "pydantic==2.5.0",
            "pydantic-settings==2.1.0",
            "python-dotenv==1.0.0",
            "aiofiles==23.2.0"
        ]
        
        for package in packages:
            print(f"   Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
        
        print("✅ All dependencies installed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("   Try running: pip install --upgrade pip")
        return False

def setup_database():
    """Set up the database."""
    print("\n🗄️ Setting up database...")
    try:
        # Add current directory to path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        # Import and initialize database
        from contextvault.database import init_database, create_tables
        
        init_database()
        create_tables()
        print("✅ Database ready!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def test_installation():
    """Test that everything works."""
    print("\n🧪 Testing installation...")
    try:
        # Test imports
        import contextvault
        print("✅ Core module works")
        
        # Test CLI
        from contextvault.cli.main_enhanced_v2 import EnhancedContextVaultCLI
        cli = EnhancedContextVaultCLI()
        print("✅ CLI works")
        
        # Test database
        from contextvault.database import get_db_session
        from contextvault.models.context import ContextEntry
        with get_db_session() as db:
            db.query(ContextEntry).first()
        print("✅ Database works")
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def show_success():
    """Show success message and next steps."""
    print("\n" + "=" * 50)
    print("🎉 SUCCESS! Contextible is ready to use!")
    print("=" * 50)
    print()
    print("🚀 Quick Start:")
    print("   1. Run: python contextible.py")
    print("   2. Type: add \"My name is John and I'm a developer\"")
    print("   3. Type: list")
    print("   4. Type: help")
    print()
    print("🤖 To use with Ollama:")
    print("   1. Run: python scripts/ollama_proxy.py")
    print("   2. Use Ollama normally - it will have memory!")
    print()
    print("📚 Need help? Check the README.md file")
    print("=" * 50)

def main():
    """Main installation process."""
    print_header()
    
    # Step 1: Check Python
    if not check_python():
        return 1
    
    # Step 2: Install dependencies
    if not install_dependencies():
        return 1
    
    # Step 3: Setup database
    if not setup_database():
        return 1
    
    # Step 4: Test installation
    if not test_installation():
        return 1
    
    # Step 5: Show success
    show_success()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled. Run again when ready!")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check the README.md for troubleshooting help.")
        sys.exit(1)
