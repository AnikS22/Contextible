"""
Context Injection Debugger
Provides complete visibility into the context injection pipeline
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from ..models.context import ContextEntry
from ..database import get_db_context


@dataclass
class InjectionStep:
    """A single step in the context injection pipeline."""
    step_name: str
    timestamp: float
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    duration_ms: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class ContextInjectionLog:
    """Complete log of a context injection operation."""
    injection_id: str
    timestamp: float
    model_id: str
    original_prompt: str
    final_prompt: str
    context_entries_retrieved: List[Dict[str, Any]]
    context_entries_injected: List[Dict[str, Any]]
    relevance_scores: Dict[str, float]
    template_used: str
    injection_successful: bool
    steps: List[InjectionStep]
    ai_response: Optional[str] = None
    response_analysis: Optional[Dict[str, Any]] = None


class ContextInjectionDebugger:
    """Debugger for context injection pipeline."""
    
    def __init__(self):
        self.logs_dir = Path("./injection_logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.active_injection = None
        self.injection_logs = []
    
    def start_injection_debug(self, model_id: str, original_prompt: str) -> str:
        """Start debugging a new context injection."""
        injection_id = f"injection_{int(time.time() * 1000)}"
        
        self.active_injection = ContextInjectionLog(
            injection_id=injection_id,
            timestamp=time.time(),
            model_id=model_id,
            original_prompt=original_prompt,
            final_prompt="",
            context_entries_retrieved=[],
            context_entries_injected=[],
            relevance_scores={},
            template_used="",
            injection_successful=False,
            steps=[]
        )
        
        self._log_step("injection_start", {
            "model_id": model_id,
            "original_prompt": original_prompt
        }, {
            "injection_id": injection_id
        })
        
        return injection_id
    
    def log_context_retrieval(self, retrieved_contexts: List[ContextEntry], relevance_scores: Dict[str, float]):
        """Log context retrieval step."""
        context_data = []
        for ctx in retrieved_contexts:
            try:
                # Handle both dict and ContextEntry objects
                if isinstance(ctx, dict):
                    context_data.append(ctx)
                else:
                    # For ContextEntry objects, extract data before session closes
                    context_data.append({
                        "id": str(ctx.id) if hasattr(ctx, 'id') else 'unknown',
                        "content": ctx.content if hasattr(ctx, 'content') else str(ctx),
                        "type": str(ctx.context_type) if hasattr(ctx, 'context_type') else 'unknown',
                        "source": ctx.source if hasattr(ctx, 'source') else 'unknown',
                        "tags": ctx.tags if hasattr(ctx, 'tags') else [],
                        "created_at": ctx.created_at.isoformat() if hasattr(ctx, 'created_at') and ctx.created_at else None
                    })
            except Exception as e:
                context_data.append({
                    "error": f"Could not serialize context: {e}",
                    "id": "unknown"
                })
        
        self.active_injection.context_entries_retrieved = context_data
        self.active_injection.relevance_scores = relevance_scores
        
        self._log_step("context_retrieval", {
            "query": self.active_injection.original_prompt,
            "model_id": self.active_injection.model_id
        }, {
            "contexts_found": len(context_data),
            "relevance_scores": relevance_scores,
            "context_details": context_data
        })
    
    def log_template_selection(self, template_name: str, template_content: str):
        """Log template selection step."""
        self.active_injection.template_used = template_name
        
        self._log_step("template_selection", {
            "available_templates": self._get_available_templates()
        }, {
            "selected_template": template_name,
            "template_content": template_content
        })
    
    def log_context_formatting(self, formatted_context: str, injected_contexts: List[ContextEntry]):
        """Log context formatting step."""
        injected_data = []
        for ctx in injected_contexts:
            try:
                injected_data.append({
                    "id": ctx.id,
                    "content": ctx.content,
                    "type": str(ctx.context_type),
                    "source": ctx.source
                })
            except Exception as e:
                injected_data.append({
                    "error": f"Could not serialize context: {e}"
                })
        
        self.active_injection.context_entries_injected = injected_data
        
        self._log_step("context_formatting", {
            "template_used": self.active_injection.template_used,
            "context_count": len(injected_contexts)
        }, {
            "formatted_context": formatted_context,
            "injected_contexts": injected_data
        })
    
    def log_prompt_assembly(self, final_prompt: str):
        """Log final prompt assembly step."""
        self.active_injection.final_prompt = final_prompt
        
        self._log_step("prompt_assembly", {
            "original_prompt": self.active_injection.original_prompt,
            "formatted_context": "See context_formatting step"
        }, {
            "final_prompt": final_prompt,
            "prompt_length": len(final_prompt),
            "context_injected": len(self.active_injection.context_entries_injected) > 0
        })
    
    def log_ai_response(self, ai_response: str):
        """Log AI response and analyze context usage."""
        self.active_injection.ai_response = ai_response
        
        # Analyze response for context usage
        response_analysis = self._analyze_response_context_usage(ai_response)
        self.active_injection.response_analysis = response_analysis
        
        self._log_step("ai_response", {
            "response_length": len(ai_response)
        }, {
            "ai_response": ai_response,
            "context_usage_analysis": response_analysis
        })
    
    def complete_injection_debug(self, success: bool, error_message: Optional[str] = None):
        """Complete the injection debugging session."""
        if self.active_injection:
            self.active_injection.injection_successful = success
            
            # Add final step
            self._log_step("injection_complete", {
                "success": success,
                "total_steps": len(self.active_injection.steps)
            }, {
                "final_status": "success" if success else "failed",
                "error_message": error_message,
                "summary": self._generate_injection_summary()
            })
            
            # Save log
            self._save_injection_log(self.active_injection)
            self.injection_logs.append(self.active_injection)
            
            # Reset active injection
            self.active_injection = None
    
    def _log_step(self, step_name: str, input_data: Dict[str, Any], output_data: Dict[str, Any]):
        """Log a single step in the injection pipeline."""
        if not self.active_injection:
            return
        
        step = InjectionStep(
            step_name=step_name,
            timestamp=time.time(),
            input_data=input_data,
            output_data=output_data,
            duration_ms=0.0,  # We'll calculate this if needed
            success=True
        )
        
        self.active_injection.steps.append(step)
    
    def _analyze_response_context_usage(self, response: str) -> Dict[str, Any]:
        """Analyze AI response for evidence of context usage."""
        analysis = {
            "response_length": len(response),
            "mentions_user_info": False,
            "mentions_specific_details": False,
            "context_keywords_found": [],
            "personalization_score": 0.0,
            "evidence_of_context_usage": []
        }
        
        if not self.active_injection:
            return analysis
        
        # Check for mentions of user information from injected context
        for ctx_data in self.active_injection.context_entries_injected:
            content = ctx_data.get("content", "").lower()
            if content and any(keyword in response.lower() for keyword in content.split()[:3]):
                analysis["mentions_user_info"] = True
                analysis["evidence_of_context_usage"].append(f"Mentions content from context: {content[:50]}...")
        
        # Check for personalization indicators
        personal_indicators = ["you", "your", "you're", "you've", "i know", "as you", "given that you"]
        personal_mentions = sum(1 for indicator in personal_indicators if indicator in response.lower())
        analysis["personalization_score"] = min(1.0, personal_mentions / 5.0)
        
        # Check for specific details that wouldn't be in generic responses
        specific_indicators = ["specifically", "in particular", "as you mentioned", "based on", "considering"]
        analysis["mentions_specific_details"] = any(indicator in response.lower() for indicator in specific_indicators)
        
        return analysis
    
    def _generate_injection_summary(self) -> Dict[str, Any]:
        """Generate a summary of the injection process."""
        if not self.active_injection:
            return {}
        
        return {
            "total_steps": len(self.active_injection.steps),
            "context_entries_retrieved": len(self.active_injection.context_entries_retrieved),
            "context_entries_injected": len(self.active_injection.context_entries_injected),
            "template_used": self.active_injection.template_used,
            "injection_successful": self.active_injection.injection_successful,
            "prompt_length_change": len(self.active_injection.final_prompt) - len(self.active_injection.original_prompt),
            "has_context": len(self.active_injection.context_entries_injected) > 0
        }
    
    def _get_available_templates(self) -> List[str]:
        """Get list of available templates."""
        try:
            from .templates import template_manager
            return template_manager.get_all_templates_names()
        except:
            return ["unknown"]
    
    def _save_injection_log(self, log: ContextInjectionLog):
        """Save injection log to file."""
        try:
            log_file = self.logs_dir / f"{log.injection_id}.json"
            with open(log_file, 'w') as f:
                json.dump(asdict(log), f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save injection log: {e}")
    
    def get_recent_injections(self, limit: int = 10) -> List[ContextInjectionLog]:
        """Get recent injection logs."""
        return self.injection_logs[-limit:]
    
    def get_injection_stats(self) -> Dict[str, Any]:
        """Get statistics about injections."""
        if not self.injection_logs:
            return {
                "total_injections": 0,
                "successful_injections": 0,
                "success_rate": 0.0,
                "average_context_entries": 0.0,
                "templates_used": {}
            }
        
        total = len(self.injection_logs)
        successful = sum(1 for log in self.injection_logs if log.injection_successful)
        avg_context = sum(len(log.context_entries_injected) for log in self.injection_logs) / total
        
        template_usage = {}
        for log in self.injection_logs:
            template = log.template_used
            template_usage[template] = template_usage.get(template, 0) + 1
        
        return {
            "total_injections": total,
            "successful_injections": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_context_entries": avg_context,
            "templates_used": template_usage
        }


# Global injection debugger instance
injection_debugger = ContextInjectionDebugger()
