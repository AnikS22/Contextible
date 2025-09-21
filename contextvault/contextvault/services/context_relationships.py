"""Service for managing context relationships."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..database import get_db_context
from ..models.context import ContextEntry
from ..models.context_relationships import ContextRelationship, RelationshipType
from ..services.semantic_search import get_semantic_search_service

logger = logging.getLogger(__name__)


class ContextRelationshipService:
    """Service for managing relationships between context entries."""
    
    def __init__(self):
        """Initialize the context relationship service."""
        self.semantic_search = get_semantic_search_service()
        self.logger = logging.getLogger(__name__)
    
    async def find_related_contexts(self, 
                                  context_id: str,
                                  relationship_types: Optional[List[RelationshipType]] = None,
                                  min_strength: float = 0.3,
                                  limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find contexts related to a given context.
        
        Args:
            context_id: ID of the context to find relationships for
            relationship_types: Types of relationships to include
            min_strength: Minimum relationship strength
            limit: Maximum number of results
            
        Returns:
            List of related contexts with relationship information
        """
        with get_db_context() as db:
            query = db.query(ContextRelationship).filter(
                or_(
                    ContextRelationship.source_context_id == context_id,
                    ContextRelationship.target_context_id == context_id
                )
            )
            
            if relationship_types:
                query = query.filter(ContextRelationship.relationship_type.in_(relationship_types))
            
            if min_strength > 0:
                query = query.filter(ContextRelationship.strength >= min_strength)
            
            query = query.order_by(desc(ContextRelationship.strength)).limit(limit)
            relationships = query.all()
            
            # Get related context details
            related_contexts = []
            for rel in relationships:
                # Determine which context is the related one
                related_id = (rel.target_context_id if rel.source_context_id == context_id 
                             else rel.source_context_id)
                
                # Get the related context
                related_context = db.query(ContextEntry).filter(
                    ContextEntry.id == related_id
                ).first()
                
                if related_context:
                    related_contexts.append({
                        "context": related_context,
                        "relationship": rel,
                        "relationship_type": rel.relationship_type,
                        "strength": rel.strength,
                        "confidence": rel.confidence
                    })
            
            return related_contexts
    
    async def create_relationship(self,
                                source_context_id: str,
                                target_context_id: str,
                                relationship_type: RelationshipType,
                                strength: float = 0.5,
                                confidence: float = 0.5,
                                auto_generated: bool = False,
                                reasoning: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> ContextRelationship:
        """
        Create a new relationship between contexts.
        
        Args:
            source_context_id: Source context ID
            target_context_id: Target context ID
            relationship_type: Type of relationship
            strength: Relationship strength
            confidence: Confidence in relationship
            auto_generated: Whether auto-generated
            reasoning: Human-readable reasoning
            metadata: Additional metadata
            
        Returns:
            Created relationship
        """
        with get_db_context() as db:
            # Check if relationship already exists
            existing = db.query(ContextRelationship).filter(
                and_(
                    ContextRelationship.source_context_id == source_context_id,
                    ContextRelationship.target_context_id == target_context_id,
                    ContextRelationship.relationship_type == relationship_type
                )
            ).first()
            
            if existing:
                # Update existing relationship
                existing.strength = strength
                existing.confidence = confidence
                existing.reasoning = reasoning
                existing.metadata = metadata or {}
                existing.updated_at = datetime.utcnow()
                db.commit()
                return existing
            
            # Create new relationship
            relationship = ContextRelationship.create_relationship(
                source_context_id=source_context_id,
                target_context_id=target_context_id,
                relationship_type=relationship_type,
                strength=strength,
                confidence=confidence,
                auto_generated=auto_generated,
                reasoning=reasoning,
                metadata=metadata
            )
            
            db.add(relationship)
            db.commit()
            db.refresh(relationship)
            
            # Create opposite relationship if symmetric
            if relationship.is_symmetric():
                opposite = relationship.get_opposite_relationship()
                db.add(opposite)
                db.commit()
            
            self.logger.info(f"Created relationship: {source_context_id} -> {target_context_id} ({relationship_type.value})")
            return relationship
    
    async def detect_relationships(self, 
                                 context_id: str,
                                 auto_create: bool = True) -> List[ContextRelationship]:
        """
        Detect relationships for a context using semantic analysis.
        
        Args:
            context_id: ID of the context to analyze
            auto_create: Whether to automatically create detected relationships
            
        Returns:
            List of detected relationships
        """
        with get_db_context() as db:
            # Get the context to analyze
            context = db.query(ContextEntry).filter(ContextEntry.id == context_id).first()
            if not context:
                return []
            
            # Get all other contexts for comparison
            other_contexts = db.query(ContextEntry).filter(
                ContextEntry.id != context_id
            ).all()
            
            detected_relationships = []
            
            for other_context in other_contexts:
                # Calculate semantic similarity
                similarity = await self._calculate_semantic_similarity(
                    context.content, other_context.content
                )
                
                if similarity > 0.7:
                    # High similarity - likely related
                    relationship_type = RelationshipType.SIMILAR
                    strength = similarity
                    confidence = 0.8
                elif similarity > 0.5:
                    # Medium similarity - possibly related
                    relationship_type = RelationshipType.RELATED
                    strength = similarity
                    confidence = 0.6
                else:
                    continue
                
                if auto_create:
                    relationship = await self.create_relationship(
                        source_context_id=context_id,
                        target_context_id=other_context.id,
                        relationship_type=relationship_type,
                        strength=strength,
                        confidence=confidence,
                        auto_generated=True,
                        reasoning=f"Auto-detected based on semantic similarity: {similarity:.2f}"
                    )
                    detected_relationships.append(relationship)
                else:
                    # Just return the detected relationship without creating
                    relationship = ContextRelationship.create_relationship(
                        source_context_id=context_id,
                        target_context_id=other_context.id,
                        relationship_type=relationship_type,
                        strength=strength,
                        confidence=confidence,
                        auto_generated=True,
                        reasoning=f"Auto-detected based on semantic similarity: {similarity:.2f}"
                    )
                    detected_relationships.append(relationship)
            
            return detected_relationships
    
    async def detect_conflicts(self, 
                             context_id: str) -> List[Dict[str, Any]]:
        """
        Detect conflicts for a context.
        
        Args:
            context_id: ID of the context to analyze
            
        Returns:
            List of detected conflicts
        """
        with get_db_context() as db:
            # Get the context to analyze
            context = db.query(ContextEntry).filter(ContextEntry.id == context_id).first()
            if not context:
                return []
            
            # Get all other contexts for comparison
            other_contexts = db.query(ContextEntry).filter(
                ContextEntry.id != context_id
            ).all()
            
            conflicts = []
            
            for other_context in other_contexts:
                # Check for semantic similarity first
                similarity = await self._calculate_semantic_similarity(
                    context.content, other_context.content
                )
                
                if similarity > 0.6:
                    # High similarity - check for contradictions
                    contradiction_score = await self._calculate_contradiction_score(
                        context.content, other_context.content
                    )
                    
                    if contradiction_score > 0.7:
                        conflicts.append({
                            "context_id": context_id,
                            "conflicting_context_id": other_context.id,
                            "conflict_type": "contradiction",
                            "contradiction_score": contradiction_score,
                            "similarity_score": similarity,
                            "reasoning": f"High similarity ({similarity:.2f}) but contradictory content ({contradiction_score:.2f})"
                        })
            
            return conflicts
    
    async def build_context_hierarchy(self, 
                                    root_context_id: str,
                                    max_depth: int = 3) -> Dict[str, Any]:
        """
        Build a hierarchy of related contexts.
        
        Args:
            root_context_id: ID of the root context
            max_depth: Maximum depth of the hierarchy
            
        Returns:
            Hierarchical structure of contexts
        """
        with get_db_context() as db:
            def build_node(context_id: str, depth: int) -> Dict[str, Any]:
                if depth > max_depth:
                    return None
                
                # Get the context
                context = db.query(ContextEntry).filter(ContextEntry.id == context_id).first()
                if not context:
                    return None
                
                # Get hierarchical relationships
                relationships = db.query(ContextRelationship).filter(
                    and_(
                        or_(
                            ContextRelationship.source_context_id == context_id,
                            ContextRelationship.target_context_id == context_id
                        ),
                        ContextRelationship.relationship_type == RelationshipType.HIERARCHICAL
                    )
                ).all()
                
                # Build children
                children = []
                for rel in relationships:
                    child_id = (rel.target_context_id if rel.source_context_id == context_id 
                               else rel.source_context_id)
                    child_node = build_node(child_id, depth + 1)
                    if child_node:
                        child_node["relationship_strength"] = rel.strength
                        children.append(child_node)
                
                return {
                    "id": context_id,
                    "content": context.content[:100] + "..." if len(context.content) > 100 else context.content,
                    "context_type": context.context_type.value if hasattr(context.context_type, 'value') else str(context.context_type),
                    "children": children,
                    "depth": depth
                }
            
            return build_node(root_context_id, 0)
    
    async def get_relationship_statistics(self) -> Dict[str, Any]:
        """Get statistics about context relationships."""
        with get_db_context() as db:
            # Total relationships
            total_relationships = db.query(ContextRelationship).count()
            
            # Relationships by type
            relationships_by_type = {}
            for rel_type in RelationshipType:
                count = db.query(ContextRelationship).filter(
                    ContextRelationship.relationship_type == rel_type
                ).count()
                relationships_by_type[rel_type.value] = count
            
            # Auto-generated vs manual
            auto_generated_count = db.query(ContextRelationship).filter(
                ContextRelationship.auto_generated == True
            ).count()
            manual_count = total_relationships - auto_generated_count
            
            # Average strength by type
            avg_strength_by_type = {}
            for rel_type in RelationshipType:
                result = db.query(func.avg(ContextRelationship.strength)).filter(
                    ContextRelationship.relationship_type == rel_type
                ).scalar()
                avg_strength_by_type[rel_type.value] = result or 0.0
            
            return {
                "total_relationships": total_relationships,
                "relationships_by_type": relationships_by_type,
                "auto_generated_count": auto_generated_count,
                "manual_count": manual_count,
                "avg_strength_by_type": avg_strength_by_type
            }
    
    async def _calculate_semantic_similarity(self, 
                                           content1: str, 
                                           content2: str) -> float:
        """Calculate semantic similarity between two content strings."""
        try:
            # Use semantic search service for similarity calculation
            if hasattr(self.semantic_search, 'calculate_similarity'):
                return await self.semantic_search.calculate_similarity(content1, content2)
            else:
                # Fallback to simple text similarity
                return self._simple_text_similarity(content1, content2)
        except Exception as e:
            self.logger.error(f"Failed to calculate semantic similarity: {e}")
            return 0.0
    
    async def _calculate_contradiction_score(self, 
                                           content1: str, 
                                           content2: str) -> float:
        """Calculate contradiction score between two content strings."""
        # Simple contradiction detection based on keywords
        contradiction_keywords = [
            ("yes", "no"), ("true", "false"), ("correct", "incorrect"),
            ("agree", "disagree"), ("support", "oppose"), ("like", "dislike")
        ]
        
        content1_lower = content1.lower()
        content2_lower = content2.lower()
        
        contradiction_score = 0.0
        
        for positive, negative in contradiction_keywords:
            if positive in content1_lower and negative in content2_lower:
                contradiction_score += 0.3
            elif negative in content1_lower and positive in content2_lower:
                contradiction_score += 0.3
        
        return min(1.0, contradiction_score)
    
    def _simple_text_similarity(self, content1: str, content2: str) -> float:
        """Simple text similarity calculation."""
        # Convert to lowercase and split into words
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0


# Global context relationship service instance
context_relationship_service = ContextRelationshipService()
