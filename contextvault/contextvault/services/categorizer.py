"""
Context Categorization Engine
Automatically categorizes context entries by type and domain
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from ..models.context import ContextEntry, ContextCategory, ContextType


@dataclass
class CategorizationResult:
    """Result of context categorization."""
    context_category: ContextCategory
    context_type: ContextType
    confidence: float
    reasoning: str
    suggested_tags: List[str]


class ContextCategorizer:
    """Automatically categorizes context entries."""
    
    def __init__(self):
        # Define categorization patterns
        self.category_patterns = {
            ContextCategory.PERSONAL_INFO: [
                r"my name is", r"i am", r"i'm", r"i live in", r"i work at",
                r"i was born", r"my age is", r"i am from", r"my hometown",
                r"my occupation", r"my profession", r"i am a", r"i work as"
            ],
            ContextCategory.PREFERENCES: [
                r"i like", r"i love", r"i enjoy", r"i prefer", r"my favorite",
                r"i hate", r"i dislike", r"i'm not a fan of", r"i don't like",
                r"i'm interested in", r"i'm passionate about", r"i'm into"
            ],
            ContextCategory.GOALS: [
                r"i want to", r"i hope to", r"i plan to", r"my goal is",
                r"i aspire to", r"i dream of", r"my objective is", r"i'm trying to",
                r"i'm working toward", r"my target is", r"i aim to"
            ],
            ContextCategory.SKILLS: [
                r"i can", r"i know how to", r"i'm good at", r"i'm skilled in",
                r"i have experience with", r"i'm proficient in", r"i'm expert in",
                r"i've mastered", r"i'm learning", r"i'm studying"
            ],
            ContextCategory.WORK: [
                r"my job", r"my work", r"my company", r"my employer",
                r"my role", r"my position", r"my team", r"my manager",
                r"my colleague", r"my workplace", r"my office"
            ],
            ContextCategory.PROJECTS: [
                r"my project", r"i'm working on", r"i'm building", r"i'm developing",
                r"my current project", r"the project i'm doing", r"i'm creating",
                r"i'm designing", r"i'm implementing"
            ],
            ContextCategory.RELATIONSHIPS: [
                r"my friend", r"my family", r"my colleague", r"my partner",
                r"my spouse", r"my parent", r"my child", r"my sibling",
                r"i know", r"i met", r"i was introduced to"
            ],
            ContextCategory.TECHNICAL: [
                r"programming", r"coding", r"software", r"algorithm", r"database",
                r"api", r"framework", r"library", r"debug", r"deploy",
                r"python", r"javascript", r"java", r"react", r"node", r"docker"
            ]
        }
        
        # Define context type patterns
        self.type_patterns = {
            ContextType.PERSONAL_INFO: [
                r"name", r"age", r"location", r"occupation", r"profession",
                r"hometown", r"birthday", r"address"
            ],
            ContextType.PREFERENCE: [
                r"like", r"love", r"prefer", r"favorite", r"hate", r"dislike"
            ],
            ContextType.GOAL: [
                r"goal", r"plan", r"objective", r"target", r"dream", r"aspire"
            ],
            ContextType.SKILL: [
                r"skill", r"ability", r"expertise", r"proficient", r"experienced"
            ],
            ContextType.RELATIONSHIP: [
                r"friend", r"family", r"colleague", r"partner", r"relationship"
            ],
            ContextType.PROJECT: [
                r"project", r"work", r"build", r"develop", r"create", r"design"
            ]
        }
        
        # Domain classification patterns
        self.domain_patterns = {
            "technical": [
                r"programming", r"coding", r"software", r"technology", r"computer",
                r"algorithm", r"database", r"api", r"framework", r"library",
                r"python", r"javascript", r"java", r"react", r"node", r"docker",
                r"git", r"linux", r"cloud", r"aws", r"azure"
            ],
            "personal": [
                r"family", r"friend", r"hobby", r"interest", r"personal",
                r"relationship", r"emotion", r"feeling", r"private"
            ],
            "professional": [
                r"work", r"job", r"career", r"business", r"meeting",
                r"project", r"team", r"manager", r"company", r"employer"
            ]
        }
    
    def categorize_context(self, content: str) -> CategorizationResult:
        """
        Categorize a context entry based on its content.
        
        Args:
            content: The context content to categorize
            
        Returns:
            CategorizationResult with category, type, confidence, and reasoning
        """
        content_lower = content.lower()
        
        # Analyze category
        category_result = self._analyze_category(content_lower)
        
        # Analyze context type
        type_result = self._analyze_context_type(content_lower)
        
        # Generate suggested tags
        suggested_tags = self._generate_suggested_tags(content_lower)
        
        # Combine confidence scores
        combined_confidence = (category_result["confidence"] + type_result["confidence"]) / 2
        
        # Generate reasoning
        reasoning = f"Category: {category_result['reasoning']}. Type: {type_result['reasoning']}."
        
        return CategorizationResult(
            context_category=category_result["category"],
            context_type=type_result["type"],
            confidence=combined_confidence,
            reasoning=reasoning,
            suggested_tags=suggested_tags
        )
    
    def _analyze_category(self, content: str) -> Dict[str, Any]:
        """Analyze the category of the context."""
        category_scores = {}
        
        for category, patterns in self.category_patterns.items():
            score = 0
            matched_patterns = []
            
            for pattern in patterns:
                if re.search(pattern, content):
                    score += 1
                    matched_patterns.append(pattern)
            
            if score > 0:
                category_scores[category] = {
                    "score": score,
                    "matched_patterns": matched_patterns,
                    "confidence": min(1.0, score / len(patterns) + 0.2)
                }
        
        # Determine best category
        if category_scores:
            best_category = max(category_scores.keys(), key=lambda k: category_scores[k]["score"])
            confidence = category_scores[best_category]["confidence"]
            reasoning = f"Matched {len(category_scores[best_category]['matched_patterns'])} patterns for {best_category}"
        else:
            # Default to OTHER category
            best_category = ContextCategory.OTHER
            confidence = 0.1
            reasoning = "No specific category patterns matched"
        
        return {
            "category": best_category,
            "confidence": confidence,
            "reasoning": reasoning
        }
    
    def _analyze_context_type(self, content: str) -> Dict[str, Any]:
        """Analyze the context type."""
        type_scores = {}
        
        for context_type, patterns in self.type_patterns.items():
            score = 0
            matched_patterns = []
            
            for pattern in patterns:
                if re.search(pattern, content):
                    score += 1
                    matched_patterns.append(pattern)
            
            if score > 0:
                type_scores[context_type] = {
                    "score": score,
                    "matched_patterns": matched_patterns,
                    "confidence": min(1.0, score / len(patterns) + 0.3)
                }
        
        # Determine best type
        if type_scores:
            best_type = max(type_scores.keys(), key=lambda k: type_scores[k]["score"])
            confidence = type_scores[best_type]["confidence"]
            reasoning = f"Matched {len(type_scores[best_type]['matched_patterns'])} patterns for {best_type}"
        else:
            # Default to NOTE type
            best_type = ContextType.NOTE
            confidence = 0.1
            reasoning = "No specific type patterns matched"
        
        return {
            "type": best_type,
            "confidence": confidence,
            "reasoning": reasoning
        }
    
    def _generate_suggested_tags(self, content: str) -> List[str]:
        """Generate suggested tags based on content analysis."""
        tags = []
        
        # Extract domain tags
        for domain, patterns in self.domain_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    tags.append(domain)
                    break
        
        # Extract keyword tags
        keywords = re.findall(r'\b[a-z]{4,}\b', content)
        
        # Filter and score keywords
        keyword_scores = {}
        for keyword in keywords:
            if keyword not in ["that", "this", "with", "from", "they", "have", "been", "will", "would", "could", "should"]:
                keyword_scores[keyword] = keyword_scores.get(keyword, 0) + 1
        
        # Add top keywords as tags
        top_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        for keyword, _ in top_keywords:
            if keyword not in tags:
                tags.append(keyword)
        
        # Add auto-extracted tag if content seems automatically extracted
        if any(indicator in content for indicator in ["i am", "i work", "i like", "my name"]):
            tags.append("auto_extracted")
        
        return tags[:5]  # Limit to 5 tags
    
    def batch_categorize_contexts(self, contexts: List[ContextEntry]) -> List[CategorizationResult]:
        """Categorize multiple contexts in batch."""
        results = []
        for context in contexts:
            result = self.categorize_context(context.content)
            results.append(result)
        return results
    
    def update_context_categorization(self, context: ContextEntry) -> ContextEntry:
        """Update a context entry with new categorization."""
        result = self.categorize_context(context.content)
        
        # Update fields if confidence is high enough
        if result.confidence > 0.5:
            context.context_category = result.context_category
            context.context_type = result.context_type
            
            # Add suggested tags
            if not context.tags:
                context.tags = []
            for tag in result.suggested_tags:
                if tag not in context.tags:
                    context.tags.append(tag)
        
        return context
    
    def get_category_statistics(self) -> Dict[ContextCategory, int]:
        """Get statistics about context categories."""
        from ..database import get_db_context
        
        stats = {}
        with get_db_context() as db:
            for category in ContextCategory:
                count = db.query(ContextEntry).filter(ContextEntry.context_category == category).count()
                stats[category] = count
        
        return stats
    
    def suggest_category_improvements(self) -> List[Dict[str, Any]]:
        """Suggest improvements for context categorization."""
        suggestions = []
        
        # Get uncategorized contexts
        from ..database import get_db_context
        with get_db_context() as db:
            uncategorized = db.query(ContextEntry).filter(
                ContextEntry.context_category == ContextCategory.OTHER
            ).limit(10).all()
        
        if uncategorized:
            suggestions.append({
                "type": "uncategorized_contexts",
                "count": len(uncategorized),
                "message": f"Found {len(uncategorized)} contexts that need categorization",
                "action": "Run batch categorization on these contexts"
            })
        
        # Get low-confidence contexts
        with get_db_context() as db:
            low_confidence = db.query(ContextEntry).filter(
                ContextEntry.confidence_score < 0.5
            ).count()
        
        if low_confidence > 0:
            suggestions.append({
                "type": "low_confidence_contexts",
                "count": low_confidence,
                "message": f"Found {low_confidence} contexts with low confidence scores",
                "action": "Review and validate these contexts"
            })
        
        return suggestions


# Global instance
context_categorizer = ContextCategorizer()
