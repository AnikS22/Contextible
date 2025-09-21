"""
Context Deduplication Service
Prevents storing duplicate or conflicting context entries
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher

from .context_extractor import ExtractedContext
from ..models.context import ContextEntry


class ContextDeduplicator:
    """Handles deduplication of extracted context entries."""
    
    def __init__(self):
        self.similarity_threshold = 0.8  # Threshold for considering contexts similar
        self.conflict_threshold = 0.7    # Threshold for considering contexts conflicting
    
    def deduplicate_extracted_context(
        self, 
        new_contexts: List[ExtractedContext], 
        existing_contexts: List[ContextEntry]
    ) -> List[ExtractedContext]:
        """Deduplicate newly extracted context against existing context."""
        deduplicated = []
        
        # Extract content from existing contexts to avoid detached instance issues
        existing_contents = []
        for existing in existing_contexts:
            try:
                # Try to get content directly
                existing_contents.append(existing.content)
            except Exception:
                # Skip detached instances for now
                continue
        
        for new_context in new_contexts:
            is_duplicate = False
            
            # Check against existing content strings
            for existing_content in existing_contents:
                similarity = self._calculate_similarity(new_context.content, existing_content)
                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(new_context)
        
        # Merge similar contexts within the new batch
        merged = self._merge_similar_contexts(deduplicated)
        
        return merged
    
    def _is_similar_context(self, new_context: ExtractedContext, existing_context: ContextEntry) -> bool:
        """Check if two contexts are similar enough to be considered duplicates."""
        # Get content from existing context, handling detached instances
        try:
            existing_content = existing_context.content
        except Exception:
            # Handle detached instance by converting to string
            existing_content = str(existing_context)
        
        # Calculate similarity
        similarity = self._calculate_similarity(new_context.content, existing_content)
        
        return similarity >= self.similarity_threshold
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        # Normalize text
        text1_norm = self._normalize_text(text1)
        text2_norm = self._normalize_text(text2)
        
        # Use SequenceMatcher for similarity
        matcher = SequenceMatcher(None, text1_norm, text2_norm)
        return matcher.ratio()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Strip whitespace
        normalized = normalized.strip()
        
        return normalized
    
    def _merge_similar_contexts(self, contexts: List[ExtractedContext]) -> List[ExtractedContext]:
        """Merge similar contexts within a list."""
        if len(contexts) <= 1:
            return contexts
        
        merged = []
        processed = set()
        
        for i, context1 in enumerate(contexts):
            if i in processed:
                continue
            
            similar_contexts = [context1]
            
            # Find similar contexts
            for j, context2 in enumerate(contexts[i+1:], i+1):
                if j in processed:
                    continue
                
                similarity = self._calculate_similarity(context1.content, context2.content)
                if similarity >= self.similarity_threshold:
                    similar_contexts.append(context2)
                    processed.add(j)
            
            # Merge similar contexts
            if len(similar_contexts) > 1:
                merged_context = self._merge_context_group(similar_contexts)
                merged.append(merged_context)
            else:
                merged.append(context1)
            
            processed.add(i)
        
        return merged
    
    def _merge_context_group(self, contexts: List[ExtractedContext]) -> ExtractedContext:
        """Merge a group of similar contexts into one."""
        if len(contexts) == 1:
            return contexts[0]
        
        # Use the context with highest confidence as base
        base_context = max(contexts, key=lambda c: self._confidence_score(c.confidence))
        
        # Combine content (take the most complete version)
        combined_content = self._combine_content([c.content for c in contexts])
        
        # Combine tags
        all_tags = set()
        for context in contexts:
            all_tags.update(context.tags)
        
        # Combine metadata
        combined_metadata = base_context.metadata.copy()
        combined_metadata['merged_from'] = [c.message_id for c in contexts]
        combined_metadata['merge_count'] = len(contexts)
        
        return ExtractedContext(
            content=combined_content,
            context_type=base_context.context_type,
            confidence=base_context.confidence,  # Use highest confidence
            source=base_context.source,
            conversation_id=base_context.conversation_id,
            message_id=base_context.message_id,
            tags=list(all_tags),
            metadata=combined_metadata
        )
    
    def _confidence_score(self, confidence) -> int:
        """Convert confidence enum to numeric score."""
        from .context_extractor import ExtractionConfidence
        if confidence == ExtractionConfidence.HIGH:
            return 3
        elif confidence == ExtractionConfidence.MEDIUM:
            return 2
        else:
            return 1
    
    def _combine_content(self, contents: List[str]) -> str:
        """Combine multiple content strings into one."""
        if len(contents) == 1:
            return contents[0]
        
        # Find the longest content as base
        base_content = max(contents, key=len)
        
        # If all contents are very similar, return the longest
        similarities = [self._calculate_similarity(base_content, content) for content in contents]
        if all(sim >= 0.9 for sim in similarities):
            return base_content
        
        # Otherwise, try to combine intelligently
        # For now, return the longest content
        return base_content
    
    def detect_conflicts(self, new_contexts: List[ExtractedContext], existing_contexts: List[ContextEntry]) -> List[Dict[str, Any]]:
        """Detect potential conflicts between new and existing contexts."""
        conflicts = []
        
        for new_context in new_contexts:
            for existing in existing_contexts:
                conflict_type = self._detect_conflict_type(new_context, existing)
                if conflict_type:
                    conflicts.append({
                        "new_context": new_context,
                        "existing_context": existing,
                        "conflict_type": conflict_type,
                        "similarity": self._calculate_similarity(
                            new_context.content, 
                            existing.content if hasattr(existing, 'content') else str(existing)
                        )
                    })
        
        return conflicts
    
    def _detect_conflict_type(self, new_context: ExtractedContext, existing_context: ContextEntry) -> Optional[str]:
        """Detect the type of conflict between contexts."""
        existing_content = existing_context.content if hasattr(existing_context, 'content') else str(existing_context)
        
        # Check for direct contradictions
        if self._is_contradiction(new_context.content, existing_content):
            return "contradiction"
        
        # Check for conflicting preferences
        if self._is_preference_conflict(new_context.content, existing_content):
            return "preference_conflict"
        
        # Check for conflicting facts
        if self._is_fact_conflict(new_context.content, existing_content):
            return "fact_conflict"
        
        return None
    
    def _is_contradiction(self, text1: str, text2: str) -> bool:
        """Check if two texts directly contradict each other."""
        # Simple contradiction patterns
        contradictions = [
            ("i like", "i don't like"),
            ("i love", "i hate"),
            ("i prefer", "i don't prefer"),
            ("i am", "i'm not"),
            ("i have", "i don't have"),
        ]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        for positive, negative in contradictions:
            if positive in text1_lower and negative in text2_lower:
                return True
            if negative in text1_lower and positive in text2_lower:
                return True
        
        return False
    
    def _is_preference_conflict(self, text1: str, text2: str) -> bool:
        """Check if two texts represent conflicting preferences."""
        # This is a simplified check - in reality, this would be more sophisticated
        preference_keywords = ["prefer", "like", "love", "favorite", "best", "worst"]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # If both contain preference keywords but are about different things
        if any(keyword in text1_lower for keyword in preference_keywords) and \
           any(keyword in text2_lower for keyword in preference_keywords):
            
            # Check if they're about the same topic but with different preferences
            # This is a simplified implementation
            return False  # For now, return False to avoid false positives
        
        return False
    
    def _is_fact_conflict(self, text1: str, text2: str) -> bool:
        """Check if two texts represent conflicting facts."""
        # This is a simplified check - in reality, this would be more sophisticated
        fact_keywords = ["i am", "i have", "i live", "i work", "my name is"]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # If both contain fact keywords but contradict each other
        if any(keyword in text1_lower for keyword in fact_keywords) and \
           any(keyword in text2_lower for keyword in fact_keywords):
            
            # Check for direct contradictions in facts
            return self._is_contradiction(text1, text2)
        
        return False
    
    def get_deduplication_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics."""
        return {
            "similarity_threshold": self.similarity_threshold,
            "conflict_threshold": self.conflict_threshold,
            "supported_conflict_types": ["contradiction", "preference_conflict", "fact_conflict"]
        }


# Global context deduplicator instance
context_deduplicator = ContextDeduplicator()