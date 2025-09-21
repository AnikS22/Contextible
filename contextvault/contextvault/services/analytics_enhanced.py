"""Enhanced analytics service for multi-model support and performance tracking."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict, Counter

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..database import get_db_context
from ..models.context import ContextEntry, ContextCategory, ContextSource
from ..models.sessions import Session as SessionModel
from ..models.models import AIModel, ModelProvider
from ..services.analytics import ContextAnalytics

logger = logging.getLogger(__name__)


class EnhancedAnalytics(ContextAnalytics):
    """Enhanced analytics service with multi-model support and performance tracking."""
    
    def __init__(self):
        """Initialize the enhanced analytics service."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    async def track_model_performance(self, 
                                    model_id: str, 
                                    metrics: Dict[str, Any]) -> None:
        """
        Track performance metrics for a specific model.
        
        Args:
            model_id: Model identifier
            metrics: Performance metrics dictionary
        """
        with get_db_context() as db:
            model = db.query(AIModel).filter(AIModel.id == model_id).first()
            if not model:
                self.logger.warning(f"Model {model_id} not found for performance tracking")
                return
            
            # Update model performance
            response_time_ms = metrics.get("response_time_ms", 0)
            success = metrics.get("success", True)
            tokens_generated = metrics.get("tokens_generated", 0)
            
            model.update_performance_metrics(response_time_ms, success, tokens_generated)
            db.commit()
            
            self.logger.info(f"Updated performance metrics for model {model.name}")
    
    async def get_usage_patterns(self, days: int = 30) -> Dict[str, Any]:
        """
        Get usage patterns for the specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with usage pattern data
        """
        with get_db_context() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get session data
            sessions = db.query(SessionModel).filter(
                SessionModel.started_at >= cutoff_date
            ).all()
            
            # Analyze usage patterns
            patterns = {
                "total_sessions": len(sessions),
                "sessions_by_day": self._analyze_sessions_by_day(sessions),
                "sessions_by_hour": self._analyze_sessions_by_hour(sessions),
                "model_usage": self._analyze_model_usage(sessions),
                "context_usage": self._analyze_context_usage(sessions),
                "performance_trends": self._analyze_performance_trends(sessions),
                "peak_usage_times": self._identify_peak_usage_times(sessions)
            }
            
            return patterns
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report.
        
        Returns:
            Dictionary with performance report data
        """
        with get_db_context() as db:
            # Get all models
            models = db.query(AIModel).all()
            
            # Get recent sessions
            recent_sessions = db.query(SessionModel).filter(
                SessionModel.started_at >= datetime.utcnow() - timedelta(days=7)
            ).all()
            
            report = {
                "report_generated_at": datetime.utcnow().isoformat(),
                "model_performance": await self._analyze_model_performance(models),
                "system_performance": await self._analyze_system_performance(recent_sessions),
                "usage_statistics": await self._analyze_usage_statistics(recent_sessions),
                "recommendations": await self._generate_performance_recommendations(models, recent_sessions)
            }
            
            return report
    
    async def track_context_effectiveness(self) -> Dict[str, Any]:
        """
        Track the effectiveness of context injection.
        
        Returns:
            Dictionary with context effectiveness metrics
        """
        with get_db_context() as db:
            # Get sessions with context usage
            sessions_with_context = db.query(SessionModel).filter(
                SessionModel.context_count > 0
            ).all()
            
            if not sessions_with_context:
                return {"error": "No sessions with context usage found"}
            
            effectiveness_metrics = {
                "total_sessions_with_context": len(sessions_with_context),
                "average_context_per_session": sum(s.context_count for s in sessions_with_context) / len(sessions_with_context),
                "context_usage_by_type": self._analyze_context_usage_by_type(sessions_with_context),
                "context_effectiveness_by_model": self._analyze_context_effectiveness_by_model(sessions_with_context),
                "most_effective_context": self._identify_most_effective_context(sessions_with_context),
                "context_retrieval_performance": self._analyze_context_retrieval_performance(sessions_with_context)
            }
            
            return effectiveness_metrics
    
    async def get_model_comparison(self) -> Dict[str, Any]:
        """
        Compare performance across different models.
        
        Returns:
            Dictionary with model comparison data
        """
        with get_db_context() as db:
            models = db.query(AIModel).all()
            
            comparison = {
                "models_compared": len(models),
                "performance_metrics": {},
                "capability_analysis": {},
                "recommendations": {}
            }
            
            for model in models:
                model_data = {
                    "name": model.name,
                    "provider": model.provider.value if hasattr(model.provider, 'value') else str(model.provider),
                    "total_requests": model.total_requests,
                    "success_rate": model.success_rate,
                    "average_response_time_ms": model.average_response_time_ms,
                    "health_score": model.get_health_score(),
                    "capabilities": model.capabilities or {}
                }
                
                comparison["performance_metrics"][model.name] = model_data
            
            # Analyze capabilities
            comparison["capability_analysis"] = self._analyze_model_capabilities(models)
            
            # Generate recommendations
            comparison["recommendations"] = self._generate_model_recommendations(models)
            
            return comparison
    
    def _analyze_sessions_by_day(self, sessions: List[SessionModel]) -> Dict[str, int]:
        """Analyze sessions by day of week."""
        day_counts = defaultdict(int)
        
        for session in sessions:
            day_name = session.started_at.strftime("%A")
            day_counts[day_name] += 1
        
        return dict(day_counts)
    
    def _analyze_sessions_by_hour(self, sessions: List[SessionModel]) -> Dict[int, int]:
        """Analyze sessions by hour of day."""
        hour_counts = defaultdict(int)
        
        for session in sessions:
            hour = session.started_at.hour
            hour_counts[hour] += 1
        
        return dict(hour_counts)
    
    def _analyze_model_usage(self, sessions: List[SessionModel]) -> Dict[str, int]:
        """Analyze model usage patterns."""
        model_counts = Counter()
        
        for session in sessions:
            model_counts[session.model_id] += 1
        
        return dict(model_counts)
    
    def _analyze_context_usage(self, sessions: List[SessionModel]) -> Dict[str, Any]:
        """Analyze context usage patterns."""
        total_context_used = sum(s.context_count for s in sessions)
        total_sessions = len(sessions)
        
        return {
            "total_context_entries_used": total_context_used,
            "average_context_per_session": total_context_used / total_sessions if total_sessions > 0 else 0,
            "sessions_with_context": len([s for s in sessions if s.context_count > 0]),
            "sessions_without_context": len([s for s in sessions if s.context_count == 0])
        }
    
    def _analyze_performance_trends(self, sessions: List[SessionModel]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if not sessions:
            return {}
        
        # Group sessions by day
        daily_sessions = defaultdict(list)
        for session in sessions:
            day = session.started_at.date()
            daily_sessions[day].append(session)
        
        trends = {
            "daily_average_response_time": {},
            "daily_success_rate": {},
            "daily_context_usage": {}
        }
        
        for day, day_sessions in daily_sessions.items():
            response_times = [s.model_response_time_ms for s in day_sessions if s.model_response_time_ms]
            success_count = len([s for s in day_sessions if s.success])
            context_usage = sum(s.context_count for s in day_sessions)
            
            trends["daily_average_response_time"][day.isoformat()] = (
                sum(response_times) / len(response_times) if response_times else 0
            )
            trends["daily_success_rate"][day.isoformat()] = (
                success_count / len(day_sessions) if day_sessions else 0
            )
            trends["daily_context_usage"][day.isoformat()] = context_usage
        
        return trends
    
    def _identify_peak_usage_times(self, sessions: List[SessionModel]) -> Dict[str, Any]:
        """Identify peak usage times."""
        if not sessions:
            return {}
        
        # Analyze by hour
        hour_counts = defaultdict(int)
        for session in sessions:
            hour_counts[session.started_at.hour] += 1
        
        # Find peak hours
        peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "peak_hours": [{"hour": hour, "sessions": count} for hour, count in peak_hours],
            "total_peak_sessions": sum(count for _, count in peak_hours)
        }
    
    async def _analyze_model_performance(self, models: List[AIModel]) -> Dict[str, Any]:
        """Analyze model performance metrics."""
        performance_data = {}
        
        for model in models:
            performance_data[model.name] = {
                "total_requests": model.total_requests,
                "success_rate": model.success_rate,
                "average_response_time_ms": model.average_response_time_ms,
                "health_score": model.get_health_score(),
                "capabilities": model.capabilities or {},
                "last_used": model.last_used_at.isoformat() if model.last_used_at else None
            }
        
        return performance_data
    
    async def _analyze_system_performance(self, sessions: List[SessionModel]) -> Dict[str, Any]:
        """Analyze overall system performance."""
        if not sessions:
            return {}
        
        response_times = [s.model_response_time_ms for s in sessions if s.model_response_time_ms]
        processing_times = [s.processing_time_ms for s in sessions if s.processing_time_ms]
        success_count = len([s for s in sessions if s.success])
        
        return {
            "total_sessions": len(sessions),
            "success_rate": success_count / len(sessions) if sessions else 0,
            "average_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
            "average_processing_time_ms": sum(processing_times) / len(processing_times) if processing_times else 0,
            "total_context_used": sum(s.context_count for s in sessions)
        }
    
    async def _analyze_usage_statistics(self, sessions: List[SessionModel]) -> Dict[str, Any]:
        """Analyze usage statistics."""
        if not sessions:
            return {}
        
        # Group by model
        model_usage = defaultdict(int)
        for session in sessions:
            model_usage[session.model_id] += 1
        
        # Group by context usage
        context_usage_groups = {
            "no_context": len([s for s in sessions if s.context_count == 0]),
            "low_context": len([s for s in sessions if 1 <= s.context_count <= 3]),
            "medium_context": len([s for s in sessions if 4 <= s.context_count <= 10]),
            "high_context": len([s for s in sessions if s.context_count > 10])
        }
        
        return {
            "model_usage": dict(model_usage),
            "context_usage_groups": context_usage_groups,
            "average_context_per_session": sum(s.context_count for s in sessions) / len(sessions)
        }
    
    async def _generate_performance_recommendations(self, 
                                                  models: List[AIModel], 
                                                  sessions: List[SessionModel]) -> List[Dict[str, Any]]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Check for underperforming models
        for model in models:
            if model.success_rate and model.success_rate < 0.8:
                recommendations.append({
                    "type": "model_performance",
                    "priority": "high",
                    "title": f"Low success rate for {model.name}",
                    "description": f"Model {model.name} has a success rate of {model.success_rate:.2f}",
                    "recommendation": "Consider investigating model issues or switching to a more reliable model"
                })
            
            if model.average_response_time_ms and model.average_response_time_ms > 10000:
                recommendations.append({
                    "type": "model_performance",
                    "priority": "medium",
                    "title": f"Slow response time for {model.name}",
                    "description": f"Model {model.name} has an average response time of {model.average_response_time_ms}ms",
                    "recommendation": "Consider optimizing model configuration or using a faster model"
                })
        
        # Check for context usage patterns
        sessions_with_context = [s for s in sessions if s.context_count > 0]
        if len(sessions_with_context) < len(sessions) * 0.5:
            recommendations.append({
                "type": "context_usage",
                "priority": "medium",
                "title": "Low context usage",
                "description": f"Only {len(sessions_with_context)}/{len(sessions)} sessions used context",
                "recommendation": "Consider improving context retrieval or user education"
            })
        
        return recommendations
    
    def _analyze_context_usage_by_type(self, sessions: List[SessionModel]) -> Dict[str, int]:
        """Analyze context usage by type."""
        # This would require joining with context entries
        # For now, return a placeholder
        return {"placeholder": "context_type_analysis"}
    
    def _analyze_context_effectiveness_by_model(self, sessions: List[SessionModel]) -> Dict[str, Any]:
        """Analyze context effectiveness by model."""
        model_effectiveness = defaultdict(lambda: {"sessions": 0, "total_context": 0, "success_rate": 0})
        
        for session in sessions:
            model_effectiveness[session.model_id]["sessions"] += 1
            model_effectiveness[session.model_id]["total_context"] += session.context_count
            if session.success:
                model_effectiveness[session.model_id]["success_rate"] += 1
        
        # Calculate averages
        for model_id, data in model_effectiveness.items():
            if data["sessions"] > 0:
                data["success_rate"] = data["success_rate"] / data["sessions"]
                data["average_context_per_session"] = data["total_context"] / data["sessions"]
        
        return dict(model_effectiveness)
    
    def _identify_most_effective_context(self, sessions: List[SessionModel]) -> Dict[str, Any]:
        """Identify the most effective context entries."""
        # This would require analyzing which context entries lead to successful sessions
        # For now, return a placeholder
        return {"placeholder": "most_effective_context_analysis"}
    
    def _analyze_context_retrieval_performance(self, sessions: List[SessionModel]) -> Dict[str, Any]:
        """Analyze context retrieval performance."""
        processing_times = [s.processing_time_ms for s in sessions if s.processing_time_ms]
        
        return {
            "average_processing_time_ms": sum(processing_times) / len(processing_times) if processing_times else 0,
            "total_processing_time_ms": sum(processing_times),
            "sessions_with_processing_data": len(processing_times)
        }
    
    def _analyze_model_capabilities(self, models: List[AIModel]) -> Dict[str, Any]:
        """Analyze model capabilities across all models."""
        capability_scores = defaultdict(list)
        
        for model in models:
            if model.capabilities:
                for capability, data in model.capabilities.items():
                    if isinstance(data, dict) and "score" in data:
                        capability_scores[capability].append(data["score"])
        
        # Calculate average scores for each capability
        avg_scores = {}
        for capability, scores in capability_scores.items():
            avg_scores[capability] = sum(scores) / len(scores) if scores else 0
        
        return avg_scores
    
    def _generate_model_recommendations(self, models: List[AIModel]) -> List[Dict[str, Any]]:
        """Generate model-specific recommendations."""
        recommendations = []
        
        # Find best model for each capability
        capabilities = set()
        for model in models:
            if model.capabilities:
                capabilities.update(model.capabilities.keys())
        
        for capability in capabilities:
            best_model = None
            best_score = 0
            
            for model in models:
                if model.capabilities and capability in model.capabilities:
                    score = model.capabilities[capability].get("score", 0)
                    if score > best_score:
                        best_score = score
                        best_model = model
            
            if best_model:
                recommendations.append({
                    "capability": capability,
                    "recommended_model": best_model.name,
                    "score": best_score,
                    "reasoning": f"Model {best_model.name} has the highest score ({best_score:.2f}) for {capability}"
                })
        
        return recommendations


# Global enhanced analytics service instance
enhanced_analytics = EnhancedAnalytics()
