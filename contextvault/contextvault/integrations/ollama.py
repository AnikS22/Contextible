"""Ollama integration for ContextVault."""

import json
import logging
from typing import Any, Dict, List, Optional

from .base import BaseIntegration
from ..models import Session as SessionModel
from ..services import context_retrieval_service
from ..config import settings
from ..services.templates import template_manager, format_context_with_template
from ..services.conversation_logger import conversation_logger
from ..services.context_extractor import context_extractor
from ..services.deduplication import context_deduplicator
from ..services.validation import context_validator
from ..database import get_db_context
from ..services.vault import vault_service

logger = logging.getLogger(__name__)


class OllamaIntegration(BaseIntegration):
    """Integration for Ollama AI models."""
    
    def __init__(self, host: str = None, port: int = None):
        """
        Initialize Ollama integration.
        
        Args:
            host: Ollama host (defaults to config)
            port: Ollama port (defaults to config)
        """
        host = host or settings.ollama_host
        port = port or settings.ollama_port
        super().__init__(name="ollama", host=host, port=port)
    
    async def inject_context(
        self,
        request_data: Dict[str, Any],
        model_id: str,
        session: Optional[SessionModel] = None,
    ) -> Dict[str, Any]:
        """
        Inject context into Ollama request.
        
        Supports both /api/generate and /api/chat endpoints.
        
        Args:
            request_data: Original Ollama request data
            model_id: Model identifier
            session: Optional session for tracking
            
        Returns:
            Modified request data with context injection
        """
        # Import debugging services
        from ..services.injection_debugger import injection_debugger
        from ..services.injection_monitor import injection_monitor
        
        try:
            print(f"[INJECTION DEBUG] Starting injection for model {model_id}")
            print(f"[INJECTION DEBUG] Request data: {request_data}")
            
            # Determine request type and extract prompt
            original_prompt = self._extract_prompt(request_data)
            print(f"[INJECTION DEBUG] Extracted prompt: {original_prompt}")
            
            if not original_prompt:
                print(f"[INJECTION DEBUG] No prompt found, skipping injection")
                self.logger.debug("No prompt found in request, skipping context injection")
                return request_data
            
            # Start injection debugging
            injection_id = injection_debugger.start_injection_debug(model_id, original_prompt)
            injection_monitor.log_event("start", model_id, {
                "original_prompt": original_prompt,
                "request_type": "generate" if "prompt" in request_data else "chat"
            }, injection_id)
            
            # Get relevant context with session management
            from ..database import get_db_context
            from ..services.context_retrieval import ContextRetrievalService
            from ..models.context import ContextEntry
            
            with get_db_context() as db:
                # DEBUG: Check what's in the database
                total_entries = db.query(ContextEntry).count()
                print(f"[INJECTION DEBUG] Total entries in database session: {total_entries}")
                
                session_retrieval_service = ContextRetrievalService(db_session=db)
                print(f"[INJECTION DEBUG] max_context_length: {settings.max_context_length}")
                print(f"[INJECTION DEBUG] user_prompt: {original_prompt}")
                print(f"[INJECTION DEBUG] model_id: {model_id}")
                
                context_result = session_retrieval_service.get_context_for_prompt(
                    model_id=model_id,
                    user_prompt=original_prompt,
                    max_context_length=settings.max_context_length,
                )
            
            if context_result.get("error"):
                print(f"[INJECTION DEBUG] Context retrieval error: {context_result['error']}")
                self.logger.warning(f"Context retrieval failed for model {model_id}: {context_result['error']}")
                injection_debugger.complete_injection_debug(False, context_result['error'])
                return request_data
            
            context_entries = context_result.get("context_entries", [])
            relevance_scores = context_result.get("relevance_scores", {})
            print(f"[INJECTION DEBUG] Context retrieval result: {len(context_entries)} entries found")
            print(f"[INJECTION DEBUG] Context result keys: {list(context_result.keys())}")
            if context_entries:
                print(f"[INJECTION DEBUG] First context entry: {context_entries[0]}")
            
            # Log context retrieval
            injection_debugger.log_context_retrieval(context_entries, relevance_scores)
            injection_monitor.log_event("context_retrieved", model_id, {
                "contexts_found": len(context_entries),
                "relevance_scores": relevance_scores
            }, injection_id)
            
            if not context_entries:
                print(f"[INJECTION DEBUG] No relevant context found for model {model_id}, returning original request")
                self.logger.debug(f"No relevant context found for model {model_id}")
                injection_debugger.complete_injection_debug(True, "No context found")
                return request_data
            
            # Get current template
            current_template = template_manager.get_template()
            template_name = current_template.name if current_template else "default"
            template_content = current_template.template if current_template else "No template"
            
            # Log template selection
            injection_debugger.log_template_selection(template_name, template_content)
            injection_monitor.log_event("template_selected", model_id, {
                "template_name": template_name,
                "template_content": template_content
            }, injection_id)
            
            # Format context for injection using our enhanced template system
            context_strings = [entry.get('content', str(entry)) if isinstance(entry, dict) else (entry.content if hasattr(entry, 'content') else str(entry)) for entry in context_entries]
            formatted_context = self.format_prompt(
                original_prompt=original_prompt,
                context_entries=context_strings,
                template_name=None  # Uses current template from template_manager
            )
            
            # Log context formatting
            injection_debugger.log_context_formatting(formatted_context, context_entries)
            injection_monitor.log_event("context_formatted", model_id, {
                "formatted_context_length": len(formatted_context),
                "context_entries_count": len(context_entries)
            }, injection_id)
            
            # Inject context into request
            modified_request = self._inject_into_request(request_data, formatted_context)
            final_prompt = self._extract_prompt(modified_request)
            
            # DEBUG: Log the enhancement
            self.logger.info(f"DEBUG: Context injection successful!")
            self.logger.info(f"DEBUG: Original prompt length: {len(original_prompt)}")
            self.logger.info(f"DEBUG: Enhanced prompt length: {len(final_prompt)}")
            self.logger.info(f"DEBUG: Enhanced prompt preview: {final_prompt[:200]}...")
            
            # Log prompt assembly
            injection_debugger.log_prompt_assembly(final_prompt)
            injection_monitor.log_event("prompt_assembled", model_id, {
                "original_prompt_length": len(original_prompt),
                "final_prompt_length": len(final_prompt),
                "context_added": len(final_prompt) - len(original_prompt)
            }, injection_id)
            
            # Track context usage in session
            if session:
                for entry_data in context_entries:
                    session.add_context_entry(entry_data)
                
                session.original_prompt = original_prompt
                session.final_prompt = final_prompt
                session.total_context_length = context_result.get("total_length", 0)
            
            self.logger.info(f"Context injected successfully for model {model_id}: {len(context_entries)} entries, {context_result.get('total_length', 0)} chars")
            
            # DEBUG: Log the final result
            print(f"[INJECTION DEBUG] Final modified_request: {modified_request}")
            print(f"[INJECTION DEBUG] Final prompt: {self._extract_prompt(modified_request)}")
            
            return modified_request
            
        except Exception as e:
            print(f"[INJECTION ERROR] Context injection failed: {str(e)}")
            import traceback
            print(f"[INJECTION ERROR] Traceback: {traceback.format_exc()}")
            
            self.logger.error(f"Context injection failed for model {model_id}: {str(e)}", exc_info=True)
            injection_debugger.complete_injection_debug(False, str(e))
            injection_monitor.log_event("injection_failed", model_id, {
                "error": str(e)
            }, injection_id if 'injection_id' in locals() else None)
            # Return original request if injection fails
            return request_data
    
    def _extract_prompt(self, request_data: Dict[str, Any]) -> Optional[str]:
        """Extract prompt from Ollama request data."""
        
        # /api/generate endpoint
        if "prompt" in request_data:
            return request_data["prompt"]
        
        # /api/chat endpoint
        if "messages" in request_data:
            messages = request_data["messages"]
            if messages and isinstance(messages, list):
                # Get the last user message
                for message in reversed(messages):
                    if isinstance(message, dict) and message.get("role") == "user":
                        return message.get("content", "")
        
        return None
    
    def _inject_into_request(
        self,
        request_data: Dict[str, Any],
        formatted_context: str,
    ) -> Dict[str, Any]:
        """Inject formatted context into Ollama request."""
        
        modified_request = request_data.copy()
        
        # /api/generate endpoint
        if "prompt" in modified_request:
            modified_request["prompt"] = formatted_context
            return modified_request
        
        # /api/chat endpoint
        if "messages" in modified_request:
            messages = modified_request["messages"].copy() if modified_request["messages"] else []
            
            if messages:
                # Find the last user message and inject context
                for i in range(len(messages) - 1, -1, -1):
                    if messages[i].get("role") == "user":
                        # Create context-injected message
                        original_content = messages[i].get("content", "")
                        
                        # Use the formatted context which already includes the original prompt
                        messages[i] = {
                            **messages[i],
                            "content": formatted_context
                        }
                        break
            else:
                # No messages, create a user message with context
                messages = [{
                    "role": "user",
                    "content": formatted_context
                }]
            
            modified_request["messages"] = messages
            return modified_request
        
        # Unknown format, return as-is
        self.logger.warning("Unknown Ollama request format, cannot inject context")
        return modified_request
    
    async def check_model_availability(self, model_id: str) -> bool:
        """Check if a model is available in Ollama."""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.endpoint}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    
                    # Check if model exists in the list
                    for model in models:
                        if model.get("name") == model_id:
                            return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to check model availability: {e}")
            return False
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from Ollama."""
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.endpoint}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    
                    # Format model information
                    formatted_models = []
                    for model in models:
                        formatted_models.append({
                            "id": model.get("name"),
                            "name": model.get("name"),
                            "size": model.get("size"),
                            "modified_at": model.get("modified_at"),
                            "digest": model.get("digest"),
                            "details": model.get("details", {}),
                        })
                    
                    return formatted_models
                else:
                    self.logger.warning(f"Failed to get models: HTTP {response.status_code}")
                    return []
                
        except Exception as e:
            self.logger.error(f"Failed to get available models: {e}")
            return []
    
    def extract_model_id(self, request_data: Dict[str, Any]) -> Optional[str]:
        """Extract model ID from Ollama request data."""
        return request_data.get("model")
    
    def format_prompt(
        self,
        original_prompt: str,
        context_entries: List[str],
        template_name: Optional[str] = None,
    ) -> str:
        """Format prompt with context for Ollama using enhanced templates."""
        
        # Use the new template system
        formatted_prompt = format_context_with_template(
            context_entries=context_entries,
            user_prompt=original_prompt,
            template_name=template_name
        )
        
        # Log the template being used for debugging
        current_template = template_manager.get_template(template_name)
        logger.info(f"Using template: {current_template.name} (strength: {current_template.strength}/10)")
        logger.debug(f"Context entries: {len(context_entries)}")
        logger.debug(f"Original prompt: {original_prompt}")
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")
        
        # Optional: Log the full formatted prompt for debugging (be careful with sensitive data)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Full formatted prompt:\n{formatted_prompt}")
        
        return formatted_prompt
    
    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """
        Pull a model in Ollama.
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            Dictionary with operation status
        """
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=300.0) as client:  # Long timeout for model pulls
                response = await client.post(
                    f"{self.endpoint}/api/pull",
                    json={"name": model_name},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "model": model_name,
                        "message": f"Model {model_name} pulled successfully"
                    }
                else:
                    return {
                        "success": False,
                        "model": model_name,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "model": model_name,
                "error": str(e)
            }
    
    async def generate_response(
        self,
        model_id: str,
        prompt: str,
        inject_context: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response using Ollama with optional context injection.
        
        Args:
            model_id: Model to use for generation
            prompt: User prompt
            inject_context: Whether to inject context
            **kwargs: Additional parameters for Ollama
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            import httpx
            
            # Prepare request
            request_data = {
                "model": model_id,
                "prompt": prompt,
                **kwargs
            }
            
            # Inject context if requested
            if inject_context:
                session = self.create_session(model_id, source="direct_generate")
                request_data = await self.inject_context(request_data, model_id, session)
            
            # Make request to Ollama
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.endpoint}/api/generate",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "response": data.get("response", ""),
                        "model": data.get("model"),
                        "created_at": data.get("created_at"),
                        "done": data.get("done"),
                        "context_injected": inject_context,
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "context_injected": inject_context,
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "context_injected": inject_context,
            }
    
    async def chat(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        inject_context: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Chat with Ollama model with optional context injection.
        
        Args:
            model_id: Model to use for chat
            messages: List of chat messages
            inject_context: Whether to inject context
            **kwargs: Additional parameters for Ollama
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            import httpx
            
            # Prepare request
            request_data = {
                "model": model_id,
                "messages": messages,
                **kwargs
            }
            
            # Inject context if requested
            if inject_context:
                session = self.create_session(model_id, source="direct_chat")
                request_data = await self.inject_context(request_data, model_id, session)
            
            # Make request to Ollama
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.endpoint}/api/chat",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "message": data.get("message", {}),
                        "model": data.get("model"),
                        "created_at": data.get("created_at"),
                        "done": data.get("done"),
                        "context_injected": inject_context,
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "context_injected": inject_context,
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "context_injected": inject_context,
            }


# Global Ollama integration instance
ollama_integration = OllamaIntegration()
