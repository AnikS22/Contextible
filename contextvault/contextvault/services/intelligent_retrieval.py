"""
Intelligent Context Retrieval System
Multi-factor scoring and smart context organization
"""

import re
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

from ..models.context import ContextEntry, ContextCategory, ContextType, ValidationStatus
from ..database import get_db_context


@dataclass
class RetrievalQuery:
    """Represents a context retrieval query with intent analysis."""
    text: str
    intent_type: str  # "personal_info", "preferences", "technical", "general"
    categories: List[ContextCategory]
    max_results: int = 10
    min_confidence: float = 0.3
    include_disputed: bool = False
    user_id: Optional[str] = None


@dataclass
class ContextScore:
    """Represents a scored context entry."""
    context: ContextEntry
    relevance_score: float
    recency_score: float
    confidence_score: float
    access_frequency_score: float
    category_relevance_score: float
    total_score: float
    match_reasons: List[str]


class QueryIntentAnalyzer:
    """Analyzes query intent to determine what type of context is needed."""
    
    def __init__(self):
        self.intent_patterns = {
            "personal_info": [
                r"who are you", r"what do you know about me", r"tell me about myself",
                r"my name", r"my age", r"where do I live", r"what do I do"
            ],
            "preferences": [
                r"what do I like", r"my favorite", r"prefer", r"preference",
                r"what do I enjoy", r"hobby", r"interest"
            ],
            "technical": [
                r"how to", r"code", r"programming", r"technical", r"debug",
                r"algorithm", r"architecture", r"system design"
            ],
            "goals": [
                r"goal", r"want to", r"planning to", r"objective", r"target",
                r"aspire", r"dream", r"ambition"
            ],
            "work": [
                r"work", r"job", r"career", r"employer", r"company",
                r"project", r"meeting", r"deadline"
            ],
            "relationships": [
                r"friend", r"family", r"colleague", r"relationship", r"know",
                r"met", r"introduced"
            ]
        }
    
    def analyze_intent(self, query: str) -> Tuple[str, List[ContextCategory]]:
        """
        Analyze query intent and return intent type and relevant categories.
        
        Args:
            query: The query text
            
        Returns:
            Tuple of (intent_type, relevant_categories)
        """
        query_lower = query.lower()
        intent_scores = defaultdict(int)
        
        # Score each intent type
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    intent_scores[intent_type] += 1
        
        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
        else:
            primary_intent = "general"
        
        # Map intent to categories
        intent_to_categories = {
            "personal_info": [ContextCategory.PERSONAL_INFO, ContextCategory.WORK],
            "preferences": [ContextCategory.PREFERENCES, ContextCategory.PERSONAL],
            "technical": [ContextCategory.TECHNICAL, ContextCategory.SKILLS, ContextCategory.PROJECTS],
            "goals": [ContextCategory.GOALS, ContextCategory.PROJECTS],
            "work": [ContextCategory.WORK, ContextCategory.PROJECTS, ContextCategory.PROFESSIONAL],
            "relationships": [ContextCategory.RELATIONSHIPS, ContextCategory.PERSONAL],
            "general": [ContextCategory.PERSONAL_INFO, ContextCategory.PREFERENCES, ContextCategory.WORK]
        }
        
        categories = intent_to_categories.get(primary_intent, [ContextCategory.OTHER])
        
        return primary_intent, categories


