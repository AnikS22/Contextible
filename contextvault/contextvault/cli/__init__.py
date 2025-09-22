"""Command-line interface for ContextVault."""

# Import the enhanced CLI by default
from .main_enhanced_v2 import main

def cli():
    """CLI entry point."""
    return main()

__all__ = ["main", "cli"]
