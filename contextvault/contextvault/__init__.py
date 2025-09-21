"""ContextVault - Local-first context management layer for AI models."""

__version__ = "0.1.0"
__author__ = "ContextVault Contributors"
__description__ = "Local-first context management layer for AI models"

from .config import settings
from .database import get_db_session, init_database

__all__ = [
    "__version__",
    "__author__", 
    "__description__",
    "settings",
    "get_db_session",
    "init_database",
]