class IntelligentContextRetrieval:
    """Intelligent context retrieval with multi-factor scoring."""
    
    def __init__(self):
        self.intent_analyzer = QueryIntentAnalyzer()
        self.category_weights = {
            ContextCategory.PERSONAL_INFO: 1.0,
            ContextCategory.PREFERENCES: 0.9,
            ContextCategory.GOALS: 0.8,
            ContextCategory.WORK: 0.9,
            ContextCategory.SKILLS: 0.8,
            ContextCategory.PROJECTS: 0.7,
            ContextCategory.RELATIONSHIPS: 0.8,
            ContextCategory.TECHNICAL: 0.7,
            ContextCategory.PERSONAL: 0.8,
            ContextCategory.PROFESSIONAL: 0.9,
            ContextCategory.OTHER: 0.5
        }
    
    def retrieve_context(self, query: str, user_id: Optional[str] = None, max_results: int = 10) -> List[ContextScore]:
        """
        Retrieve context using intelligent multi-factor scoring.
        
        Args:
            query: The query text
            user_id: Optional user ID for filtering
            max_results: Maximum number of results to return
            
        Returns:
            List of scored context entries, sorted by total score
        """
        # Analyze query intent
        intent_type, relevant_categories = self.intent_analyzer.analyze_intent(query)
        
        # Create retrieval query
        retrieval_query = RetrievalQuery(
            text=query,
            intent_type=intent_type,
            categories=relevant_categories,
            max_results=max_results,
            user_id=user_id
        )
        
        # Get candidate contexts
        candidate_contexts = self._get_candidate_contexts(retrieval_query)
        
        # Score each context
        scored_contexts = []
        for context_dict in candidate_contexts:
            score = self._calculate_context_score_dict(context_dict, retrieval_query)
            scored_contexts.append(score)
        
        # Sort by total score and return top results
        scored_contexts.sort(key=lambda x: x.total_score, reverse=True)
        return scored_contexts[:max_results]
    
    def _get_candidate_contexts(self, query: RetrievalQuery) -> List[Dict[str, Any]]:
        """Get candidate contexts from database as dictionaries to avoid detached instances."""
        with get_db_context() as db:
            # Base query
            db_query = db.query(ContextEntry)
            
            # Filter by user if specified
            if query.user_id:
                db_query = db_query.filter(ContextEntry.user_id == query.user_id)
            
            # Filter by validation status
            if not query.include_disputed:
                db_query = db_query.filter(ContextEntry.validation_status != ValidationStatus.DISPUTED)
            
            # Filter by confidence
            db_query = db_query.filter(ContextEntry.confidence_score >= query.min_confidence)
            
            # Filter by categories if specified
            if query.categories:
                db_query = db_query.filter(ContextEntry.context_category.in_(query.categories))
            
            # Order by relevance and recency
            db_query = db_query.order_by(
                ContextEntry.access_count.desc(),
                ContextEntry.created_at.desc()
            )
            
            # Convert to dictionaries to avoid detached instances
            contexts = db_query.limit(query.max_results * 3).all()
            return [ctx.to_dict() for ctx in contexts]
    
    def _calculate_context_score_dict(self, context_dict: Dict[str, Any], query: RetrievalQuery) -> ContextScore:
        """Calculate multi-factor score for a context dictionary."""
        match_reasons = []
        
        # 1. Relevance score (text similarity)
        relevance_score = self._calculate_relevance_score(context_dict["content"], query.text)
        if relevance_score > 0.5:
            match_reasons.append(f"Text similarity: {relevance_score:.2f}")
        
        # 2. Recency score (how recent is this context)
        recency_score = self._calculate_recency_score(context_dict["created_at"])
        if recency_score > 0.7:
            match_reasons.append(f"Recent context: {recency_score:.2f}")
        
        # 3. Confidence score (how reliable is this information)
        confidence_score = context_dict.get("confidence_score", 0.5)
        if confidence_score > 0.8:
            match_reasons.append(f"High confidence: {confidence_score:.2f}")
        
        # 4. Access frequency score (how often is this used)
        access_frequency_score = self._calculate_access_frequency_score(context_dict.get("access_count", 0))
        if access_frequency_score > 0.5:
            match_reasons.append(f"Frequently accessed: {access_frequency_score:.2f}")
        
        # 5. Category relevance score
        category_relevance_score = self._calculate_category_relevance_score(
            context_dict.get("context_category", ContextCategory.OTHER), query.categories
        )
        if category_relevance_score > 0.7:
            match_reasons.append(f"Category match: {category_relevance_score:.2f}")
        
        # Calculate total score with weights
        total_score = (
            relevance_score * 0.4 +
            recency_score * 0.2 +
            confidence_score * 0.2 +
            access_frequency_score * 0.1 +
            category_relevance_score * 0.1
        )
        
        return ContextScore(
            context=context_dict,  # Store dict instead of ContextEntry
            relevance_score=relevance_score,
            recency_score=recency_score,
            confidence_score=confidence_score,
            access_frequency_score=access_frequency_score,
            category_relevance_score=category_relevance_score,
            total_score=total_score,
            match_reasons=match_reasons
        )
    
    def _calculate_context_score(self, context: ContextEntry, query: RetrievalQuery) -> ContextScore:
        """Calculate multi-factor score for a context entry."""
        match_reasons = []
        
        # 1. Relevance score (text similarity)
        relevance_score = self._calculate_relevance_score(context.content, query.text)
        if relevance_score > 0.5:
            match_reasons.append(f"Text similarity: {relevance_score:.2f}")
        
        # 2. Recency score (how recent is this context)
        recency_score = self._calculate_recency_score(context.created_at)
        if recency_score > 0.7:
            match_reasons.append(f"Recent context: {recency_score:.2f}")
        
        # 3. Confidence score (how reliable is this information)
        confidence_score = context.confidence_score or 0.5
        if confidence_score > 0.8:
            match_reasons.append(f"High confidence: {confidence_score:.2f}")
        
        # 4. Access frequency score (how often is this used)
        access_frequency_score = self._calculate_access_frequency_score(context.access_count or 0)
        if access_frequency_score > 0.5:
            match_reasons.append(f"Frequently accessed: {access_frequency_score:.2f}")
        
        # 5. Category relevance score
        category_relevance_score = self._calculate_category_relevance_score(
            context.context_category, query.categories
        )
        if category_relevance_score > 0.7:
            match_reasons.append(f"Category match: {category_relevance_score:.2f}")
        
        # Calculate total score with weights
        total_score = (
            relevance_score * 0.4 +
            recency_score * 0.2 +
            confidence_score * 0.2 +
            access_frequency_score * 0.1 +
            category_relevance_score * 0.1
        )
        
        return ContextScore(
            context=context,
            relevance_score=relevance_score,
            recency_score=recency_score,
            confidence_score=confidence_score,
            access_frequency_score=access_frequency_score,
            category_relevance_score=category_relevance_score,
            total_score=total_score,
            match_reasons=match_reasons
        )
    
    def _calculate_relevance_score(self, content: str, query: str) -> float:
        """Calculate text relevance score using keyword matching."""
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Extract keywords from query
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        content_words = set(re.findall(r'\b\w+\b', content_lower))
        
        if not query_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(query_words.intersection(content_words))
        union = len(query_words.union(content_words))
        
        if union == 0:
            return 0.0
        
        jaccard_score = intersection / union
        
        # Boost score for exact phrase matches
        if query_lower in content_lower:
            jaccard_score += 0.3
        
        # Boost score for important word matches
        important_words = {"work", "job", "company", "name", "like", "prefer", "love", "hate"}
        important_matches = len(query_words.intersection(important_words).intersection(content_words))
        if important_matches > 0:
            jaccard_score += important_matches * 0.1
        
        return min(1.0, jaccard_score)
    
    def _calculate_recency_score(self, created_at) -> float:
        """Calculate recency score based on creation date."""
        if not created_at:
            return 0.0
        
        # Handle both datetime objects and ISO strings
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                return 0.0
        
        now = datetime.utcnow()
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=None)
        
        age_days = (now - created_at).days
        
        # Score decreases with age
        if age_days <= 1:
            return 1.0
        elif age_days <= 7:
            return 0.9
        elif age_days <= 30:
            return 0.7
        elif age_days <= 90:
            return 0.5
        elif age_days <= 365:
            return 0.3
        else:
            return 0.1
    
    def _calculate_access_frequency_score(self, access_count: int) -> float:
        """Calculate access frequency score."""
        if access_count == 0:
            return 0.0
        elif access_count <= 5:
            return 0.3
        elif access_count <= 20:
            return 0.6
        elif access_count <= 50:
            return 0.8
        else:
            return 1.0
    
    def _calculate_category_relevance_score(self, context_category: ContextCategory, query_categories: List[ContextCategory]) -> float:
        """Calculate category relevance score."""
        if not query_categories:
            return 0.5
        
        if context_category in query_categories:
            return 1.0
        
        # Check for related categories
        related_categories = {
            ContextCategory.PERSONAL_INFO: [ContextCategory.WORK, ContextCategory.PERSONAL],
            ContextCategory.PREFERENCES: [ContextCategory.PERSONAL, ContextCategory.SKILLS],
            ContextCategory.WORK: [ContextCategory.PROFESSIONAL, ContextCategory.PROJECTS],
            ContextCategory.SKILLS: [ContextCategory.TECHNICAL, ContextCategory.WORK],
            ContextCategory.PROJECTS: [ContextCategory.WORK, ContextCategory.GOALS],
            ContextCategory.GOALS: [ContextCategory.PROJECTS, ContextCategory.PERSONAL],
        }
        
        related = related_categories.get(context_category, [])
        if any(cat in query_categories for cat in related):
            return 0.7
        
        return 0.0
    
    def get_context_relationships(self, context_id: str) -> List[ContextEntry]:
        """Get related contexts based on relationships."""
        with get_db_context() as db:
            # Get contexts with same parent
            parent_context = db.query(ContextEntry).filter(ContextEntry.id == context_id).first()
            if not parent_context:
                return []
            
            related_contexts = []
            
            # Get sibling contexts (same parent)
            if parent_context.parent_context_id:
                siblings = db.query(ContextEntry).filter(
                    ContextEntry.parent_context_id == parent_context.parent_context_id,
                    ContextEntry.id != context_id
                ).limit(5).all()
                related_contexts.extend(siblings)
            
            # Get child contexts
            children = db.query(ContextEntry).filter(
                ContextEntry.parent_context_id == context_id
            ).limit(5).all()
            related_contexts.extend(children)
            
            # Get contexts with similar tags
            if parent_context.tags:
                similar_tag_contexts = db.query(ContextEntry).filter(
                    ContextEntry.tags.contains(parent_context.tags),
                    ContextEntry.id != context_id
                ).limit(3).all()
                related_contexts.extend(similar_tag_contexts)
            
            return related_contexts
    
    def update_access_stats(self, context_ids: List[str]) -> None:
        """Update access statistics for retrieved contexts."""
        with get_db_context() as db:
            contexts = db.query(ContextEntry).filter(ContextEntry.id.in_(context_ids)).all()
            for context in contexts:
                context.access_count = (context.access_count or 0) + 1
                context.last_accessed_at = datetime.utcnow()
            db.commit()


# Global instance
intelligent_retrieval = IntelligentContextRetrieval()
