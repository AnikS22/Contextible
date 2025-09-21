"""
User Feedback System for ContextVault

Allows users to rate AI responses and provides feedback-driven improvements
to the context retrieval and injection system.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db_context
from ..models.context import ContextEntry

logger = logging.getLogger(__name__)


@dataclass
class ResponseFeedback:
    """User feedback for an AI response."""
    session_id: str
    model_id: str
    user_prompt: str
    ai_response: str
    context_used: List[Dict[str, Any]]
    rating: int  # 1-5 scale
    feedback_text: Optional[str] = None
    timestamp: datetime = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class FeedbackAnalytics:
    """Analytics derived from user feedback."""
    total_feedback_count: int
    average_rating: float
    rating_distribution: Dict[int, int]
    context_type_effectiveness: Dict[str, float]
    most_helpful_context_entries: List[Dict[str, Any]]
    improvement_suggestions: List[str]
    last_updated: datetime


class UserFeedbackService:
    """Service for managing user feedback and learning from it."""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.feedback_history: List[ResponseFeedback] = []
        self.max_memory_feedback = 1000  # Keep last 1000 feedback items in memory
    
    def submit_feedback(
        self,
        session_id: str,
        model_id: str,
        user_prompt: str,
        ai_response: str,
        context_used: List[Dict[str, Any]],
        rating: int,
        feedback_text: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Submit user feedback for an AI response.
        
        Args:
            session_id: Unique session identifier
            model_id: AI model that generated the response
            user_prompt: User's original query
            ai_response: AI's response
            context_used: Context entries that were injected
            rating: User rating (1-5 scale, 5 = very helpful)
            feedback_text: Optional text feedback
            user_id: Optional user identifier
            
        Returns:
            True if feedback was submitted successfully
        """
        try:
            if not 1 <= rating <= 5:
                logger.error(f"Invalid rating {rating}. Must be between 1 and 5.")
                return False
            
            feedback = ResponseFeedback(
                session_id=session_id,
                model_id=model_id,
                user_prompt=user_prompt,
                ai_response=ai_response,
                context_used=context_used,
                rating=rating,
                feedback_text=feedback_text,
                user_id=user_id
            )
            
            # Store in memory
            self.feedback_history.append(feedback)
            if len(self.feedback_history) > self.max_memory_feedback:
                self.feedback_history.pop(0)  # Remove oldest feedback
            
            # Store in database (using metadata field for now)
            if self.db_session:
                self._store_feedback_in_db(feedback)
            
            logger.info(f"Feedback submitted for session {session_id}: rating {rating}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}")
            return False
    
    def _store_feedback_in_db(self, feedback: ResponseFeedback):
        """Store feedback in database using context entry metadata."""
        try:
            # Create a context entry to store feedback
            feedback_content = f"User feedback: Rating {feedback.rating}/5 for session {feedback.session_id}"
            if feedback.feedback_text:
                feedback_content += f"\n\nFeedback: {feedback.feedback_text}"
            
            # Store as a special context entry
            feedback_entry = ContextEntry(
                content=feedback_content,
                context_type="note",  # Using string instead of enum for now
                source="user_feedback",
                tags=["feedback", f"rating_{feedback.rating}", feedback.model_id],
                entry_metadata={
                    "session_id": feedback.session_id,
                    "model_id": feedback.model_id,
                    "user_prompt": feedback.user_prompt,
                    "ai_response": feedback.ai_response,
                    "context_used": feedback.context_used,
                    "rating": feedback.rating,
                    "feedback_text": feedback.feedback_text,
                    "user_id": feedback.user_id,
                    "timestamp": feedback.timestamp.isoformat()
                }
            )
            
            self.db_session.add(feedback_entry)
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Failed to store feedback in database: {e}")
    
    def get_feedback_for_session(self, session_id: str) -> Optional[ResponseFeedback]:
        """Get feedback for a specific session."""
        for feedback in self.feedback_history:
            if feedback.session_id == session_id:
                return feedback
        return None
    
    def get_recent_feedback(self, limit: int = 10) -> List[ResponseFeedback]:
        """Get recent feedback entries."""
        return self.feedback_history[-limit:]
    
    def calculate_analytics(self, days: int = 30) -> FeedbackAnalytics:
        """Calculate feedback analytics for the specified time period."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter feedback by date
        recent_feedback = [
            f for f in self.feedback_history 
            if f.timestamp >= cutoff_date
        ]
        
        if not recent_feedback:
            return FeedbackAnalytics(
                total_feedback_count=0,
                average_rating=0.0,
                rating_distribution={},
                context_type_effectiveness={},
                most_helpful_context_entries=[],
                improvement_suggestions=[],
                last_updated=datetime.now()
            )
        
        # Calculate basic statistics
        total_count = len(recent_feedback)
        average_rating = sum(f.rating for f in recent_feedback) / total_count
        
        # Rating distribution
        rating_distribution = {}
        for rating in range(1, 6):
            rating_distribution[rating] = sum(1 for f in recent_feedback if f.rating == rating)
        
        # Context type effectiveness
        context_type_effectiveness = self._calculate_context_type_effectiveness(recent_feedback)
        
        # Most helpful context entries
        most_helpful_context = self._find_most_helpful_context_entries(recent_feedback)
        
        # Improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(recent_feedback, average_rating)
        
        return FeedbackAnalytics(
            total_feedback_count=total_count,
            average_rating=average_rating,
            rating_distribution=rating_distribution,
            context_type_effectiveness=context_type_effectiveness,
            most_helpful_context_entries=most_helpful_context,
            improvement_suggestions=improvement_suggestions,
            last_updated=datetime.now()
        )
    
    def _calculate_context_type_effectiveness(self, feedback: List[ResponseFeedback]) -> Dict[str, float]:
        """Calculate effectiveness scores for different context types."""
        context_type_ratings = {}
        context_type_counts = {}
        
        for f in feedback:
            for context_entry in f.context_used:
                context_type = context_entry.get("context_type", "unknown")
                
                if context_type not in context_type_ratings:
                    context_type_ratings[context_type] = 0
                    context_type_counts[context_type] = 0
                
                context_type_ratings[context_type] += f.rating
                context_type_counts[context_type] += 1
        
        # Calculate average ratings
        effectiveness = {}
        for context_type in context_type_ratings:
            if context_type_counts[context_type] > 0:
                effectiveness[context_type] = context_type_ratings[context_type] / context_type_counts[context_type]
        
        return effectiveness
    
    def _find_most_helpful_context_entries(self, feedback: List[ResponseFeedback]) -> List[Dict[str, Any]]:
        """Find context entries that consistently receive high ratings."""
        context_entry_ratings = {}
        
        for f in feedback:
            for context_entry in f.context_used:
                entry_id = context_entry.get("id", "unknown")
                
                if entry_id not in context_entry_ratings:
                    context_entry_ratings[entry_id] = {
                        "ratings": [],
                        "context_entry": context_entry
                    }
                
                context_entry_ratings[entry_id]["ratings"].append(f.rating)
        
        # Calculate average ratings and filter for helpful entries
        helpful_entries = []
        for entry_id, data in context_entry_ratings.items():
            if len(data["ratings"]) >= 2:  # At least 2 ratings
                avg_rating = sum(data["ratings"]) / len(data["ratings"])
                if avg_rating >= 4.0:  # High rating threshold
                    helpful_entries.append({
                        "entry_id": entry_id,
                        "content_preview": data["context_entry"].get("content", "")[:100],
                        "context_type": data["context_entry"].get("context_type"),
                        "average_rating": avg_rating,
                        "rating_count": len(data["ratings"])
                    })
        
        # Sort by average rating
        helpful_entries.sort(key=lambda x: x["average_rating"], reverse=True)
        return helpful_entries[:5]  # Top 5 most helpful entries
    
    def _generate_improvement_suggestions(self, feedback: List[ResponseFeedback], average_rating: float) -> List[str]:
        """Generate improvement suggestions based on feedback analysis."""
        suggestions = []
        
        # Low average rating
        if average_rating < 3.0:
            suggestions.append("Overall rating is low. Consider improving context relevance and template effectiveness.")
        
        # High variance in ratings
        ratings = [f.rating for f in feedback]
        if len(ratings) > 1:
            rating_variance = sum((r - average_rating) ** 2 for r in ratings) / len(ratings)
            if rating_variance > 2.0:
                suggestions.append("High variance in ratings suggests inconsistent context quality. Review context retrieval algorithm.")
        
        # Context type analysis
        context_type_effectiveness = self._calculate_context_type_effectiveness(feedback)
        low_effectiveness_types = [
            ctx_type for ctx_type, effectiveness in context_type_effectiveness.items()
            if effectiveness < 3.0
        ]
        
        if low_effectiveness_types:
            suggestions.append(f"Low effectiveness for context types: {', '.join(low_effectiveness_types)}. Consider improving these types.")
        
        # Empty context feedback
        empty_context_feedback = [f for f in feedback if not f.context_used]
        if len(empty_context_feedback) / len(feedback) > 0.3:
            suggestions.append("High percentage of responses without context. Improve context retrieval coverage.")
        
        # Negative feedback analysis
        negative_feedback = [f for f in feedback if f.rating <= 2 and f.feedback_text]
        if negative_feedback:
            common_complaints = self._analyze_negative_feedback(negative_feedback)
            if common_complaints:
                suggestions.append(f"Common complaints: {', '.join(common_complaints)}. Address these issues.")
        
        return suggestions
    
    def _analyze_negative_feedback(self, negative_feedback: List[ResponseFeedback]) -> List[str]:
        """Analyze negative feedback text for common complaints."""
        complaints = []
        
        # Simple keyword analysis
        complaint_keywords = {
            "irrelevant": ["irrelevant", "not relevant", "doesn't apply", "wrong context"],
            "generic": ["generic", "not personal", "could be anyone", "not specific"],
            "incomplete": ["incomplete", "missing", "didn't include", "left out"],
            "confusing": ["confusing", "unclear", "hard to understand", "doesn't make sense"]
        }
        
        for feedback in negative_feedback:
            if feedback.feedback_text:
                feedback_lower = feedback.feedback_text.lower()
                for complaint_type, keywords in complaint_keywords.items():
                    if any(keyword in feedback_lower for keyword in keywords):
                        if complaint_type not in complaints:
                            complaints.append(complaint_type)
        
        return complaints
    
    def get_learning_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for improving the system based on feedback."""
        analytics = self.calculate_analytics()
        
        recommendations = {
            "context_retrieval": [],
            "template_improvements": [],
            "system_optimization": [],
            "priority": "medium"
        }
        
        # Context retrieval recommendations
        if analytics.context_type_effectiveness:
            worst_context_type = min(
                analytics.context_type_effectiveness.items(),
                key=lambda x: x[1]
            )
            recommendations["context_retrieval"].append(
                f"Improve {worst_context_type[0]} context type (current effectiveness: {worst_context_type[1]:.2f})"
            )
        
        # Template recommendations
        if analytics.average_rating < 3.5:
            recommendations["template_improvements"].append(
                "Consider using stronger context injection templates"
            )
        
        # System optimization
        if analytics.total_feedback_count > 0:
            low_rated_feedback = sum(1 for r in analytics.rating_distribution.values() for rating in range(1, 4) if r)
            if low_rated_feedback / analytics.total_feedback_count > 0.4:
                recommendations["system_optimization"].append(
                    "High percentage of low-rated responses - consider overall system review"
                )
        
        # Set priority
        if analytics.average_rating < 2.5:
            recommendations["priority"] = "high"
        elif analytics.average_rating < 3.5:
            recommendations["priority"] = "medium"
        else:
            recommendations["priority"] = "low"
        
        return recommendations


# Global feedback service instance
_feedback_service = None


def get_feedback_service() -> UserFeedbackService:
    """Get the global feedback service instance."""
    global _feedback_service
    
    if _feedback_service is None:
        _feedback_service = UserFeedbackService()
    
    return _feedback_service


def submit_response_feedback(
    session_id: str,
    model_id: str,
    user_prompt: str,
    ai_response: str,
    context_used: List[Dict[str, Any]],
    rating: int,
    feedback_text: Optional[str] = None,
    user_id: Optional[str] = None
) -> bool:
    """
    Convenience function to submit response feedback.
    
    This is the main function to call when you want to collect
    user feedback on AI responses.
    """
    service = get_feedback_service()
    return service.submit_feedback(
        session_id=session_id,
        model_id=model_id,
        user_prompt=user_prompt,
        ai_response=ai_response,
        context_used=context_used,
        rating=rating,
        feedback_text=feedback_text,
        user_id=user_id
    )
