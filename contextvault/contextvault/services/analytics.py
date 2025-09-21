"""
Context Analytics System
Tracks usage, identifies gaps, and generates insights
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter

from ..models.context import ContextEntry, ContextCategory, ContextSource, ValidationStatus, ContextType
from ..database import get_db_context


@dataclass
class ContextGap:
    """Represents a gap in the user's context profile."""
    category: ContextCategory
    importance: float  # 0.0 to 1.0
    description: str
    suggested_questions: List[str]


@dataclass
class UsageInsight:
    """Represents an insight about context usage."""
    insight_type: str
    title: str
    description: str
    value: Any
    recommendation: str


@dataclass
class QualityReport:
    """Comprehensive quality report for context entries."""
    total_contexts: int
    category_distribution: Dict[ContextCategory, int]
    source_distribution: Dict[ContextSource, int]
    validation_status_distribution: Dict[ValidationStatus, int]
    average_confidence: float
    low_confidence_count: int
    gaps: List[ContextGap]
    insights: List[UsageInsight]
    quality_score: float


class ContextAnalytics:
    """Analytics engine for context management."""
    
    def __init__(self):
        self.category_importance_weights = {
            ContextCategory.PERSONAL_INFO: 1.0,
            ContextCategory.PREFERENCES: 0.8,
            ContextCategory.WORK: 0.9,
            ContextCategory.SKILLS: 0.8,
            ContextCategory.GOALS: 0.7,
            ContextCategory.RELATIONSHIPS: 0.6,
            ContextCategory.PROJECTS: 0.7,
            ContextCategory.TECHNICAL: 0.6,
            ContextCategory.PERSONAL: 0.8,
            ContextCategory.PROFESSIONAL: 0.9,
            ContextCategory.OTHER: 0.3
        }
        
        self.gap_suggestions = {
            ContextCategory.PERSONAL_INFO: [
                "What's your full name?",
                "Where are you from?",
                "What's your age or birth year?",
                "What do you do for work?"
            ],
            ContextCategory.PREFERENCES: [
                "What are your favorite foods?",
                "What music do you enjoy?",
                "What are your hobbies?",
                "What's your favorite programming language?"
            ],
            ContextCategory.WORK: [
                "What company do you work for?",
                "What's your job title?",
                "What projects are you working on?",
                "Who do you work with?"
            ],
            ContextCategory.SKILLS: [
                "What programming languages do you know?",
                "What tools do you use regularly?",
                "What are you learning?",
                "What are you good at?"
            ],
            ContextCategory.GOALS: [
                "What are your career goals?",
                "What do you want to learn?",
                "What projects do you want to work on?",
                "Where do you see yourself in 5 years?"
            ]
        }
    
    def generate_quality_report(self, user_id: Optional[str] = None) -> QualityReport:
        """
        Generate a comprehensive quality report for context entries.
        
        Args:
            user_id: Optional user ID for filtering
            
        Returns:
            QualityReport with comprehensive analytics
        """
        with get_db_context() as db:
            # Base query
            query = db.query(ContextEntry)
            if user_id:
                query = query.filter(ContextEntry.user_id == user_id)
            
            all_contexts = query.all()
            
            if not all_contexts:
                return QualityReport(
                    total_contexts=0,
                    category_distribution={},
                    source_distribution={},
                    validation_status_distribution={},
                    average_confidence=0.0,
                    low_confidence_count=0,
                    gaps=[],
                    insights=[],
                    quality_score=0.0
                )
            
            # Calculate distributions
            category_distribution = self._calculate_category_distribution(all_contexts)
            source_distribution = self._calculate_source_distribution(all_contexts)
            validation_status_distribution = self._calculate_validation_distribution(all_contexts)
            
            # Calculate metrics
            average_confidence = sum(ctx.confidence_score for ctx in all_contexts) / len(all_contexts)
            low_confidence_count = len([ctx for ctx in all_contexts if ctx.confidence_score < 0.5])
            
            # Identify gaps
            gaps = self._identify_context_gaps(category_distribution, all_contexts)
            
            # Generate insights
            insights = self._generate_usage_insights(all_contexts, category_distribution)
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(
                all_contexts, average_confidence, low_confidence_count, gaps
            )
            
            return QualityReport(
                total_contexts=len(all_contexts),
                category_distribution=category_distribution,
                source_distribution=source_distribution,
                validation_status_distribution=validation_status_distribution,
                average_confidence=average_confidence,
                low_confidence_count=low_confidence_count,
                gaps=gaps,
                insights=insights,
                quality_score=quality_score
            )
    
    def _calculate_category_distribution(self, contexts: List[ContextEntry]) -> Dict[ContextCategory, int]:
        """Calculate distribution of contexts by category."""
        distribution = defaultdict(int)
        for context in contexts:
            distribution[context.context_category] += 1
        return dict(distribution)
    
    def _calculate_source_distribution(self, contexts: List[ContextEntry]) -> Dict[ContextSource, int]:
        """Calculate distribution of contexts by source."""
        distribution = defaultdict(int)
        for context in contexts:
            distribution[context.context_source] += 1
        return dict(distribution)
    
    def _calculate_validation_distribution(self, contexts: List[ContextEntry]) -> Dict[ValidationStatus, int]:
        """Calculate distribution of contexts by validation status."""
        distribution = defaultdict(int)
        for context in contexts:
            distribution[context.validation_status] += 1
        return dict(distribution)
    
    def _identify_context_gaps(self, category_distribution: Dict[ContextCategory, int], contexts: List[ContextEntry]) -> List[ContextGap]:
        """Identify gaps in the user's context profile."""
        gaps = []
        total_contexts = sum(category_distribution.values())
        
        for category, importance_weight in self.category_importance_weights.items():
            count = category_distribution.get(category, 0)
            
            # Calculate expected minimum based on importance
            expected_minimum = max(1, int(total_contexts * importance_weight * 0.1))
            
            if count < expected_minimum:
                # Calculate gap importance
                gap_importance = importance_weight * (expected_minimum - count) / expected_minimum
                
                # Get suggestions for this category
                suggestions = self.gap_suggestions.get(category, [])
                
                category_str = category.value if hasattr(category, 'value') else str(category)
                gap = ContextGap(
                    category=category,
                    importance=gap_importance,
                    description=f"Only {count} context entries in {category_str} category (expected {expected_minimum})",
                    suggested_questions=suggestions[:3]  # Limit to 3 suggestions
                )
                gaps.append(gap)
        
        # Sort by importance
        gaps.sort(key=lambda x: x.importance, reverse=True)
        return gaps[:5]  # Return top 5 gaps
    
    def _generate_usage_insights(self, contexts: List[ContextEntry], category_distribution: Dict[ContextCategory, int]) -> List[UsageInsight]:
        """Generate insights about context usage."""
        insights = []
        
        # Insight 1: Most/Least used categories
        if category_distribution:
            most_used_category = max(category_distribution, key=category_distribution.get)
            least_used_category = min(category_distribution, key=category_distribution.get)
            
            most_used_str = most_used_category.value if hasattr(most_used_category, 'value') else str(most_used_category)
            insights.append(UsageInsight(
                insight_type="category_usage",
                title="Category Usage Distribution",
                description=f"Most used category: {most_used_str} ({category_distribution[most_used_category]} entries)",
                value=category_distribution,
                recommendation="Consider adding more context to underrepresented categories"
            ))
        
        # Insight 2: Confidence analysis
        confidence_scores = [ctx.confidence_score for ctx in contexts]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        insights.append(UsageInsight(
            insight_type="confidence_analysis",
            title="Context Confidence Analysis",
            description=f"Average confidence score: {avg_confidence:.2f}",
            value=avg_confidence,
            recommendation="Review low-confidence contexts and validate or improve them"
        ))
        
        # Insight 3: Access patterns
        access_counts = [ctx.access_count or 0 for ctx in contexts]
        total_accesses = sum(access_counts)
        avg_accesses = total_accesses / len(contexts) if contexts else 0
        
        insights.append(UsageInsight(
            insight_type="access_patterns",
            title="Context Access Patterns",
            description=f"Average access count: {avg_accesses:.1f} per context",
            value=avg_accesses,
            recommendation="Contexts with low access might need better organization or relevance"
        ))
        
        # Insight 4: Recent activity
        recent_contexts = [ctx for ctx in contexts if ctx.created_at > datetime.utcnow() - timedelta(days=7)]
        recent_percentage = len(recent_contexts) / len(contexts) * 100 if contexts else 0
        
        insights.append(UsageInsight(
            insight_type="recent_activity",
            title="Recent Context Activity",
            description=f"{len(recent_contexts)} contexts added in the last 7 days ({recent_percentage:.1f}%)",
            value=recent_percentage,
            recommendation="Good context growth! Keep adding relevant information"
        ))
        
        return insights
    
    def _calculate_quality_score(self, contexts: List[ContextEntry], avg_confidence: float, low_confidence_count: int, gaps: List[ContextGap]) -> float:
        """Calculate overall quality score."""
        if not contexts:
            return 0.0
        
        total_contexts = len(contexts)
        
        # Confidence component (40%)
        confidence_component = avg_confidence * 0.4
        
        # Coverage component (30%) - based on category distribution
        category_count = len(set(ctx.context_category for ctx in contexts))
        # Count all possible ContextCategory values
        max_categories = 11  # Hardcoded count of ContextCategory enum values
        coverage_component = (category_count / max_categories) * 0.3 if max_categories > 0 else 0
        
        # Validation component (20%) - based on confirmed contexts
        confirmed_count = len([ctx for ctx in contexts if ctx.validation_status == ValidationStatus.CONFIRMED])
        validation_component = (confirmed_count / total_contexts) * 0.2
        
        # Gap component (10%) - penalty for gaps
        gap_penalty = sum(gap.importance for gap in gaps) * 0.1
        gap_component = max(0, 0.1 - gap_penalty)
        
        quality_score = confidence_component + coverage_component + validation_component + gap_component
        return min(1.0, quality_score)
    
    def get_usage_statistics(self, user_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """Get usage statistics for the specified period."""
        with get_db_context() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = db.query(ContextEntry)
            if user_id:
                query = query.filter(ContextEntry.user_id == user_id)
            
            # Total contexts
            total_contexts = query.count()
            
            # Recent contexts
            recent_contexts = query.filter(ContextEntry.created_at >= cutoff_date).count()
            
            # Most accessed contexts
            most_accessed = query.order_by(ContextEntry.access_count.desc()).limit(5).all()
            
            # Contexts by source
            source_stats = {}
            for source in [ContextSource.MANUAL, ContextSource.EXTRACTED, ContextSource.CONVERSATION, ContextSource.IMPORTED, ContextSource.API]:
                count = query.filter(ContextEntry.context_source == source).count()
                if count > 0:
                    source_str = source.value if hasattr(source, 'value') else str(source)
                    source_stats[source_str] = count
            
            # Average confidence by category
            category_confidence = {}
            categories = [ContextCategory.PERSONAL_INFO, ContextCategory.PREFERENCES, ContextCategory.GOALS, 
                         ContextCategory.RELATIONSHIPS, ContextCategory.SKILLS, ContextCategory.WORK, 
                         ContextCategory.PROJECTS, ContextCategory.TECHNICAL, ContextCategory.PERSONAL, 
                         ContextCategory.PROFESSIONAL, ContextCategory.OTHER]
            for category in categories:
                category_contexts = query.filter(ContextEntry.context_category == category).all()
                if category_contexts:
                    avg_conf = sum(ctx.confidence_score for ctx in category_contexts) / len(category_contexts)
                    category_str = category.value if hasattr(category, 'value') else str(category)
                    category_confidence[category_str] = avg_conf
            
            return {
                "period_days": days,
                "total_contexts": total_contexts,
                "recent_contexts": recent_contexts,
                "growth_rate": recent_contexts / days if days > 0 else 0,
                "most_accessed": [
                    {"id": ctx.id, "content": ctx.content[:50], "access_count": ctx.access_count}
                    for ctx in most_accessed
                ],
                "source_distribution": source_stats,
                "category_confidence": category_confidence
            }
    
    def get_context_recommendations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recommendations for improving context profile."""
        recommendations = []
        
        # Generate quality report
        report = self.generate_quality_report(user_id)
        
        # Recommendation 1: Address gaps
        if report.gaps:
            top_gap = report.gaps[0]
            category_str = top_gap.category.value if hasattr(top_gap.category, 'value') else str(top_gap.category)
            recommendations.append({
                "type": "context_gap",
                "priority": "high",
                "title": f"Add more {category_str} context",
                "description": top_gap.description,
                "action": f"Consider asking: {top_gap.suggested_questions[0] if top_gap.suggested_questions else 'What else can you tell me about this category?'}"
            })
        
        # Recommendation 2: Improve confidence
        if report.average_confidence < 0.7:
            recommendations.append({
                "type": "confidence_improvement",
                "priority": "medium",
                "title": "Improve context confidence",
                "description": f"Average confidence is {report.average_confidence:.2f} - consider validating low-confidence contexts",
                "action": "Review and confirm contexts with confidence < 0.5"
            })
        
        # Recommendation 3: Validate pending contexts
        pending_count = report.validation_status_distribution.get(ValidationStatus.PENDING, 0)
        if pending_count > 5:
            recommendations.append({
                "type": "validation_needed",
                "priority": "medium",
                "title": "Validate pending contexts",
                "description": f"{pending_count} contexts are pending validation",
                "action": "Review and confirm or dispute pending contexts"
            })
        
        # Recommendation 4: Address disputed contexts
        disputed_count = report.validation_status_distribution.get(ValidationStatus.DISPUTED, 0)
        if disputed_count > 0:
            recommendations.append({
                "type": "resolve_disputes",
                "priority": "high",
                "title": "Resolve context disputes",
                "description": f"{disputed_count} contexts have conflicting information",
                "action": "Review and resolve conflicting context entries"
            })
        
        return recommendations
    
    def export_analytics_report(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Export comprehensive analytics report."""
        report = self.generate_quality_report(user_id)
        usage_stats = self.get_usage_statistics(user_id)
        recommendations = self.get_context_recommendations(user_id)
        
        return {
            "report_generated_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "quality_report": {
                "total_contexts": report.total_contexts,
                "quality_score": report.quality_score,
                "average_confidence": report.average_confidence,
                "category_distribution": {(k.value if hasattr(k, 'value') else str(k)): v for k, v in report.category_distribution.items()},
                "source_distribution": {(k.value if hasattr(k, 'value') else str(k)): v for k, v in report.source_distribution.items()},
                "validation_distribution": {(k.value if hasattr(k, 'value') else str(k)): v for k, v in report.validation_status_distribution.items()}
            },
            "usage_statistics": usage_stats,
            "gaps": [
                {
                    "category": gap.category.value if hasattr(gap.category, 'value') else str(gap.category),
                    "importance": gap.importance,
                    "description": gap.description,
                    "suggested_questions": gap.suggested_questions
                }
                for gap in report.gaps
            ],
            "insights": [
                {
                    "type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description,
                    "recommendation": insight.recommendation
                }
                for insight in report.insights
            ],
            "recommendations": recommendations
        }


# Global instance
context_analytics = ContextAnalytics()
