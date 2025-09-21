"""SQLAlchemy models for context relationships."""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, String, Text, func, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class RelationshipType(str, Enum):
    """Enumeration of context relationship types."""
    RELATED = "related"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    HIERARCHICAL = "hierarchical"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    SIMILAR = "similar"


class ContextRelationship(Base):
    """
    Model for storing relationships between context entries.
    
    Enables building context hierarchies, detecting conflicts,
    and understanding context connections.
    """
    
    __tablename__ = "context_relationships"
    
    # Primary identifier
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier for the relationship"
    )
    
    # Relationship endpoints
    source_context_id: Mapped[str] = mapped_column(
        String(36), 
        nullable=False,
        comment="ID of the source context entry"
    )
    
    target_context_id: Mapped[str] = mapped_column(
        String(36), 
        nullable=False,
        comment="ID of the target context entry"
    )
    
    # Relationship properties
    relationship_type: Mapped[RelationshipType] = mapped_column(
        nullable=False,
        comment="Type of relationship between contexts"
    )
    
    strength: Mapped[float] = mapped_column(
        Float, 
        default=0.5,
        comment="Strength of the relationship (0.0-1.0)"
    )
    
    confidence: Mapped[float] = mapped_column(
        Float, 
        default=0.5,
        comment="Confidence in the relationship (0.0-1.0)"
    )
    
    # Relationship metadata
    auto_generated: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="Whether this relationship was auto-generated"
    )
    
    reasoning: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Human-readable reasoning for the relationship"
    )
    
    relationship_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=dict,
        comment="Additional relationship metadata"
    )
    
    # Validation and quality
    is_validated: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="Whether this relationship has been validated"
    )
    
    validation_notes: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Notes from relationship validation"
    )
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(
        default=0,
        comment="Number of times this relationship has been used"
    )
    
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        comment="When this relationship was last used"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the relationship was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        comment="When the relationship was last updated"
    )
    
    def __repr__(self) -> str:
        """String representation of the relationship."""
        return (
            f"<ContextRelationship(id='{self.id}', "
            f"source='{self.source_context_id}', "
            f"target='{self.target_context_id}', "
            f"type='{self.relationship_type}')>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the relationship to a dictionary."""
        return {
            "id": self.id,
            "source_context_id": self.source_context_id,
            "target_context_id": self.target_context_id,
            "relationship_type": self.relationship_type.value if hasattr(self.relationship_type, 'value') else str(self.relationship_type),
            "strength": self.strength,
            "confidence": self.confidence,
            "auto_generated": self.auto_generated,
            "reasoning": self.reasoning,
            "relationship_metadata": self.relationship_metadata or {},
            "is_validated": self.is_validated,
            "validation_notes": self.validation_notes,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }
    
    def is_symmetric(self) -> bool:
        """Check if this relationship is symmetric (bidirectional)."""
        symmetric_types = {
            RelationshipType.RELATED,
            RelationshipType.SIMILAR,
            RelationshipType.SUPPORTS
        }
        return self.relationship_type in symmetric_types
    
    def get_opposite_relationship(self) -> "ContextRelationship":
        """Get the opposite relationship (if symmetric)."""
        if not self.is_symmetric():
            raise ValueError("Cannot create opposite for non-symmetric relationship")
        
        return ContextRelationship(
            source_context_id=self.target_context_id,
            target_context_id=self.source_context_id,
            relationship_type=self.relationship_type,
            strength=self.strength,
            confidence=self.confidence,
            auto_generated=self.auto_generated,
            reasoning=self.reasoning,
            relationship_metadata=self.relationship_metadata
        )
    
    def record_usage(self) -> None:
        """Record that this relationship was used."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
    
    def validate(self, validation_notes: Optional[str] = None) -> None:
        """Mark this relationship as validated."""
        self.is_validated = True
        if validation_notes:
            self.validation_notes = validation_notes
        self.updated_at = datetime.utcnow()
    
    def invalidate(self, reason: str) -> None:
        """Mark this relationship as invalid."""
        self.is_validated = False
        self.validation_notes = reason
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def create_relationship(cls,
                          source_context_id: str,
                          target_context_id: str,
                          relationship_type: RelationshipType,
                          strength: float = 0.5,
                          confidence: float = 0.5,
                          auto_generated: bool = False,
                          reasoning: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> "ContextRelationship":
        """
        Create a new context relationship.
        
        Args:
            source_context_id: Source context ID
            target_context_id: Target context ID
            relationship_type: Type of relationship
            strength: Relationship strength (0.0-1.0)
            confidence: Confidence in relationship (0.0-1.0)
            auto_generated: Whether auto-generated
            reasoning: Human-readable reasoning
            metadata: Additional metadata
            
        Returns:
            New ContextRelationship instance
        """
        return cls(
            source_context_id=source_context_id,
            target_context_id=target_context_id,
            relationship_type=relationship_type,
            strength=strength,
            confidence=confidence,
            auto_generated=auto_generated,
            reasoning=reasoning,
            relationship_metadata=metadata or {}
        )
