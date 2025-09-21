"""Base integration class for AI model integrations."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models import Session as SessionModel

logger = logging.getLogger(__name__)


class BaseIntegration(ABC):
    """Base class for AI model integrations."""
    
    def __init__(self, name: str, host: str, port: int):
        """
        Initialize the integration.
        
        Args:
            name: Name of the integration (e.g., "ollama", "lmstudio")
            host: Host address of the AI service
            port: Port number of the AI service
        """
        self.name = name
        self.host = host
        self.port = port
        self.endpoint = f"http://{host}:{port}"
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def inject_context(
        self,
        request_data: Dict[str, Any],
        model_id: str,
        session: Optional[SessionModel] = None,
    ) -> Dict[str, Any]:
        """
        Inject context into the AI model request.
        
        Args:
            request_data: Original request data
            model_id: AI model identifier
            session: Optional session for tracking
            
        Returns:
            Modified request data with injected context
        """
        pass
    
    @abstractmethod
    async def check_model_availability(self, model_id: str) -> bool:
        """
        Check if a specific model is available.
        
        Args:
            model_id: AI model identifier
            
        Returns:
            True if model is available, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models.
        
        Returns:
            List of model information dictionaries
        """
        pass
    
    @abstractmethod
    def extract_model_id(self, request_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract model ID from request data.
        
        Args:
            request_data: Request data to extract model ID from
            
        Returns:
            Model ID if found, None otherwise
        """
        pass
    
    @abstractmethod
    def format_prompt(
        self,
        original_prompt: str,
        context_entries: List[str],
        template: Optional[str] = None,
    ) -> str:
        """
        Format prompt with injected context.
        
        Args:
            original_prompt: Original user prompt
            context_entries: List of context entries to inject
            template: Optional custom template
            
        Returns:
            Formatted prompt with context
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the integration.
        
        Returns:
            Dictionary with health status information
        """
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.endpoint}/")
                
                if response.status_code == 200:
                    status = "healthy"
                else:
                    status = "degraded"
                
                return {
                    "integration": self.name,
                    "status": status,
                    "endpoint": self.endpoint,
                    "response_code": response.status_code,
                    "available": True,
                }
                
        except Exception as e:
            self.logger.warning(f"Health check failed for {self.name}", exc_info=True)
            return {
                "integration": self.name,
                "status": "unhealthy",
                "endpoint": self.endpoint,
                "error": str(e),
                "available": False,
            }
    
    def get_integration_info(self) -> Dict[str, Any]:
        """
        Get information about this integration.
        
        Returns:
            Dictionary with integration information
        """
        return {
            "name": self.name,
            "type": "ai_model_integration",
            "endpoint": self.endpoint,
            "host": self.host,
            "port": self.port,
            "capabilities": {
                "context_injection": True,
                "model_detection": True,
                "health_check": True,
                "prompt_formatting": True,
            }
        }
    
    def create_session(
        self,
        model_id: str,
        source: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> SessionModel:
        """
        Create a new session for tracking this integration usage.
        
        Args:
            model_id: AI model identifier
            source: Source of the session
            user_id: User ID
            
        Returns:
            New SessionModel instance
        """
        return SessionModel.create_session(
            model_id=model_id,
            session_type="chat",
            source=source or self.name,
            user_id=user_id,
        )
    
    def log_request(
        self,
        model_id: str,
        request_type: str,
        success: bool,
        context_count: int = 0,
        processing_time_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Log integration request for monitoring.
        
        Args:
            model_id: AI model identifier
            request_type: Type of request (generate, chat, etc.)
            success: Whether the request was successful
            context_count: Number of context entries injected
            processing_time_ms: Processing time in milliseconds
            error: Error message if request failed
        """
        log_data = {
            "integration": self.name,
            "model_id": model_id,
            "request_type": request_type,
            "success": success,
            "context_count": context_count,
        }
        
        if processing_time_ms is not None:
            log_data["processing_time_ms"] = processing_time_ms
        
        if error:
            log_data["error"] = error
        
        if success:
            self.logger.info(f"Integration request completed: {log_data}")
        else:
            self.logger.error(f"Integration request failed: {log_data}")
    
    async def proxy_request(
        self,
        path: str,
        method: str,
        headers: Dict[str, str],
        body: Optional[bytes] = None,
        inject_context: bool = True,
    ) -> Dict[str, Any]:
        """
        Proxy a request to the AI service with optional context injection.
        
        Args:
            path: Request path
            method: HTTP method
            headers: Request headers
            body: Request body
            inject_context: Whether to inject context
            
        Returns:
            Dictionary with response data and metadata
        """
        try:
            import httpx
            import json
            
            # Parse request body
            request_data = {}
            if body:
                try:
                    request_data = json.loads(body.decode('utf-8'))
                except json.JSONDecodeError:
                    request_data = {}
            
            # Extract model ID
            model_id = self.extract_model_id(request_data)
            
            # Create session for tracking
            session = None
            session_id = None
            if model_id:
                session = self.create_session(model_id, source=f"{self.name}_proxy")
                session_id = session.id  # Extract ID while session is in context
            
            # Inject context if requested and possible
            if inject_context and model_id and request_data:
                try:
                    print(f"[PROXY DEBUG] About to call inject_context for model {model_id}")
                    print(f"[PROXY DEBUG] Original request_data: {request_data}")
                    request_data = await self.inject_context(request_data, model_id, session)
                    print(f"[PROXY DEBUG] inject_context completed for model {model_id}")
                    print(f"[PROXY DEBUG] Enhanced request_data: {request_data}")
                    body = json.dumps(request_data).encode('utf-8')
                    headers['content-length'] = str(len(body))
                    print(f"[PROXY DEBUG] Body length: {len(body)} bytes")
                except Exception as e:
                    print(f"[PROXY ERROR] Context injection failed: {e}")
                    import traceback
                    print(f"[PROXY ERROR] Traceback: {traceback.format_exc()}")
            else:
                print(f"[PROXY DEBUG] Skipping context injection - inject_context={inject_context}, model_id={model_id}, has_request_data={bool(request_data)}")
            
            # Make request to actual service
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=f"{self.endpoint}{path}",
                    headers=headers,
                    content=body,
                )
                
                # Learn from conversation if successful
                if response.status_code == 200 and session and inject_context:
                    try:
                        self.logger.info(f"Starting conversation learning for model {model_id}")
                        await self._learn_from_conversation(
                            request_data, 
                            response.content, 
                            model_id, 
                            session_id
                        )
                        self.logger.info(f"Conversation learning completed for model {model_id}")
                        
                        # Log AI response to injection debugger
                        try:
                            from ..services.injection_debugger import injection_debugger
                            response_data = json.loads(response.content.decode('utf-8'))
                            ai_response = response_data.get("response", "")
                            if ai_response:
                                injection_debugger.log_ai_response(ai_response)
                        except Exception as debug_error:
                            self.logger.debug(f"Could not log AI response to debugger: {debug_error}")
                            
                    except Exception as e:
                        self.logger.warning(f"Conversation learning failed: {e}")
                        import traceback
                        self.logger.warning(f"Learning error traceback: {traceback.format_exc()}")
                else:
                    self.logger.info(f"Skipping conversation learning: status={response.status_code}, session={bool(session)}, inject_context={inject_context}")
                
                # Complete session tracking
                if session:
                    session.complete_session(
                        success=response.status_code < 400,
                        error_message=None if response.status_code < 400 else f"HTTP {response.status_code}",
                    )
                    
                    # Save session to database
                    from ..database import get_db_context
                    try:
                        with get_db_context() as db:
                            db.add(session)
                            db.commit()
                    except Exception as e:
                        self.logger.warning(f"Failed to save session: {e}")
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response.content,
                    "session_id": session_id,
                }
                
        except Exception as e:
            self.logger.error(f"Proxy request failed: {e}", exc_info=True)
            
            # Complete session with error if it exists
            if session:
                session.complete_session(success=False, error_message=str(e))
                try:
                    from ..database import get_db_context
                    with get_db_context() as db:
                        db.add(session)
                        db.commit()
                except Exception:
                    pass
            
            raise
    
    async def _learn_from_conversation(
        self,
        request_data: Dict[str, Any],
        response_content: bytes,
        model_id: str,
        session_id: Optional[str]
    ) -> None:
        """Learn from conversation by extracting context from prompts and responses."""
        try:
            from ..services.conversation_learning import conversation_learning_service
            
            # Extract user prompt
            user_prompt = self._extract_user_prompt(request_data)
            if not user_prompt:
                return
            
            # Extract AI response
            ai_response = ""
            try:
                response_data = json.loads(response_content.decode('utf-8'))
                
                # Handle streaming response
                if isinstance(response_data, list):
                    # Concatenate all response chunks
                    ai_response = "".join([chunk.get("response", "") for chunk in response_data])
                elif isinstance(response_data, dict):
                    ai_response = response_data.get("response", "")
                    
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Try to extract text from raw response
                try:
                    ai_response = response_content.decode('utf-8')
                except UnicodeDecodeError:
                    return
            
            if not ai_response:
                return
            
            # Start or get conversation session
            from ..services.conversation_logger import conversation_logger
            from ..services.context_extractor import context_extractor
            from ..services.deduplication import context_deduplicator
            from ..services.validation import context_validator
            from ..services.vault import vault_service
            from ..database import get_db_context
            
            if session_id:
                # Try to get existing conversation
                conversation = conversation_logger.get_conversation(session_id)
                if not conversation:
                    # Create new conversation if session_id doesn't exist
                    conversation_id = conversation_logger.start_conversation(model_id)
                else:
                    conversation_id = session_id
            else:
                conversation_id = conversation_logger.start_conversation(model_id)
            
            # Log the conversation
            conversation_logger.log_user_message(conversation_id, user_prompt)
            conversation_logger.log_assistant_message(conversation_id, ai_response)
            
            # Get the conversation for context extraction
            conversation = conversation_logger.get_conversation(conversation_id)
            if conversation:
                # Extract context from the conversation
                extracted_contexts = context_extractor.extract_from_conversation(
                    conversation_id, conversation
                )
                
                if extracted_contexts:
                    # Get existing contexts for deduplication
                    with get_db_context() as db:
                        from ..models.context import ContextEntry
                        existing_contexts = db.query(ContextEntry).all()
                    
                    # Deduplicate extracted contexts
                    deduplicated_contexts = context_deduplicator.deduplicate_extracted_context(
                        extracted_contexts, existing_contexts
                    )
                    
                    # Validate extracted contexts
                    validation_results = context_validator.validate_context_batch(deduplicated_contexts)
                    
                    # Save valid contexts
                    saved_count = 0
                    for i, context in enumerate(deduplicated_contexts):
                        validation_result = validation_results[i]
                        
                        # Save contexts that are valid, need review, or uncertain (but not invalid)
                        if validation_result.status.value in ['valid', 'needs_review', 'uncertain']:
                            try:
                                # Save to database
                                with get_db_context() as db:
                                    context_entry = ContextEntry(
                                        content=context.content,
                                        context_type=context.context_type,
                                        source=context.source,
                                        tags=context.tags,
                                        entry_metadata={
                                            'conversation_id': context.conversation_id,
                                            'message_id': context.message_id,
                                            'extraction_confidence': context.confidence.value,
                                            'validation_status': validation_result.status.value,
                                            'validation_confidence': validation_result.confidence,
                                            'auto_extracted': True,
                                            **context.metadata
                                        }
                                    )
                                    db.add(context_entry)
                                    db.commit()
                                    saved_count += 1
                                    
                            except Exception as e:
                                self.logger.warning(f"Failed to save extracted context: {e}")
                    
                    if saved_count > 0:
                        self.logger.info(f"Automatically extracted and saved {saved_count} context entries from conversation")
            
        except Exception as e:
            self.logger.warning(f"Failed to learn from conversation: {e}")
    
    def _extract_user_prompt(self, request_data: Dict[str, Any]) -> Optional[str]:
        """Extract user prompt from request data."""
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
    
    def __str__(self) -> str:
        """String representation of the integration."""
        return f"{self.name.title()}Integration({self.endpoint})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the integration."""
        return f"{self.__class__.__name__}(name='{self.name}', host='{self.host}', port={self.port})"
