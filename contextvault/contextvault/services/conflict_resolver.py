"""
Context Conflict Resolution System
Handles conflicting context entries and intelligent merging
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from difflib import SequenceMatcher

from ..models.context import ContextEntry, ContextCategory, ValidationStatus, ContextType
from ..database import get_db_context


@dataclass
class ConflictDetection:
    """Represents a detected conflict between contexts."""
    context1: ContextEntry
    context2: ContextEntry
    conflict_type: str  # "contradiction", "update", "duplicate"
    confidence: float
    reasoning: str
    suggested_action: str


@dataclass
class MergeResult:
    """Result of merging conflicting contexts."""
    merged_context: Optional[ContextEntry]
    conflicts_resolved: int
    actions_taken: List[str]
    confidence: float


class ContextConflictResolver:
    """Resolves conflicts between context entries."""
    
    def __init__(self):
        # Define conflict patterns
        self.conflict_patterns = {
            "name_conflict": [
                (r"my name is (\w+)", r"my name is (\w+)"),
                (r"i am (\w+)", r"i am (\w+)")
            ],
            "location_conflict": [
                (r"i live in ([^,]+)", r"i live in ([^,]+)"),
                (r"i'm from ([^,]+)", r"i'm from ([^,]+)")
            ],
            "work_conflict": [
                (r"i work at ([^,]+)", r"i work at ([^,]+)"),
                (r"i'm a ([^,]+) at ([^,]+)", r"i'm a ([^,]+) at ([^,]+)")
            ],
            "preference_conflict": [
                (r"i like ([^,]+)", r"i hate ([^,]+)"),
                (r"i prefer ([^,]+)", r"i don't like ([^,]+)")
            ]
        }
        
        # Define contradiction keywords
        self.contradiction_keywords = {
            "positive_negative": [
                ("like", "hate"), ("love", "hate"), ("prefer", "dislike"),
                ("good", "bad"), ("great", "terrible"), ("yes", "no")
            ],
            "temporal": [
                ("was", "am"), ("used to", "now"), ("before", "currently"),
                ("previously", "nowadays")
            ]
        }
    
    def detect_conflicts(self, contexts: List[ContextEntry]) -> List[ConflictDetection]:
        """
        Detect conflicts between context entries.
        
        Args:
            contexts: List of context entries to analyze
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Compare each pair of contexts
        for i in range(len(contexts)):
            for j in range(i + 1, len(contexts)):
                context1 = contexts[i]
                context2 = contexts[j]
                
                # Skip if contexts are too different in category
                if self._are_categories_incompatible(context1.context_category, context2.context_category):
                    continue
                
                # Check for various types of conflicts
                conflict = self._detect_specific_conflict(context1, context2)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _are_categories_incompatible(self, category1: ContextCategory, category2: ContextCategory) -> bool:
        """Check if two categories are incompatible for conflict detection."""
        incompatible_pairs = [
            (ContextCategory.TECHNICAL, ContextCategory.RELATIONSHIPS),
            (ContextCategory.PROJECTS, ContextCategory.PERSONAL_INFO),
            (ContextCategory.SKILLS, ContextCategory.RELATIONSHIPS)
        ]
        
        return (category1, category2) in incompatible_pairs or (category2, category1) in incompatible_pairs
    
    def _detect_specific_conflict(self, context1: ContextEntry, context2: ContextEntry) -> Optional[ConflictDetection]:
        """Detect specific conflicts between two contexts."""
        content1 = context1.content.lower()
        content2 = context2.content.lower()
        
        # Check for exact contradictions
        contradiction_conflict = self._detect_contradiction_conflict(context1, context2)
        if contradiction_conflict:
            return contradiction_conflict
        
        # Check for update conflicts (same topic, different information)
        update_conflict = self._detect_update_conflict(context1, context2)
        if update_conflict:
            return update_conflict
        
        # Check for duplicate conflicts (very similar content)
        duplicate_conflict = self._detect_duplicate_conflict(context1, context2)
        if duplicate_conflict:
            return duplicate_conflict
        
        return None
    
    def _detect_contradiction_conflict(self, context1: ContextEntry, context2: ContextEntry) -> Optional[ConflictDetection]:
        """Detect contradiction conflicts."""
        content1 = context1.content.lower()
        content2 = context2.content.lower()
        
        # Check for positive/negative contradictions
        for positive, negative in self.contradiction_keywords["positive_negative"]:
            if positive in content1 and negative in content2:
                return ConflictDetection(
                    context1=context1,
                    context2=context2,
                    conflict_type="contradiction",
                    confidence=0.9,
                    reasoning=f"Contradiction detected: '{positive}' vs '{negative}'",
                    suggested_action="Choose the most recent or highest confidence entry"
                )
            elif positive in content2 and negative in content1:
                return ConflictDetection(
                    context1=context1,
                    context2=context2,
                    conflict_type="contradiction",
                    confidence=0.9,
                    reasoning=f"Contradiction detected: '{positive}' vs '{negative}'",
                    suggested_action="Choose the most recent or highest confidence entry"
                )
        
        # Check for temporal contradictions
        for past, present in self.contradiction_keywords["temporal"]:
            if past in content1 and present in content2:
                return ConflictDetection(
                    context1=context1,
                    context2=context2,
                    conflict_type="update",
                    confidence=0.8,
                    reasoning=f"Temporal conflict: past '{past}' vs present '{present}'",
                    suggested_action="Merge as historical progression"
                )
        
        return None
    
    def _detect_update_conflict(self, context1: ContextEntry, context2: ContextEntry) -> Optional[ConflictDetection]:
        """Detect update conflicts (same topic, different information)."""
        content1 = context1.content.lower()
        content2 = context2.content.lower()
        
        # Check for name conflicts
        name_match1 = re.search(r"my name is (\w+)", content1)
        name_match2 = re.search(r"my name is (\w+)", content2)
        if name_match1 and name_match2 and name_match1.group(1) != name_match2.group(1):
            return ConflictDetection(
                context1=context1,
                context2=context2,
                conflict_type="update",
                confidence=0.95,
                reasoning=f"Name conflict: '{name_match1.group(1)}' vs '{name_match2.group(1)}'",
                suggested_action="Choose the most recent entry"
            )
        
        # Check for location conflicts
        location_match1 = re.search(r"i live in ([^,]+)", content1)
        location_match2 = re.search(r"i live in ([^,]+)", content2)
        if location_match1 and location_match2 and location_match1.group(1) != location_match2.group(1):
            return ConflictDetection(
                context1=context1,
                context2=context2,
                conflict_type="update",
                confidence=0.9,
                reasoning=f"Location conflict: '{location_match1.group(1)}' vs '{location_match2.group(1)}'",
                suggested_action="Choose the most recent entry"
            )
        
        # Check for work conflicts
        work_match1 = re.search(r"i work at ([^,]+)", content1)
        work_match2 = re.search(r"i work at ([^,]+)", content2)
        if work_match1 and work_match2 and work_match1.group(1) != work_match2.group(1):
            return ConflictDetection(
                context1=context1,
                context2=context2,
                conflict_type="update",
                confidence=0.9,
                reasoning=f"Work conflict: '{work_match1.group(1)}' vs '{work_match2.group(1)}'",
                suggested_action="Choose the most recent entry"
            )
        
        return None
    
    def _detect_duplicate_conflict(self, context1: ContextEntry, context2: ContextEntry) -> Optional[ConflictDetection]:
        """Detect duplicate conflicts (very similar content)."""
        similarity = SequenceMatcher(None, context1.content, context2.content).ratio()
        
        if similarity > 0.8:
            return ConflictDetection(
                context1=context1,
                context2=context2,
                conflict_type="duplicate",
                confidence=similarity,
                reasoning=f"High similarity detected: {similarity:.2f}",
                suggested_action="Merge or remove duplicate"
            )
        
        return None
    
    def resolve_conflict(self, conflict: ConflictDetection) -> MergeResult:
        """
        Resolve a specific conflict.
        
        Args:
            conflict: The conflict to resolve
            
        Returns:
            MergeResult with the resolution
        """
        actions_taken = []
        confidence = 0.0
        
        if conflict.conflict_type == "contradiction":
            # Choose the most recent or highest confidence entry
            if conflict.context1.created_at > conflict.context2.created_at:
                chosen_context = conflict.context1
                actions_taken.append(f"Chose context1 (more recent: {conflict.context1.created_at})")
            elif conflict.context1.confidence_score > conflict.context2.confidence_score:
                chosen_context = conflict.context1
                actions_taken.append(f"Chose context1 (higher confidence: {conflict.context1.confidence_score})")
            else:
                chosen_context = conflict.context2
                actions_taken.append(f"Chose context2 (better score)")
            
            # Mark the other as disputed
            other_context = conflict.context2 if chosen_context == conflict.context1 else conflict.context1
            other_context.validation_status = ValidationStatus.DISPUTED
            other_context.update_metadata("conflict_resolution", {
                "conflict_type": "contradiction",
                "resolved_at": datetime.utcnow().isoformat(),
                "chosen_context_id": chosen_context.id
            })
            
            return MergeResult(
                merged_context=chosen_context,
                conflicts_resolved=1,
                actions_taken=actions_taken,
                confidence=0.8
            )
        
        elif conflict.conflict_type == "update":
            # Merge as historical progression
            merged_content = self._merge_as_progression(conflict.context1, conflict.context2)
            
            # Create new merged context
            merged_context = ContextEntry(
                content=merged_content,
                context_type=conflict.context1.context_type,
                context_category=conflict.context1.context_category,
                source=f"merged_from_{conflict.context1.id}_{conflict.context2.id}",
                context_source=conflict.context1.context_source,
                confidence_score=max(conflict.context1.confidence_score, conflict.context2.confidence_score) * 0.9,
                tags=list(set((conflict.context1.tags or []) + (conflict.context2.tags or []))),
                extraction_metadata={
                    "merged_from": [conflict.context1.id, conflict.context2.id],
                    "merge_type": "progression",
                    "merged_at": datetime.utcnow().isoformat()
                }
            )
            
            # Mark originals as outdated
            conflict.context1.validation_status = ValidationStatus.OUTDATED
            conflict.context2.validation_status = ValidationStatus.OUTDATED
            
            actions_taken.append("Merged contexts as historical progression")
            actions_taken.append("Marked original contexts as outdated")
            
            return MergeResult(
                merged_context=merged_context,
                conflicts_resolved=1,
                actions_taken=actions_taken,
                confidence=0.9
            )
        
        elif conflict.conflict_type == "duplicate":
            # Choose the better duplicate and mark the other as duplicate
            if conflict.context1.confidence_score > conflict.context2.confidence_score:
                chosen_context = conflict.context1
                duplicate_context = conflict.context2
            else:
                chosen_context = conflict.context2
                duplicate_context = conflict.context1
            
            # Merge tags
            all_tags = list(set((chosen_context.tags or []) + (duplicate_context.tags or [])))
            chosen_context.tags = all_tags
            chosen_context.access_count = (chosen_context.access_count or 0) + (duplicate_context.access_count or 0)
            
            # Mark duplicate as outdated
            duplicate_context.validation_status = ValidationStatus.OUTDATED
            duplicate_context.update_metadata("duplicate_of", chosen_context.id)
            
            actions_taken.append(f"Merged duplicate, kept context with higher confidence")
            actions_taken.append("Marked duplicate as outdated")
            
            return MergeResult(
                merged_context=chosen_context,
                conflicts_resolved=1,
                actions_taken=actions_taken,
                confidence=0.95
            )
        
        return MergeResult(
            merged_context=None,
            conflicts_resolved=0,
            actions_taken=["No resolution applied"],
            confidence=0.0
        )
    
    def _merge_as_progression(self, context1: ContextEntry, context2: ContextEntry) -> str:
        """Merge two contexts as a historical progression."""
        # Determine which is older
        if context1.created_at < context2.created_at:
            old_context, new_context = context1, context2
        else:
            old_context, new_context = context2, context1
        
        # Create progression text
        merged_content = f"Previously: {old_context.content}. Currently: {new_context.content}."
        
        return merged_content
    
    def batch_resolve_conflicts(self, contexts: List[ContextEntry]) -> List[MergeResult]:
        """Resolve all conflicts in a batch of contexts."""
        conflicts = self.detect_conflicts(contexts)
        results = []
        
        resolved_context_ids = set()
        
        for conflict in conflicts:
            # Skip if either context has already been resolved
            if conflict.context1.id in resolved_context_ids or conflict.context2.id in resolved_context_ids:
                continue
            
            result = self.resolve_conflict(conflict)
            results.append(result)
            
            if result.merged_context:
                resolved_context_ids.add(conflict.context1.id)
                resolved_context_ids.add(conflict.context2.id)
        
        return results
    
    def get_conflict_statistics(self) -> Dict[str, Any]:
        """Get statistics about conflicts in the database."""
        from ..database import get_db_context
        
        with get_db_context() as db:
            total_contexts = db.query(ContextEntry).count()
            disputed_contexts = db.query(ContextEntry).filter(
                ContextEntry.validation_status == ValidationStatus.DISPUTED
            ).count()
            outdated_contexts = db.query(ContextEntry).filter(
                ContextEntry.validation_status == ValidationStatus.OUTDATED
            ).count()
            
            # Get contexts with low confidence
            low_confidence = db.query(ContextEntry).filter(
                ContextEntry.confidence_score < 0.5
            ).count()
        
        return {
            "total_contexts": total_contexts,
            "disputed_contexts": disputed_contexts,
            "outdated_contexts": outdated_contexts,
            "low_confidence_contexts": low_confidence,
            "conflict_rate": disputed_contexts / total_contexts if total_contexts > 0 else 0
        }
    
    def cleanup_resolved_conflicts(self) -> int:
        """Clean up resolved conflicts by removing outdated contexts."""
        from ..database import get_db_context
        
        with get_db_context() as db:
            # Get outdated contexts that are older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            outdated_contexts = db.query(ContextEntry).filter(
                ContextEntry.validation_status == ValidationStatus.OUTDATED,
                ContextEntry.updated_at < cutoff_date
            ).all()
            
            # Delete outdated contexts
            count = len(outdated_contexts)
            for context in outdated_contexts:
                db.delete(context)
            
            db.commit()
            
        return count


# Global instance
context_conflict_resolver = ContextConflictResolver()
