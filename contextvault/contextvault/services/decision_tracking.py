"""Model decision tracking service for enterprise compliance."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from ..database import get_db_context
from ..models.audit import AuditLog, AuditEventType
from ..models.models import AIModel
from ..models.context import ContextEntry
from ..models.sessions import Session as SessionModel

logger = logging.getLogger(__name__)


class ModelDecisionTracker:
    """Service for tracking model decisions and reasoning."""
    
    def __init__(self):
        """Initialize the decision tracker."""
        self.logger = logging.getLogger(__name__)
    
    async def track_model_decision(self,
                                 user_id: str,
                                 model_id: str,
                                 request_data: Dict[str, Any],
                                 response_data: Dict[str, Any],
                                 context_used: List[ContextEntry],
                                 decision_reasoning: Dict[str, Any],
                                 session_id: Optional[str] = None,
                                 ip_address: Optional[str] = None,
                                 user_agent: Optional[str] = None) -> AuditLog:
        """
        Track a model decision with full reasoning.
        
        Args:
            user_id: User ID
            model_id: Model identifier
            request_data: Request data
            response_data: Response data
            context_used: Context entries used
            decision_reasoning: Reasoning for the decision
            session_id: Session ID
            ip_address: IP address
            user_agent: User agent
            
        Returns:
            Audit log entry
        """
        with get_db_context() as db:
            # Create comprehensive decision tracking
            decision_data = {
                "model_id": model_id,
                "request_data": request_data,
                "response_data": response_data,
                "context_used": [
                    {
                        "id": ctx.id,
                        "content": ctx.content[:200],  # Truncated for storage
                        "context_type": ctx.context_type.value if hasattr(ctx.context_type, 'value') else str(ctx.context_type),
                        "relevance_score": decision_reasoning.get("context_relevance", {}).get(ctx.id, 0.0)
                    }
                    for ctx in context_used
                ],
                "decision_reasoning": decision_reasoning,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log the decision
            audit_log = await self._log_decision_event(
                user_id=user_id,
                model_id=model_id,
                decision_data=decision_data,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Track model performance
            await self._track_model_performance(
                model_id=model_id,
                decision_data=decision_data,
                success=decision_reasoning.get("success", True)
            )
            
            return audit_log
    
    async def track_context_injection_decision(self,
                                             user_id: str,
                                             model_id: str,
                                             original_prompt: str,
                                             context_entries: List[ContextEntry],
                                             injection_reasoning: Dict[str, Any],
                                             session_id: Optional[str] = None,
                                             ip_address: Optional[str] = None,
                                             user_agent: Optional[str] = None) -> AuditLog:
        """
        Track context injection decision.
        
        Args:
            user_id: User ID
            model_id: Model identifier
            original_prompt: Original user prompt
            context_entries: Context entries injected
            injection_reasoning: Reasoning for injection
            session_id: Session ID
            ip_address: IP address
            user_agent: User agent
            
        Returns:
            Audit log entry
        """
        with get_db_context() as db:
            # Create injection decision data
            injection_data = {
                "model_id": model_id,
                "original_prompt": original_prompt,
                "context_entries": [
                    {
                        "id": ctx.id,
                        "content": ctx.content[:200],
                        "context_type": ctx.context_type.value if hasattr(ctx.context_type, 'value') else str(ctx.context_type),
                        "injection_score": injection_reasoning.get("injection_scores", {}).get(ctx.id, 0.0)
                    }
                    for ctx in context_entries
                ],
                "injection_reasoning": injection_reasoning,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log the injection decision
            audit_log = await self._log_injection_event(
                user_id=user_id,
                injection_data=injection_data,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return audit_log
    
    async def track_model_routing_decision(self,
                                        user_id: str,
                                        available_models: List[AIModel],
                                        selected_model: AIModel,
                                        routing_reasoning: Dict[str, Any],
                                        session_id: Optional[str] = None,
                                        ip_address: Optional[str] = None,
                                        user_agent: Optional[str] = None) -> AuditLog:
        """
        Track model routing decision.
        
        Args:
            user_id: User ID
            available_models: Available models
            selected_model: Selected model
            routing_reasoning: Reasoning for routing
            session_id: Session ID
            ip_address: IP address
            user_agent: User agent
            
        Returns:
            Audit log entry
        """
        with get_db_context() as db:
            # Create routing decision data
            routing_data = {
                "available_models": [
                    {
                        "id": model.id,
                        "name": model.name,
                        "provider": model.provider.value if hasattr(model.provider, 'value') else str(model.provider),
                        "capabilities": model.capabilities
                    }
                    for model in available_models
                ],
                "selected_model": {
                    "id": selected_model.id,
                    "name": selected_model.name,
                    "provider": selected_model.provider.value if hasattr(selected_model.provider, 'value') else str(selected_model.provider),
                    "capabilities": selected_model.capabilities
                },
                "routing_reasoning": routing_reasoning,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log the routing decision
            audit_log = await self._log_routing_event(
                user_id=user_id,
                routing_data=routing_data,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return audit_log
    
    async def get_decision_history(self,
                                 user_id: Optional[str] = None,
                                 model_id: Optional[str] = None,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 limit: int = 100) -> List[AuditLog]:
        """
        Get decision history with filtering.
        
        Args:
            user_id: Filter by user ID
            model_id: Filter by model ID
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of records
            
        Returns:
            List of decision audit logs
        """
        with get_db_context() as db:
            query = db.query(AuditLog).filter(
                AuditLog.event_type.in_([
                    AuditEventType.MODEL_REQUEST,
                    AuditEventType.MODEL_RESPONSE,
                    AuditEventType.MODEL_ROUTING
                ])
            )
            
            # Apply filters
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if start_date:
                query = query.filter(AuditLog.event_timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.event_timestamp <= end_date)
            
            # Filter by model ID in event data
            if model_id:
                query = query.filter(
                    AuditLog.event_data.op('->>')('model_id') == model_id
                )
            
            # Order by timestamp and apply limit
            decisions = query.order_by(desc(AuditLog.event_timestamp)).limit(limit).all()
            
            return decisions
    
    async def get_model_decision_analytics(self, model_id: str, days: int = 30) -> Dict[str, Any]:
        """Get analytics for model decisions."""
        with get_db_context() as db:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get model decisions
            decisions = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.MODEL_RESPONSE,
                    AuditLog.event_data.op('->>')('model_id') == model_id,
                    AuditLog.event_timestamp >= start_date
                )
            ).all()
            
            # Calculate analytics
            total_decisions = len(decisions)
            successful_decisions = sum(1 for d in decisions if d.success)
            success_rate = successful_decisions / total_decisions if total_decisions > 0 else 0.0
            
            # Get context usage patterns
            context_usage = {}
            for decision in decisions:
                context_entries = decision.event_data.get("context_used", [])
                for ctx in context_entries:
                    ctx_type = ctx.get("context_type", "unknown")
                    context_usage[ctx_type] = context_usage.get(ctx_type, 0) + 1
            
            # Get reasoning patterns
            reasoning_patterns = {}
            for decision in decisions:
                reasoning = decision.event_data.get("decision_reasoning", {})
                for key, value in reasoning.items():
                    if isinstance(value, (str, int, float)):
                        reasoning_patterns[key] = reasoning_patterns.get(key, 0) + 1
            
            return {
                "model_id": model_id,
                "period_days": days,
                "total_decisions": total_decisions,
                "successful_decisions": successful_decisions,
                "success_rate": success_rate,
                "context_usage": context_usage,
                "reasoning_patterns": reasoning_patterns,
                "average_response_time": self._calculate_average_response_time(decisions)
            }
    
    async def get_user_decision_patterns(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get decision patterns for a user."""
        with get_db_context() as db:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get user decisions
            decisions = db.query(AuditLog).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.event_type.in_([
                        AuditEventType.MODEL_REQUEST,
                        AuditEventType.MODEL_RESPONSE
                    ]),
                    AuditLog.event_timestamp >= start_date
                )
            ).all()
            
            # Analyze patterns
            model_preferences = {}
            context_preferences = {}
            time_patterns = {}
            
            for decision in decisions:
                # Model preferences
                model_id = decision.event_data.get("model_id", "unknown")
                model_preferences[model_id] = model_preferences.get(model_id, 0) + 1
                
                # Context preferences
                context_entries = decision.event_data.get("context_used", [])
                for ctx in context_entries:
                    ctx_type = ctx.get("context_type", "unknown")
                    context_preferences[ctx_type] = context_preferences.get(ctx_type, 0) + 1
                
                # Time patterns
                hour = decision.event_timestamp.hour
                time_patterns[hour] = time_patterns.get(hour, 0) + 1
            
            return {
                "user_id": user_id,
                "period_days": days,
                "total_decisions": len(decisions),
                "model_preferences": model_preferences,
                "context_preferences": context_preferences,
                "time_patterns": time_patterns,
                "most_active_hour": max(time_patterns.items(), key=lambda x: x[1])[0] if time_patterns else None
            }
    
    async def _log_decision_event(self,
                               user_id: str,
                               model_id: str,
                               decision_data: Dict[str, Any],
                               session_id: Optional[str] = None,
                               ip_address: Optional[str] = None,
                               user_agent: Optional[str] = None) -> AuditLog:
        """Log a decision event."""
        from ..services.audit_service import audit_service
        
        return await audit_service.log_event(
            event_type=AuditEventType.MODEL_RESPONSE,
            user_id=user_id,
            session_id=session_id,
            event_data=decision_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def _log_injection_event(self,
                                 user_id: str,
                                 injection_data: Dict[str, Any],
                                 session_id: Optional[str] = None,
                                 ip_address: Optional[str] = None,
                                 user_agent: Optional[str] = None) -> AuditLog:
        """Log an injection event."""
        from ..services.audit_service import audit_service
        
        return await audit_service.log_event(
            event_type=AuditEventType.CONTEXT_ACCESS,
            user_id=user_id,
            session_id=session_id,
            event_data=injection_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def _log_routing_event(self,
                               user_id: str,
                               routing_data: Dict[str, Any],
                               session_id: Optional[str] = None,
                               ip_address: Optional[str] = None,
                               user_agent: Optional[str] = None) -> AuditLog:
        """Log a routing event."""
        from ..services.audit_service import audit_service
        
        return await audit_service.log_event(
            event_type=AuditEventType.MODEL_ROUTING,
            user_id=user_id,
            session_id=session_id,
            event_data=routing_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def _track_model_performance(self,
                                    model_id: str,
                                    decision_data: Dict[str, Any],
                                    success: bool) -> None:
        """Track model performance metrics."""
        # This would integrate with the enhanced analytics service
        # For now, we'll just log the performance
        self.logger.info(f"Tracked performance for model {model_id}: success={success}")
    
    def _calculate_average_response_time(self, decisions: List[AuditLog]) -> float:
        """Calculate average response time from decisions."""
        # This would calculate from actual response times
        # For now, return a placeholder
        return 1.5  # seconds


# Global decision tracker instance
decision_tracker = ModelDecisionTracker()
