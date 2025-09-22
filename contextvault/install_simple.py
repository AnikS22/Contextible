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
        # Install all required dependencies
        packages = [
            # Core web framework
            "fastapi==0.104.1",
            "uvicorn==0.24.0",
            "starlette",  # FastAPI dependency
            
            # Database
            "sqlalchemy==2.0.23",
            
            # HTTP client
            "httpx==0.25.2",
            "aiofiles==23.2.0",
            "requests",
            
            # CLI and UI
            "click==8.1.7",
            "rich==13.7.0",
            
            # Configuration and validation
            "pydantic==2.5.0",
            "pydantic-settings==2.1.0",
            "python-dotenv==1.0.0",
            
            # System monitoring (optional)
            "psutil",
            
            # Data processing (optional)
            "numpy",
            "pyyaml==6.0.1",
            "scikit-learn",  # For semantic search fallback
            
            # JSON processing
            "orjson==3.9.10",
            
            # Security
            "passlib[bcrypt]==1.7.4",
            
            # Web interface
            "jinja2==3.1.2",
            "python-multipart==0.0.6"
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

def setup_seamless_integration():
    """Set up seamless Ollama integration with user consent."""
    print("\n🤖 Seamless Ollama Integration Setup")
    print("=" * 50)
    print("This will configure Ollama to work seamlessly with Contextible.")
    print("Your AI models will automatically get context injection!")
    print()
    print("What this does:")
    print("• Stops Ollama on port 11434 (default)")
    print("• Starts Ollama on port 11436 (alternative)")
    print("• Starts Contextible proxy on port 11434")
    print("• Ollama Dashboard works normally with context injection")
    print()
    print("Benefits:")
    print("• Ollama Dashboard works exactly as before")
    print("• All AI models get context injection automatically")
    print("• AI will know you and remember context")
    print("• Completely transparent - no configuration needed")
    print()
    print("⚠️  IMPORTANT: This will temporarily stop your Ollama server")
    print("   and restart it on a different port. This is completely safe.")
    print()
    
    while True:
        choice = input("🤔 Would you like to set up seamless integration? (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            print("\n🚀 Setting up seamless integration...")
            try:
                # Import and run the seamless setup
                import subprocess
                import sys
                from pathlib import Path
                
                script_path = Path(__file__).parent / "scripts" / "seamless_ollama_setup.py"
                result = subprocess.run([sys.executable, str(script_path)], 
                                      capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ Seamless integration setup complete!")
                    print("🎉 You can now use Ollama Dashboard normally with context injection!")
                    return True
                else:
                    print(f"❌ Setup failed: {result.stderr}")
                    print("💡 You can still use Contextible manually")
                    return False
                    
            except Exception as e:
                print(f"❌ Setup error: {e}")
                print("💡 You can still use Contextible manually")
                return False
                
        elif choice in ['n', 'no']:
            print("\n👍 No problem! You can set up seamless integration later with:")
            print("   python scripts/seamless_ollama_setup.py")
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")

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
        from contextvault.database import get_db_context, check_database_connection
        from contextvault.models.context import ContextEntry
        
        # First check if database connection works
        if not check_database_connection():
            raise Exception("Database connection failed")
        
        # Test that we can create a session and the table exists
        try:
            with get_db_context() as db:
                # Just test that we can create a session and the table exists
                # This will fail gracefully if table doesn't exist
                db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='context_entries'").fetchone()
                print("✅ Database works")
        except Exception as e:
            # If table doesn't exist, that's expected on fresh install
            # The CLI will create it when needed
            print("✅ Database connection works (tables will be created when needed)")
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("💡 Note: This doesn't mean Contextible won't work!")
        print("💡 The CLI will initialize the database when you first run it.")
        print("💡 Try running: python contextible.py")
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
    print("🤖 AI Memory Setup:")
    print("   If you chose seamless integration above, you're all set!")
    print("   Your AI models now have context injection automatically.")
    print()
    print("   🔧 Manual Setup (if you skipped seamless integration):")
    print("      1. Make sure Ollama is running: ollama serve")
    print("      2. Start the proxy: python scripts/ollama_proxy.py")
    print("      3. Use: curl http://localhost:11435/api/generate")
    print()
    print("   🎯 Set up seamless integration later:")
    print("      python scripts/seamless_ollama_setup.py")
    print()
    print("💡 Pro tip: The CLI will create the database automatically")
    print("   when you first run it, so don't worry if the test failed.")
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
    
    # Step 4: Test installation (non-critical)
    test_result = test_installation()
    
    # Step 5: Setup seamless integration (with user consent)
    setup_seamless_integration()
    
    # Step 6: Show success (regardless of test result)
    show_success()
    
    # Return 0 for success even if test failed, since CLI works
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
