#!/usr/bin/env python3
"""
ContextVault CLI - Enhanced Main Entry Point
Beautiful, interactive interface inspired by Claude Code
"""

import sys
import os
from pathlib import Path

# Check if this is the enhanced CLI or legacy CLI
def should_use_enhanced_cli() -> bool:
    """Determine if we should use the enhanced CLI."""
    # Check for --legacy flag
    if "--legacy" in sys.argv:
        sys.argv.remove("--legacy")
        return False
    
    # Check for specific legacy commands
    legacy_commands = [
        "context", "permissions", "templates", "test", "demo", 
        "diagnose", "config", "setup", "mcp", "learning", "auto-context"
    ]
    
    if len(sys.argv) > 1 and sys.argv[1] in legacy_commands:
        return False
    
    # Use enhanced CLI by default
    return True

if should_use_enhanced_cli():
    # Use the enhanced CLI v2
    from .main_enhanced_v2 import main
    
    if __name__ == "__main__":
        sys.exit(main())
else:
    # Use the legacy CLI
    import click
    from rich.console import Console

    console = Console()

    @click.group()
    @click.version_option(version="0.1.0", prog_name="ContextVault")
    def cli():
        """
        ContextVault - AI Memory for Local AI Models
        
        ContextVault gives your local AI models persistent memory,
        transforming them from generic chatbots into personal assistants
        that actually know you.
        """
        pass

        # Import and register command groups
        from contextvault.cli.commands import (
            system, context, permissions, templates, 
            test, demo, diagnose, config, setup, mcp, learning, auto_context, debug, models
        )

    # Add command groups
    cli.add_command(setup.setup)
    cli.add_command(system.system_group)
    cli.add_command(context.context_group)
    cli.add_command(permissions.permissions_group)
    cli.add_command(templates.templates)
    cli.add_command(test.test_group)
    cli.add_command(demo.demo_group)
    cli.add_command(diagnose.diagnose_group)
    cli.add_command(config.config_group)
    cli.add_command(mcp.mcp_group)
    cli.add_command(learning.learning_group)
    cli.add_command(auto_context.auto_context)
    cli.add_command(debug.debug_group)
    cli.add_command(models.models)

    if __name__ == "__main__":
        cli()
