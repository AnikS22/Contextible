"""
ContextVault Pipeline Debugger

Provides detailed logging and debugging tools for the context injection pipeline.
Shows exactly what context is retrieved, how it's formatted, and what's sent to AI models.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session

from ..models.context import ContextEntry
from ..database import get_db_context
from .context_retrieval import ContextRetrievalService
from .semantic_search import get_semantic_search_service

logger = logging.getLogger(__name__)


@dataclass
class PipelineStep:
    """Represents a step in the context injection pipeline."""
    step_name: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    duration_ms: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ContextInjectionDebugInfo:
    """Complete debug information for a context injection request."""
    request_id: str
    model_id: str
    user_prompt: str
    pipeline_steps: List[PipelineStep]
    final_prompt: str
    context_entries_used: List[Dict[str, Any]]
    total_duration_ms: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


class ContextPipelineDebugger:
    """Debugger for the context injection pipeline."""
    
    def __init__(self, enable_debug_logging: bool = True):
        self.enable_debug_logging = enable_debug_logging
        self.debug_sessions: List[ContextInjectionDebugInfo] = []
        self.max_sessions = 100  # Keep last 100 debug sessions
        
        if self.enable_debug_logging:
            self._setup_debug_logging()
    
    def _setup_debug_logging(self):
        """Setup detailed debug logging."""
        # Create debug logger
        debug_logger = logging.getLogger('contextvault.debug')
        debug_logger.setLevel(logging.DEBUG)
        
        # Create file handler for debug logs
        from pathlib import Path
        log_dir = Path.home() / ".contextvault" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        debug_handler = logging.FileHandler(log_dir / "context_pipeline_debug.log")
        debug_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        debug_handler.setFormatter(formatter)
        
        debug_logger.addHandler(debug_handler)
        
        self.debug_logger = debug_logger
    
    def debug_context_injection(
        self,
        model_id: str,
        user_prompt: str,
        max_context_length: Optional[int] = None,
        context_template: Optional[str] = None
    ) -> ContextInjectionDebugInfo:
        """
        Debug a complete context injection request with detailed logging.
        
        Returns:
            Complete debug information about the context injection process
        """
        request_id = f"debug_{int(time.time() * 1000)}"
        start_time = time.time()
        pipeline_steps = []
        
        debug_info = ContextInjectionDebugInfo(
            request_id=request_id,
            model_id=model_id,
            user_prompt=user_prompt,
            pipeline_steps=[],
            final_prompt="",
            context_entries_used=[],
            total_duration_ms=0,
            timestamp=datetime.now(),
            success=False
        )
        
        try:
            if self.enable_debug_logging:
                self.debug_logger.info(f"Starting context injection debug for request {request_id}")
                self.debug_logger.info(f"Model: {model_id}, Prompt: {user_prompt[:100]}...")
            
            # Step 1: Context Retrieval
            step_start = time.time()
            with get_db_context() as db:
                retrieval_service = ContextRetrievalService(db_session=db)
                
                entries, metadata = retrieval_service.get_relevant_context(
                    model_id=model_id,
                    query_context=user_prompt,
                    limit=10
                )
            
            step_duration = (time.time() - step_start) * 1000
            
            # Extract context data while session is active
            context_entries_data = []
            for entry in entries:
                context_entries_data.append({
                    "id": entry.id,
                    "content": entry.content,
                    "context_type": entry.context_type.value,
                    "tags": entry.tags,
                    "source": entry.source,
                    "created_at": entry.created_at.isoformat(),
                    "access_count": entry.access_count,
                    "relevance_score": getattr(entry, 'relevance_score', 0.0)
                })
            
            pipeline_steps.append(PipelineStep(
                step_name="context_retrieval",
                input_data={
                    "model_id": model_id,
                    "query": user_prompt,
                    "limit": 10
                },
                output_data={
                    "entries_found": len(entries),
                    "metadata": metadata,
                    "context_entries": context_entries_data
                },
                duration_ms=step_duration,
                timestamp=datetime.now(),
                metadata={"retrieval_method": "semantic_search"}
            ))
            
            if self.enable_debug_logging:
                self.debug_logger.info(f"Retrieved {len(entries)} context entries in {step_duration:.2f}ms")
                for i, entry in enumerate(entries):
                    self.debug_logger.debug(f"  Entry {i+1}: [{entry.context_type}] {entry.content[:100]}...")
            
            # Step 2: Template Selection and Context Formatting
            step_start = time.time()
            
            from .templates import template_manager, format_context_with_template
            
            # Get context strings for template formatting
            context_strings = [entry.content for entry in entries]
            
            # Format with template
            formatted_prompt = format_context_with_template(
                context_entries=context_strings,
                user_prompt=user_prompt,
                template_name=context_template
            )
            
            step_duration = (time.time() - step_start) * 1000
            
            pipeline_steps.append(PipelineStep(
                step_name="template_formatting",
                input_data={
                    "context_entries": context_strings,
                    "user_prompt": user_prompt,
                    "template_name": context_template
                },
                output_data={
                    "formatted_prompt": formatted_prompt,
                    "template_used": template_manager.get_active_template().name,
                    "context_strings_count": len(context_strings)
                },
                duration_ms=step_duration,
                timestamp=datetime.now(),
                metadata={"template_strength": template_manager.get_active_template().strength}
            ))
            
            if self.enable_debug_logging:
                self.debug_logger.info(f"Formatted prompt using template '{template_manager.get_active_template().name}' in {step_duration:.2f}ms")
                self.debug_logger.debug(f"Final prompt length: {len(formatted_prompt)} characters")
                self.debug_logger.debug(f"Final prompt preview: {formatted_prompt[:200]}...")
            
            # Step 3: Semantic Search Debug (if available)
            semantic_service = get_semantic_search_service()
            if semantic_service.is_available():
                step_start = time.time()
                
                # Get semantic search details
                semantic_results = semantic_service.search_with_hybrid_scoring(
                    query=user_prompt,
                    db_session=db,
                    max_results=10
                )
                
                step_duration = (time.time() - step_start) * 1000
                
                semantic_debug_data = {
                    "semantic_search_available": True,
                    "results_count": len(semantic_results),
                    "cache_stats": semantic_service.get_cache_stats()
                }
                
                if semantic_results:
                    semantic_debug_data["top_results"] = [
                        {
                            "entry_id": result[0].id,
                            "similarity_score": result[1],
                            "score_breakdown": result[2] if len(result) > 2 else {}
                        }
                        for result in semantic_results[:3]
                    ]
                
                pipeline_steps.append(PipelineStep(
                    step_name="semantic_search_debug",
                    input_data={"query": user_prompt},
                    output_data=semantic_debug_data,
                    duration_ms=step_duration,
                    timestamp=datetime.now(),
                    metadata={"fallback_mode": semantic_service.get_cache_stats().get("fallback_mode", False)}
                ))
                
                if self.enable_debug_logging:
                    self.debug_logger.info(f"Semantic search completed in {step_duration:.2f}ms")
                    self.debug_logger.debug(f"Semantic search results: {len(semantic_results)} entries found")
            
            # Update debug info
            debug_info.pipeline_steps = pipeline_steps
            debug_info.final_prompt = formatted_prompt
            debug_info.context_entries_used = context_entries_data
            debug_info.total_duration_ms = (time.time() - start_time) * 1000
            debug_info.success = True
            
            if self.enable_debug_logging:
                self.debug_logger.info(f"Context injection completed successfully for request {request_id} in {debug_info.total_duration_ms:.2f}ms")
            
        except Exception as e:
            debug_info.error_message = str(e)
            debug_info.total_duration_ms = (time.time() - start_time) * 1000
            
            if self.enable_debug_logging:
                self.debug_logger.error(f"Context injection failed for request {request_id}: {e}")
                import traceback
                self.debug_logger.error(traceback.format_exc())
        
        # Store debug session
        self.debug_sessions.append(debug_info)
        if len(self.debug_sessions) > self.max_sessions:
            self.debug_sessions.pop(0)  # Remove oldest session
        
        return debug_info
    
    def get_recent_debug_sessions(self, limit: int = 10) -> List[ContextInjectionDebugInfo]:
        """Get recent debug sessions."""
        return self.debug_sessions[-limit:]
    
    def get_debug_session(self, request_id: str) -> Optional[ContextInjectionDebugInfo]:
        """Get a specific debug session by request ID."""
        for session in self.debug_sessions:
            if session.request_id == request_id:
                return session
        return None
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get statistics about the context injection pipeline."""
        if not self.debug_sessions:
            return {"error": "No debug sessions available"}
        
        successful_sessions = [s for s in self.debug_sessions if s.success]
        failed_sessions = [s for s in self.debug_sessions if not s.success]
        
        # Calculate averages
        avg_duration = sum(s.total_duration_ms for s in successful_sessions) / len(successful_sessions) if successful_sessions else 0
        avg_context_entries = sum(len(s.context_entries_used) for s in successful_sessions) / len(successful_sessions) if successful_sessions else 0
        
        # Template usage statistics
        template_usage = {}
        for session in successful_sessions:
            for step in session.pipeline_steps:
                if step.step_name == "template_formatting":
                    template_name = step.output_data.get("template_used", "unknown")
                    template_usage[template_name] = template_usage.get(template_name, 0) + 1
        
        # Context type usage
        context_type_usage = {}
        for session in successful_sessions:
            for entry in session.context_entries_used:
                context_type = entry.get("context_type", "unknown")
                context_type_usage[context_type] = context_type_usage.get(context_type, 0) + 1
        
        return {
            "total_sessions": len(self.debug_sessions),
            "successful_sessions": len(successful_sessions),
            "failed_sessions": len(failed_sessions),
            "success_rate": len(successful_sessions) / len(self.debug_sessions) if self.debug_sessions else 0,
            "average_duration_ms": avg_duration,
            "average_context_entries_per_request": avg_context_entries,
            "template_usage": template_usage,
            "context_type_usage": context_type_usage,
            "recent_errors": [s.error_message for s in failed_sessions[-5:] if s.error_message],
            "last_updated": datetime.now().isoformat()
        }
    
    def export_debug_report(self, filename: Optional[str] = None) -> str:
        """Export a detailed debug report."""
        import json
        from pathlib import Path
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"contextvault_debug_report_{timestamp}.json"
        
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "statistics": self.get_pipeline_statistics(),
            "recent_sessions": [
                {
                    "request_id": session.request_id,
                    "model_id": session.model_id,
                    "user_prompt": session.user_prompt,
                    "success": session.success,
                    "total_duration_ms": session.total_duration_ms,
                    "context_entries_used": len(session.context_entries_used),
                    "timestamp": session.timestamp.isoformat(),
                    "error_message": session.error_message
                }
                for session in self.debug_sessions[-10:]  # Last 10 sessions
            ]
        }
        
        filepath = Path(filename)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return str(filepath.absolute())


# Global debugger instance
_debugger_instance = None


def get_debugger() -> ContextPipelineDebugger:
    """Get the global pipeline debugger instance."""
    global _debugger_instance
    
    if _debugger_instance is None:
        _debugger_instance = ContextPipelineDebugger()
    
    return _debugger_instance


def debug_context_injection(
    model_id: str,
    user_prompt: str,
    max_context_length: Optional[int] = None,
    context_template: Optional[str] = None
) -> ContextInjectionDebugInfo:
    """
    Convenience function to debug context injection.
    
    This is the main function to call when you want to debug
    the context injection pipeline for a specific request.
    """
    debugger = get_debugger()
    return debugger.debug_context_injection(
        model_id=model_id,
        user_prompt=user_prompt,
        max_context_length=max_context_length,
        context_template=context_template
    )
