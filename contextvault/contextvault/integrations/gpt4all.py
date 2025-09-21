"""GPT4All integration for ContextVault."""

import json
import logging
from typing import Any, Dict, List, Optional

from .base import BaseIntegration
from ..models import Session as SessionModel
from ..services import context_retrieval_service
from ..config import settings
from ..services.templates import template_manager, format_context_with_template

logger = logging.getLogger(__name__)


class GPT4AllIntegration(BaseIntegration):
    """Integration for GPT4All models."""
    
    def __init__(self, host: str = None, port: int = None):
        """
        Initialize GPT4All integration.
        
        Args:
            host: GPT4All host (defaults to localhost)
            port: GPT4All port (defaults to 4891)
        """
        host = host or "localhost"
        port = port or 4891
        super().__init__(name="gpt4all", host=host, port=port)
    
    async def inject_context(
        self,
        request_data: Dict[str, Any],
        model_id: str,
        session: Optional[SessionModel] = None,
    ) -> Dict[str, Any]:
        """
        Inject context into GPT4All request.
        
        Args:
            request_data: Original GPT4All request data
            model_id: Model identifier
            session: Optional session for tracking
            
        Returns:
            Modified request data with context injection
        """
        try:
            # Extract prompt from GPT4All format
            original_prompt = self._extract_prompt(request_data)
            
            if not original_prompt:
                self.logger.debug("No prompt found in request, skipping context injection")
                return request_data
            
            # Get relevant context
            context_result = context_retrieval_service.get_context_for_prompt(
                model_id=model_id,
                user_prompt=original_prompt,
                max_context_length=settings.max_context_length,
            )
            
            if context_result.get("error"):
                self.logger.warning(f"Context retrieval failed: {context_result['error']}")
                return request_data
            
            context_entries = context_result.get("context_entries", [])
            if not context_entries:
                self.logger.debug("No relevant context found")
                return request_data
            
            # Format context using template
            formatted_context = format_context_with_template(
                context_entries=context_entries,
                user_prompt=original_prompt,
                template_name="gpt4all_context"
            )
            
            # Inject context into GPT4All format
            modified_request = request_data.copy()
            
            # GPT4All uses OpenAI-compatible format
            if "messages" in modified_request:
                # Add context as system message
                system_message = {
                    "role": "system",
                    "content": f"Context: {formatted_context}\n\nUser: {original_prompt}"
                }
                modified_request["messages"] = [system_message] + modified_request["messages"]
            else:
                # For completion format, prepend context
                modified_request["prompt"] = f"Context: {formatted_context}\n\nUser: {original_prompt}"
            
            # Log the injection
            self.log_request(
                model_id=model_id,
                request_type="gpt4all_chat",
                success=True,
                context_count=len(context_entries),
                processing_time_ms=context_result.get("processing_time_ms")
            )
            
            return modified_request
            
        except Exception as e:
            self.logger.error(f"Context injection failed: {e}")
            self.log_request(
                model_id=model_id,
                request_type="gpt4all_chat",
                success=False,
                error=str(e)
            )
            return request_data
    
    async def check_model_availability(self, model_id: str) -> bool:
        """Check if a specific model is available in GPT4All."""
        try:
            import httpx
            
            # Check if GPT4All is running
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.endpoint}/v1/models",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    models_data = response.json()
                    available_models = [model.get("id") for model in models_data.get("data", [])]
                    return model_id in available_models
                
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to check model availability: {e}")
            return False
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from GPT4All."""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.endpoint}/v1/models",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    models_data = response.json()
                    return models_data.get("data", [])
                
                return []
                
        except Exception as e:
            self.logger.error(f"Failed to get available models: {e}")
            return []
    
    def extract_model_id(self, request_data: Dict[str, Any]) -> Optional[str]:
        """Extract model ID from GPT4All request."""
        # Check for model in request data
        if "model" in request_data:
            return request_data["model"]
        
        # Check in messages format
        if "messages" in request_data:
            # Look for model in the first message or request metadata
            return request_data.get("model")
        
        return None
    
    def _extract_prompt(self, request_data: Dict[str, Any]) -> Optional[str]:
        """Extract prompt from GPT4All request format."""
        # Check for direct prompt
        if "prompt" in request_data:
            return request_data["prompt"]
        
        # Check for messages format
        if "messages" in request_data and request_data["messages"]:
            # Get the last user message
            for message in reversed(request_data["messages"]):
                if message.get("role") == "user":
                    return message.get("content")
        
        return None


# Global GPT4All integration instance
gpt4all_integration = GPT4AllIntegration()
