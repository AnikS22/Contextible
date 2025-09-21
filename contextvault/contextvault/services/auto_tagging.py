"""Auto-tagging service for context entries."""

import logging
import re
from typing import Any, Dict, List, Optional, Set
from collections import Counter

from ..models.context import ContextEntry, ContextCategory, ContextType
from ..database import get_db_context

logger = logging.getLogger(__name__)


class AutoTaggingService:
    """Service for automatically generating tags for context entries."""
    
    def __init__(self):
        """Initialize the auto-tagging service."""
        self.logger = logging.getLogger(__name__)
        
        # Predefined tag patterns
        self.tag_patterns = {
            "programming": [
                r"\b(python|java|javascript|typescript|go|rust|c\+\+|c#|php|ruby|swift|kotlin)\b",
                r"\b(function|class|method|variable|loop|if|else|try|catch|import|export)\b",
                r"\b(api|database|sql|json|xml|html|css|react|vue|angular)\b"
            ],
            "work": [
                r"\b(meeting|project|deadline|client|customer|team|manager|boss|colleague)\b",
                r"\b(presentation|report|document|email|call|conference|workshop)\b",
                r"\b(company|office|workplace|job|career|promotion|salary|benefits)\b"
            ],
            "personal": [
                r"\b(family|friend|relationship|marriage|children|parent|sibling)\b",
                r"\b(hobby|interest|passion|love|like|enjoy|fun|entertainment)\b",
                r"\b(health|fitness|exercise|diet|medical|doctor|hospital)\b"
            ],
            "location": [
                r"\b(home|house|apartment|room|kitchen|bedroom|office|school|university)\b",
                r"\b(city|country|state|street|avenue|road|place|location|address)\b",
                r"\b(travel|trip|vacation|holiday|visit|tour|journey)\b"
            ],
            "time": [
                r"\b(today|yesterday|tomorrow|morning|afternoon|evening|night)\b",
                r"\b(week|month|year|season|spring|summer|autumn|winter)\b",
                r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
            ],
            "technology": [
                r"\b(computer|laptop|phone|tablet|device|software|app|website|internet)\b",
                r"\b(ai|artificial intelligence|machine learning|data|algorithm|model)\b",
                r"\b(cloud|server|database|security|privacy|encryption|blockchain)\b"
            ]
        }
        
        # Category-specific keywords
        self.category_keywords = {
            ContextCategory.PERSONAL_INFO: [
                "name", "age", "birthday", "address", "phone", "email", "location"
            ],
            ContextCategory.PREFERENCES: [
                "like", "love", "favorite", "prefer", "enjoy", "hate", "dislike"
            ],
            ContextCategory.WORK: [
                "job", "work", "company", "office", "career", "profession", "business"
            ],
            ContextCategory.SKILLS: [
                "skill", "ability", "talent", "expertise", "knowledge", "experience"
            ],
            ContextCategory.GOALS: [
                "goal", "objective", "target", "plan", "ambition", "dream", "aspiration"
            ],
            ContextCategory.RELATIONSHIPS: [
                "friend", "family", "relationship", "partner", "colleague", "acquaintance"
            ],
            ContextCategory.PROJECTS: [
                "project", "task", "assignment", "work", "development", "creation"
            ]
        }
    
    async def generate_tags(self, 
                          content: str, 
                          context_type: ContextType,
                          existing_tags: Optional[List[str]] = None) -> List[str]:
        """
        Generate tags for a context entry.
        
        Args:
            content: The context content
            context_type: Type of context
            existing_tags: Existing tags to consider
            
        Returns:
            List of generated tags
        """
        tags = set(existing_tags or [])
        
        # Generate tags based on patterns
        pattern_tags = await self._generate_pattern_tags(content)
        tags.update(pattern_tags)
        
        # Generate tags based on keywords
        keyword_tags = await self._generate_keyword_tags(content)
        tags.update(keyword_tags)
        
        # Generate tags based on context type
        type_tags = await self._generate_type_tags(content, context_type)
        tags.update(type_tags)
        
        # Generate tags based on content analysis
        analysis_tags = await self._analyze_content(content)
        tags.update(analysis_tags)
        
        # Clean and validate tags
        cleaned_tags = self._clean_tags(list(tags))
        
        # Limit number of tags
        return cleaned_tags[:10]
    
    async def suggest_category(self, content: str) -> ContextCategory:
        """
        Suggest a category for a context entry.
        
        Args:
            content: The context content
            
        Returns:
            Suggested category
        """
        content_lower = content.lower()
        
        # Score each category based on keyword matches
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in content_lower:
                    score += 1
            
            category_scores[category] = score
        
        # Return the category with the highest score
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category
        
        # Default to OTHER if no clear category
        return ContextCategory.OTHER
    
    async def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from content.
        
        Args:
            content: The context content
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of extracted keywords
        """
        # Clean and tokenize content
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        filtered_words = [word for word in words if word not in stop_words]
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        
        # Return most common words
        return [word for word, count in word_counts.most_common(max_keywords)]
    
    async def learn_from_user_tags(self, 
                                 user_tags: List[str],
                                 content: str,
                                 context_type: ContextType) -> None:
        """
        Learn from user-provided tags to improve future tagging.
        
        Args:
            user_tags: Tags provided by user
            content: The context content
            context_type: Type of context
        """
        # This would implement machine learning to improve tagging
        # For now, we'll just log the learning data
        self.logger.info(f"Learning from user tags: {user_tags} for {context_type.value}")
        
        # In a full implementation, this would:
        # 1. Store user tagging patterns
        # 2. Update tagging models
        # 3. Improve future tag suggestions
    
    async def get_tag_suggestions(self, 
                                content: str,
                                context_type: ContextType,
                                limit: int = 5) -> List[str]:
        """
        Get tag suggestions for content.
        
        Args:
            content: The context content
            context_type: Type of context
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested tags
        """
        # Generate tags
        tags = await self.generate_tags(content, context_type)
        
        # Get popular tags from similar contexts
        popular_tags = await self._get_popular_tags(context_type)
        
        # Combine and deduplicate
        all_suggestions = list(set(tags + popular_tags))
        
        # Return top suggestions
        return all_suggestions[:limit]
    
    async def _generate_pattern_tags(self, content: str) -> List[str]:
        """Generate tags based on predefined patterns."""
        tags = []
        content_lower = content.lower()
        
        for tag_category, patterns in self.tag_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    tags.append(tag_category)
                    break
        
        return tags
    
    async def _generate_keyword_tags(self, content: str) -> List[str]:
        """Generate tags based on keyword analysis."""
        tags = []
        content_lower = content.lower()
        
        # Extract keywords
        keywords = await self.extract_keywords(content, max_keywords=5)
        tags.extend(keywords)
        
        # Add specific keyword-based tags
        if any(word in content_lower for word in ["important", "critical", "urgent"]):
            tags.append("important")
        
        if any(word in content_lower for word in ["secret", "private", "confidential"]):
            tags.append("private")
        
        if any(word in content_lower for word in ["learn", "study", "education"]):
            tags.append("learning")
        
        return tags
    
    async def _generate_type_tags(self, content: str, context_type: ContextType) -> List[str]:
        """Generate tags based on context type."""
        tags = []
        
        # Add type-specific tags
        if context_type == ContextType.PROJECT:
            tags.append("project")
        elif context_type == ContextType.GOAL:
            tags.append("goal")
        elif context_type == ContextType.SKILL:
            tags.append("skill")
        elif context_type == ContextType.RELATIONSHIP:
            tags.append("relationship")
        elif context_type == ContextType.PREFERENCE:
            tags.append("preference")
        
        return tags
    
    async def _analyze_content(self, content: str) -> List[str]:
        """Analyze content for additional tags."""
        tags = []
        
        # Length-based tags
        if len(content) > 500:
            tags.append("long")
        elif len(content) < 50:
            tags.append("short")
        
        # Question-based tags
        if content.endswith("?"):
            tags.append("question")
        
        # List-based tags
        if any(marker in content for marker in ["1.", "2.", "3.", "-", "*"]):
            tags.append("list")
        
        # Date-based tags
        if re.search(r'\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{2}-\d{2}\b', content):
            tags.append("dated")
        
        return tags
    
    async def _get_popular_tags(self, context_type: ContextType) -> List[str]:
        """Get popular tags for a context type."""
        with get_db_context() as db:
            # Get all tags from contexts of this type
            contexts = db.query(ContextEntry).filter(
                ContextEntry.context_type == context_type
            ).all()
            
            all_tags = []
            for context in contexts:
                if context.tags:
                    all_tags.extend(context.tags)
            
            # Count tag frequencies
            tag_counts = Counter(all_tags)
            
            # Return most popular tags
            return [tag for tag, count in tag_counts.most_common(5)]
    
    def _clean_tags(self, tags: List[str]) -> List[str]:
        """Clean and validate tags."""
        cleaned = []
        
        for tag in tags:
            # Convert to lowercase
            tag = tag.lower().strip()
            
            # Remove special characters except hyphens and underscores
            tag = re.sub(r'[^a-zA-Z0-9\-_]', '', tag)
            
            # Skip empty or very short tags
            if len(tag) < 2:
                continue
            
            # Skip if already in cleaned list
            if tag in cleaned:
                continue
            
            cleaned.append(tag)
        
        return cleaned
    
    async def batch_tag_contexts(self, 
                               context_ids: List[str],
                               overwrite_existing: bool = False) -> Dict[str, List[str]]:
        """
        Batch tag multiple contexts.
        
        Args:
            context_ids: List of context IDs to tag
            overwrite_existing: Whether to overwrite existing tags
            
        Returns:
            Dictionary mapping context IDs to their new tags
        """
        results = {}
        
        with get_db_context() as db:
            for context_id in context_ids:
                context = db.query(ContextEntry).filter(
                    ContextEntry.id == context_id
                ).first()
                
                if not context:
                    continue
                
                # Generate new tags
                existing_tags = None if overwrite_existing else context.tags
                new_tags = await self.generate_tags(
                    context.content,
                    context.context_type,
                    existing_tags
                )
                
                # Update context
                context.tags = new_tags
                results[context_id] = new_tags
            
            db.commit()
        
        return results


# Global auto-tagging service instance
auto_tagging_service = AutoTaggingService()
