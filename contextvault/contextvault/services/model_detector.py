"""AI Model Detection Service for ContextVault."""

import asyncio
import json
import logging
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


@dataclass
class DetectedModel:
    """Represents a detected AI model."""
    name: str
    host: str
    port: int
    endpoint: str
    provider: str  # "ollama", "lmstudio", "openai", etc.
    status: str  # "running", "stopped", "unknown"
    version: Optional[str] = None
    context_injection_enabled: bool = False
    last_seen: Optional[str] = None


class ModelDetector:
    """Service for detecting AI models running on the system."""
    
    def __init__(self):
        self.detected_models: Dict[str, DetectedModel] = {}
        self.common_ports = [11434, 11435, 8000, 8080, 3000, 5000, 7860, 7861]
        
    async def detect_all_models(self) -> List[DetectedModel]:
        """Detect all AI models running on the system."""
        logger.info("Starting AI model detection...")
        
        detected = []
        
        # Detect Ollama models
        ollama_models = await self._detect_ollama_models()
        detected.extend(ollama_models)
        
        # Detect LM Studio models
        lmstudio_models = await self._detect_lmstudio_models()
        detected.extend(lmstudio_models)
        
        # Detect other common AI services
        other_models = await self._detect_other_services()
        detected.extend(other_models)
        
        # Update our cache
        for model in detected:
            self.detected_models[model.name] = model
        
        logger.info(f"Detected {len(detected)} AI models")
        return detected
    
    async def _detect_ollama_models(self) -> List[DetectedModel]:
        """Detect Ollama models."""
        models = []
        
        # Check common Ollama ports
        ollama_ports = [11434, 11435]
        
        for port in ollama_ports:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(f"http://localhost:{port}/api/tags")
                    
                    if response.status_code == 200:
                        data = response.json()
                        ollama_models = data.get("models", [])
                        
                        for model_data in ollama_models:
                            model_name = model_data.get("name", "unknown")
                            
                            # Check if this is our ContextVault proxy
                            is_proxy = port == 11435
                            
                            model = DetectedModel(
                                name=model_name,
                                host="localhost",
                                port=port,
                                endpoint=f"http://localhost:{port}",
                                provider="ollama",
                                status="running",
                                version=model_data.get("modified_at", ""),
                                context_injection_enabled=is_proxy,
                                last_seen="now"
                            )
                            models.append(model)
                            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
                # Port not accessible
                continue
        
        return models
    
    async def _detect_lmstudio_models(self) -> List[DetectedModel]:
        """Detect LM Studio models."""
        models = []
        
        # LM Studio typically runs on port 1234
        lmstudio_ports = [1234, 1235]
        
        for port in lmstudio_ports:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(f"http://localhost:{port}/v1/models")
                    
                    if response.status_code == 200:
                        data = response.json()
                        lmstudio_models = data.get("data", [])
                        
                        for model_data in lmstudio_models:
                            model_name = model_data.get("id", "unknown")
                            
                            model = DetectedModel(
                                name=model_name,
                                host="localhost",
                                port=port,
                                endpoint=f"http://localhost:{port}",
                                provider="lmstudio",
                                status="running",
                                version=model_data.get("created", ""),
                                context_injection_enabled=False,
                                last_seen="now"
                            )
                            models.append(model)
                            
            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
                continue
        
        return models
    
    async def _detect_other_services(self) -> List[DetectedModel]:
        """Detect other AI services."""
        models = []
        
        # Check for common AI service ports
        service_checks = [
            (8000, "openai-compatible"),
            (8080, "generic-ai"),
            (7860, "gradio"),
            (7861, "gradio"),
        ]
        
        for port, provider in service_checks:
            try:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    # Try a simple health check
                    response = await client.get(f"http://localhost:{port}/")
                    
                    if response.status_code in [200, 404]:  # 404 is OK for some services
                        model = DetectedModel(
                            name=f"{provider}-service",
                            host="localhost",
                            port=port,
                            endpoint=f"http://localhost:{port}",
                            provider=provider,
                            status="running",
                            context_injection_enabled=False,
                            last_seen="now"
                        )
                        models.append(model)
                        
            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
                continue
        
        return models
    
    def get_model_status(self, model_name: str) -> Optional[DetectedModel]:
        """Get the current status of a specific model."""
        return self.detected_models.get(model_name)
    
    def update_model_config(self, model_name: str, context_injection: bool) -> bool:
        """Update the context injection setting for a model."""
        if model_name in self.detected_models:
            self.detected_models[model_name].context_injection_enabled = context_injection
            return True
        return False
    
    def get_models_summary(self) -> Dict[str, Any]:
        """Get a summary of all detected models."""
        total_models = len(self.detected_models)
        running_models = len([m for m in self.detected_models.values() if m.status == "running"])
        injection_enabled = len([m for m in self.detected_models.values() if m.context_injection_enabled])
        
        providers = {}
        for model in self.detected_models.values():
            providers[model.provider] = providers.get(model.provider, 0) + 1
        
        return {
            "total_models": total_models,
            "running_models": running_models,
            "injection_enabled": injection_enabled,
            "providers": providers,
            "models": [
                {
                    "name": m.name,
                    "provider": m.provider,
                    "status": m.status,
                    "context_injection": m.context_injection_enabled,
                    "endpoint": m.endpoint
                }
                for m in self.detected_models.values()
            ]
        }


# Global instance
model_detector = ModelDetector()
