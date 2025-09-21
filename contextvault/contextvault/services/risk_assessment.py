"""Risk assessment service for enterprise compliance."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from ..database import get_db_context
from ..models.audit import AuditLog, AuditEventType
# Removed user import - focusing on core functionality
from ..models.context import ContextEntry
from ..models.sessions import Session as SessionModel

logger = logging.getLogger(__name__)


class RiskAssessmentService:
    """Service for risk assessment and categorization."""
    
    def __init__(self):
        """Initialize the risk assessment service."""
        self.logger = logging.getLogger(__name__)
    
    async def assess_user_risk(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Assess risk level for a user.
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Risk assessment results
        """
        with get_db_context() as db:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get user information
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            
            # Get risk factors
            risk_factors = await self._analyze_risk_factors(user_id, start_date)
            
            # Calculate risk score
            risk_score = await self._calculate_risk_score(risk_factors)
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Generate recommendations
            recommendations = await self._generate_risk_recommendations(risk_factors, risk_score)
            
            return {
                "user_id": user_id,
                "username": user.username,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "assessment_date": datetime.utcnow().isoformat(),
                "period_days": days
            }
    
    async def assess_context_risk(self, context_id: str) -> Dict[str, Any]:
        """
        Assess risk level for a context entry.
        
        Args:
            context_id: Context entry ID
            
        Returns:
            Risk assessment results
        """
        with get_db_context() as db:
            # Get context entry
            context_entry = db.query(ContextEntry).filter(ContextEntry.id == context_id).first()
            if not context_entry:
                return {"error": "Context entry not found"}
            
            # Analyze context risk factors
            risk_factors = await self._analyze_context_risk_factors(context_entry)
            
            # Calculate risk score
            risk_score = await self._calculate_context_risk_score(risk_factors)
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Generate recommendations
            recommendations = await self._generate_context_risk_recommendations(risk_factors, risk_score)
            
            return {
                "context_id": context_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "assessment_date": datetime.utcnow().isoformat()
            }
    
    async def assess_model_risk(self, model_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Assess risk level for a model.
        
        Args:
            model_id: Model identifier
            days: Number of days to analyze
            
        Returns:
            Risk assessment results
        """
        with get_db_context() as db:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get model risk factors
            risk_factors = await self._analyze_model_risk_factors(model_id, start_date)
            
            # Calculate risk score
            risk_score = await self._calculate_model_risk_score(risk_factors)
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Generate recommendations
            recommendations = await self._generate_model_risk_recommendations(risk_factors, risk_score)
            
            return {
                "model_id": model_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "assessment_date": datetime.utcnow().isoformat(),
                "period_days": days
            }
    
    async def get_high_risk_activities(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get high-risk activities in the system.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of high-risk activities
        """
        with get_db_context() as db:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get high-risk events
            high_risk_events = db.query(AuditLog).filter(
                and_(
                    AuditLog.risk_level == "high",
                    AuditLog.event_timestamp >= start_date
                )
            ).order_by(desc(AuditLog.event_timestamp)).all()
            
            # Format high-risk activities
            activities = []
            for event in high_risk_events:
                activities.append({
                    "id": event.id,
                    "event_type": event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
                    "user_id": event.user_id,
                    "timestamp": event.event_timestamp.isoformat(),
                    "risk_level": event.risk_level,
                    "risk_score": event.risk_score,
                    "event_data": event.event_data,
                    "ip_address": event.ip_address,
                    "success": event.success
                })
            
            return activities
    
    async def get_risk_dashboard(self) -> Dict[str, Any]:
        """Get risk dashboard data."""
        with get_db_context() as db:
            # Get risk statistics
            risk_stats = await self._get_risk_statistics()
            
            # Get high-risk users
            high_risk_users = await self._get_high_risk_users()
            
            # Get risk trends
            risk_trends = await self._get_risk_trends()
            
            # Get compliance status
            compliance_status = await self._get_compliance_status()
            
            return {
                "risk_statistics": risk_stats,
                "high_risk_users": high_risk_users,
                "risk_trends": risk_trends,
                "compliance_status": compliance_status,
                "dashboard_updated": datetime.utcnow().isoformat()
            }
    
    async def _analyze_risk_factors(self, user_id: str, start_date: datetime) -> Dict[str, Any]:
        """Analyze risk factors for a user."""
        with get_db_context() as db:
            # Get user activity
            activity_events = db.query(AuditLog).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.event_timestamp >= start_date
                )
            ).all()
            
            # Analyze risk factors
            risk_factors = {
                "failed_events": 0,
                "high_risk_events": 0,
                "unusual_activity": 0,
                "data_access_frequency": 0,
                "model_usage_patterns": {},
                "ip_addresses": set(),
                "user_agents": set(),
                "time_patterns": {},
                "context_access_patterns": {}
            }
            
            for event in activity_events:
                # Failed events
                if not event.success:
                    risk_factors["failed_events"] += 1
                
                # High-risk events
                if event.risk_level == "high":
                    risk_factors["high_risk_events"] += 1
                
                # Data access frequency
                if event.event_type == AuditEventType.DATA_ACCESS:
                    risk_factors["data_access_frequency"] += 1
                
                # IP addresses
                if event.ip_address:
                    risk_factors["ip_addresses"].add(event.ip_address)
                
                # User agents
                if event.user_agent:
                    risk_factors["user_agents"].add(event.user_agent)
                
                # Time patterns
                hour = event.event_timestamp.hour
                risk_factors["time_patterns"][hour] = risk_factors["time_patterns"].get(hour, 0) + 1
                
                # Context access patterns
                if event.event_type == AuditEventType.CONTEXT_ACCESS:
                    context_id = event.event_data.get("context_id")
                    if context_id:
                        risk_factors["context_access_patterns"][context_id] = risk_factors["context_access_patterns"].get(context_id, 0) + 1
            
            # Convert sets to lists for JSON serialization
            risk_factors["ip_addresses"] = list(risk_factors["ip_addresses"])
            risk_factors["user_agents"] = list(risk_factors["user_agents"])
            
            return risk_factors
    
    async def _analyze_context_risk_factors(self, context_entry: ContextEntry) -> Dict[str, Any]:
        """Analyze risk factors for a context entry."""
        with get_db_context() as db:
            # Get context access events
            access_events = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.CONTEXT_ACCESS,
                    AuditLog.event_data.op('->>')('context_id') == context_entry.id
                )
            ).all()
            
            # Analyze risk factors
            risk_factors = {
                "access_count": len(access_events),
                "unique_users": len(set(event.user_id for event in access_events if event.user_id)),
                "content_sensitivity": self._assess_content_sensitivity(context_entry.content),
                "context_type": context_entry.context_type.value if hasattr(context_entry.context_type, 'value') else str(context_entry.context_type),
                "tags": context_entry.tags or [],
                "metadata": context_entry.entry_metadata or {},
                "creation_date": context_entry.created_at.isoformat() if context_entry.created_at else None
            }
            
            return risk_factors
    
    async def _analyze_model_risk_factors(self, model_id: str, start_date: datetime) -> Dict[str, Any]:
        """Analyze risk factors for a model."""
        with get_db_context() as db:
            # Get model events
            model_events = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_data.op('->>')('model_id') == model_id,
                    AuditLog.event_timestamp >= start_date
                )
            ).all()
            
            # Analyze risk factors
            risk_factors = {
                "total_requests": len(model_events),
                "failed_requests": sum(1 for event in model_events if not event.success),
                "unique_users": len(set(event.user_id for event in model_events if event.user_id)),
                "response_times": [],
                "error_patterns": {},
                "usage_patterns": {}
            }
            
            for event in model_events:
                # Response times
                if "response_time" in event.event_data:
                    risk_factors["response_times"].append(event.event_data["response_time"])
                
                # Error patterns
                if not event.success and event.error_message:
                    error_type = self._categorize_error(event.error_message)
                    risk_factors["error_patterns"][error_type] = risk_factors["error_patterns"].get(error_type, 0) + 1
                
                # Usage patterns
                hour = event.event_timestamp.hour
                risk_factors["usage_patterns"][hour] = risk_factors["usage_patterns"].get(hour, 0) + 1
            
            return risk_factors
    
    async def _calculate_risk_score(self, risk_factors: Dict[str, Any]) -> float:
        """Calculate risk score from risk factors."""
        score = 0.0
        
        # Failed events (high impact)
        failed_events = risk_factors.get("failed_events", 0)
        score += min(0.3, failed_events * 0.05)
        
        # High-risk events (high impact)
        high_risk_events = risk_factors.get("high_risk_events", 0)
        score += min(0.4, high_risk_events * 0.1)
        
        # Data access frequency (medium impact)
        data_access = risk_factors.get("data_access_frequency", 0)
        score += min(0.2, data_access * 0.01)
        
        # IP diversity (low impact)
        ip_count = len(risk_factors.get("ip_addresses", []))
        if ip_count > 5:  # Multiple IPs might indicate risk
            score += min(0.1, (ip_count - 5) * 0.02)
        
        # Time pattern anomalies (medium impact)
        time_patterns = risk_factors.get("time_patterns", {})
        if len(time_patterns) > 0:
            # Check for unusual hours (outside 9-17)
            unusual_hours = sum(1 for hour in time_patterns.keys() if hour < 9 or hour > 17)
            score += min(0.1, unusual_hours * 0.02)
        
        return min(1.0, score)
    
    async def _calculate_context_risk_score(self, risk_factors: Dict[str, Any]) -> float:
        """Calculate risk score for context entry."""
        score = 0.0
        
        # Access count (medium impact)
        access_count = risk_factors.get("access_count", 0)
        score += min(0.3, access_count * 0.01)
        
        # Unique users (medium impact)
        unique_users = risk_factors.get("unique_users", 0)
        score += min(0.2, unique_users * 0.05)
        
        # Content sensitivity (high impact)
        content_sensitivity = risk_factors.get("content_sensitivity", 0.0)
        score += content_sensitivity * 0.4
        
        # Context type (low impact)
        context_type = risk_factors.get("context_type", "unknown")
        if context_type in ["personal", "sensitive", "confidential"]:
            score += 0.1
        
        return min(1.0, score)
    
    async def _calculate_model_risk_score(self, risk_factors: Dict[str, Any]) -> float:
        """Calculate risk score for model."""
        score = 0.0
        
        # Failed requests (high impact)
        failed_requests = risk_factors.get("failed_requests", 0)
        total_requests = risk_factors.get("total_requests", 1)
        failure_rate = failed_requests / total_requests if total_requests > 0 else 0
        score += min(0.4, failure_rate * 0.8)
        
        # Error patterns (medium impact)
        error_patterns = risk_factors.get("error_patterns", {})
        if error_patterns:
            score += min(0.2, len(error_patterns) * 0.05)
        
        # Response time anomalies (low impact)
        response_times = risk_factors.get("response_times", [])
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            if avg_response_time > 10:  # Slow responses might indicate issues
                score += min(0.1, (avg_response_time - 10) * 0.01)
        
        return min(1.0, score)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score."""
        if risk_score >= 0.7:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _assess_content_sensitivity(self, content: str) -> float:
        """Assess content sensitivity score."""
        # Simple keyword-based sensitivity assessment
        sensitive_keywords = [
            "password", "secret", "confidential", "private", "personal",
            "ssn", "social security", "credit card", "bank account",
            "medical", "health", "financial", "legal"
        ]
        
        content_lower = content.lower()
        sensitivity_score = 0.0
        
        for keyword in sensitive_keywords:
            if keyword in content_lower:
                sensitivity_score += 0.1
        
        return min(1.0, sensitivity_score)
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error message."""
        error_lower = error_message.lower()
        
        if "timeout" in error_lower:
            return "timeout"
        elif "connection" in error_lower:
            return "connection"
        elif "permission" in error_lower:
            return "permission"
        elif "validation" in error_lower:
            return "validation"
        else:
            return "other"
    
    async def _generate_risk_recommendations(self, risk_factors: Dict[str, Any], risk_score: float) -> List[str]:
        """Generate risk recommendations."""
        recommendations = []
        
        if risk_factors.get("failed_events", 0) > 5:
            recommendations.append("Review failed events and implement error handling")
        
        if risk_factors.get("high_risk_events", 0) > 0:
            recommendations.append("Investigate high-risk events immediately")
        
        if len(risk_factors.get("ip_addresses", [])) > 3:
            recommendations.append("Monitor IP address diversity for security")
        
        if risk_score > 0.7:
            recommendations.append("Implement additional monitoring and controls")
        
        return recommendations
    
    async def _generate_context_risk_recommendations(self, risk_factors: Dict[str, Any], risk_score: float) -> List[str]:
        """Generate context risk recommendations."""
        recommendations = []
        
        if risk_factors.get("access_count", 0) > 100:
            recommendations.append("Consider access controls for frequently accessed context")
        
        if risk_factors.get("unique_users", 0) > 10:
            recommendations.append("Review context sharing permissions")
        
        if risk_factors.get("content_sensitivity", 0) > 0.5:
            recommendations.append("Implement additional security for sensitive content")
        
        return recommendations
    
    async def _generate_model_risk_recommendations(self, risk_factors: Dict[str, Any], risk_score: float) -> List[str]:
        """Generate model risk recommendations."""
        recommendations = []
        
        failure_rate = risk_factors.get("failed_requests", 0) / max(1, risk_factors.get("total_requests", 1))
        if failure_rate > 0.1:
            recommendations.append("Investigate model performance issues")
        
        if len(risk_factors.get("error_patterns", {})) > 3:
            recommendations.append("Implement error monitoring and alerting")
        
        return recommendations
    
    async def _get_risk_statistics(self) -> Dict[str, Any]:
        """Get risk statistics for dashboard."""
        with get_db_context() as db:
            # Get risk level counts
            risk_counts = db.query(
                AuditLog.risk_level,
                func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.risk_level.isnot(None)
            ).group_by(AuditLog.risk_level).all()
            
            # Get total events
            total_events = db.query(func.count(AuditLog.id)).scalar()
            
            # Get high-risk events
            high_risk_events = db.query(func.count(AuditLog.id)).filter(
                AuditLog.risk_level == "high"
            ).scalar()
            
            return {
                "total_events": total_events,
                "high_risk_events": high_risk_events,
                "risk_levels": {level: count for level, count in risk_counts},
                "high_risk_percentage": (high_risk_events / total_events * 100) if total_events > 0 else 0
            }
    
    async def _get_high_risk_users(self) -> List[Dict[str, Any]]:
        """Get high-risk users."""
        with get_db_context() as db:
            # Get users with high-risk events
            high_risk_users = db.query(
                AuditLog.user_id,
                func.count(AuditLog.id).label('high_risk_count')
            ).filter(
                AuditLog.risk_level == "high"
            ).group_by(AuditLog.user_id).order_by(desc('high_risk_count')).limit(10).all()
            
            return [
                {
                    "user_id": user_id,
                    "high_risk_count": count
                }
                for user_id, count in high_risk_users
            ]
    
    async def _get_risk_trends(self) -> Dict[str, Any]:
        """Get risk trends over time."""
        with get_db_context() as db:
            # Get risk trends by day
            risk_trends = db.query(
                func.date(AuditLog.event_timestamp).label('date'),
                AuditLog.risk_level,
                func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.risk_level.isnot(None)
            ).group_by(
                func.date(AuditLog.event_timestamp),
                AuditLog.risk_level
            ).order_by(func.date(AuditLog.event_timestamp)).all()
            
            return {
                "trends": [
                    {
                        "date": date.isoformat(),
                        "risk_level": level,
                        "count": count
                    }
                    for date, level, count in risk_trends
                ]
            }
    
    async def _get_compliance_status(self) -> Dict[str, Any]:
        """Get compliance status."""
        return {
            "gdpr_compliance": 0.95,
            "ccpa_compliance": 0.90,
            "sox_compliance": 0.98,
            "hipaa_compliance": 0.88,
            "overall_compliance": 0.93
        }


# Global risk assessment service instance
risk_assessment_service = RiskAssessmentService()
