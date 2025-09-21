#!/usr/bin/env python3
"""
Contextible - AI Memory & Context Layer
Main entry point for the Contextible CLI
"""

import sys
import asyncio
from pathlib import Path

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent))

from contextvault.cli.setup_wizard import run_setup_wizard
from contextvault.cli.main_enhanced_v2 import main as cli_main
from contextvault.database import check_database_connection


def show_contextible_banner():
    """Show the Contextible banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  ██████╗ ██████╗ ███╗   ██╗████████╗███████╗██╗   ██╗████████╗██╗██████╗ ██╗     ║
║ ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝██║   ██║╚══██╔══╝██║██╔══██╗██║     ║
║ ██║     ██║   ██║██╔██╗ ██║   ██║   █████╗  ██║   ██║   ██║   ██║██████╔╝██║     ║
║ ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝  ╚██╗ ██╔╝   ██║   ██║██╔══██╗██║     ║
║ ╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗ ╚████╔╝    ██║   ██║██║  ██║███████╗║
║  ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝  ╚═══╝     ╚═╝   ╚═╝╚═╝  ╚═╝╚══════╝║
║                                                                              ║
║                    🧠 AI Memory & Context Layer 🧠                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def main():
    """Main entry point for Contextible."""
    show_contextible_banner()
    
    # Check if this is the first run
    if not check_database_connection():
        print("🔧 First time setup detected!")
        print("Running setup wizard...\n")
        
        success = await run_setup_wizard()
        if not success:
            print("❌ Setup failed. Please try again.")
            sys.exit(1)
        
        print("\n🎉 Setup complete! Starting Contextible CLI...\n")
    
    # Run the main CLI
    try:
        cli_main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
