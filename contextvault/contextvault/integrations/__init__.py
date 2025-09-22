"""AI model integrations for ContextVault."""

from .base import BaseIntegration
from .ollama import OllamaIntegration, ollama_integration

__all__ = [
    "BaseIntegration",
    "OllamaIntegration", 
    "ollama_integration",
]
