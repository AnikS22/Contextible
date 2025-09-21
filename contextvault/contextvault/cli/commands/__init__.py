"""ContextVault CLI commands package."""

# Import all command modules
from . import (
    system, context, permissions, templates, 
    test, demo, diagnose, config, setup, debug, models
)

__all__ = [
    'system', 'context', 'permissions', 'templates',
    'test', 'demo', 'diagnose', 'config', 'setup', 'debug', 'models'
]
