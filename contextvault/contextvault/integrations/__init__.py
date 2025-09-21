"""AI model integrations for ContextVault."""

from .base import BaseIntegration
from .ollama import OllamaIntegration, ollama_integration
from .lmstudio import LMStudioIntegration, lmstudio_integration
from .jan_ai import JanAIIntegration, jan_ai_integration
from .localai import LocalAIIntegration, localai_integration
from .gpt4all import GPT4AllIntegration, gpt4all_integration

__all__ = [
    "BaseIntegration",
    "OllamaIntegration", 
    "ollama_integration",
    "LMStudioIntegration",
    "lmstudio_integration",
    "JanAIIntegration",
    "jan_ai_integration",
    "LocalAIIntegration",
    "localai_integration",
    "GPT4AllIntegration",
    "gpt4all_integration",
]
