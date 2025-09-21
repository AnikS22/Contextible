"""SQLAlchemy models for context management."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, Enum, String, Text, func, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ContextType(str, Enum):
    """Enumeration of supported context types."""
    TEXT = "text"
    FILE = "file"
    EVENT = "event"
    PREFERENCE = "preference"
    NOTE = "note"
    PERSONAL_INFO = "personal_info"
    GOAL = "goal"
    RELATIONSHIP = "relationship"
    SKILL = "skill"
    PROJECT = "project"


class ContextSource(str, Enum):
    """Enumeration of context sources."""
    MANUAL = "manual"
    CONVERSATION = "conversation"
    IMPORTED = "imported"
    EXTRACTED = "extracted"
    API = "api"


class ContextCategory(str, Enum):
    """Enumeration of context categories."""
    PERSONAL_INFO = "personal_info"
    PREFERENCES = "preferences"
    GOALS = "goals"
    RELATIONSHIPS = "relationships"
    SKILLS = "skills"
    WORK = "work"
    PROJECTS = "projects"
    TECHNICAL = "technical"
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    OTHER = "other"


class ValidationStatus(str, Enum):
    """Enumeration of validation statuses."""
    CONFIRMED = "confirmed"
    PENDING = "pending"
    DISPUTED = "disputed"
    OUTDATED = "outdated"


class ContextEntry(Base):
    """
    Model for storing context entries.
    
    Each context entry represents a piece of information that can be
    retrieved and injected into AI model conversations.
    """
    
    __tablename__ = "context_entries"
    
    # Primary identifier
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier for the context entry"
    )
    
    # Core content
    content: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        comment="The actual context content/text"
    )
    
    context_type: Mapped[ContextType] = mapped_column(
        Enum("text", "file", "event", "preference", "note", "personal_info", "goal", "relationship", "skill", "project", name="context_type_enum"), 
        nullable=False, 
        default=ContextType.TEXT,
        comment="Type of context (text, file, event, preference, note, personal_info, goal, relationship, skill, project)"
    )
    
    source: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        comment="Source of the context (e.g., 'user_input', 'file:path.txt', 'api')"
    )
    
    context_source: Mapped[ContextSource] = mapped_column(
        Enum("manual", "conversation", "imported", "extracted", "api", name="context_source_enum"),
        nullable=False,
        default=ContextSource.MANUAL,
        comment="How this context was obtained (manual, conversation, imported, extracted, api)"
    )
    
    confidence_score: Mapped[float] = mapped_column(
        default=1.0,
        comment="Confidence score for this context (0.0-1.0, higher = more reliable)"
    )
    
    context_category: Mapped[ContextCategory] = mapped_column(
        Enum("personal_info", "preferences", "goals", "relationships", "skills", "work", "projects", "technical", "personal", "professional", "other", name="context_category_enum"),
        nullable=False,
        default=ContextCategory.OTHER,
        comment="Category of this context for intelligent organization"
    )
    
    parent_context_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="ID of parent context for hierarchical organization"
    )
    
    validation_status: Mapped[ValidationStatus] = mapped_column(
        Enum("confirmed", "pending", "disputed", "outdated", name="validation_status_enum"),
        nullable=False,
        default=ValidationStatus.PENDING,
        comment="Validation status of this context"
    )
    
    extraction_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=lambda: {},
        comment="Metadata about how this context was extracted/obtained"
    )
    
    # Metadata and organization
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=list,
        comment="List of tags for categorization and filtering"
    )
    
    entry_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=lambda: {},
        comment="Additional metadata as JSON"
    )
    
    # User and session tracking
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        nullable=True,
        comment="User ID for multi-user support (future)"
    )
    
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        nullable=True,
        comment="Session ID where this context was created"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the context entry was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        comment="When the context entry was last updated"
    )
    
    # Performance and relevance
    access_count: Mapped[int] = mapped_column(
        default=0,
        comment="Number of times this context has been accessed"
    )
    
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        comment="When this context was last accessed"
    )
    
    relevance_score: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="Computed relevance score for ranking (future use)"
    )
    
    # Semantic search embedding
    embedding: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary,
        nullable=True,
        comment="Semantic embedding vector for similarity search (pickled numpy array)"
    )
    
    def __repr__(self) -> str:
        """String representation of the context entry."""
        return (
            f"<ContextEntry(id='{self.id}', "
            f"type='{self.context_type}', "
            f"content='{self.content[:50]}...', "
            f"tags={self.tags})>"
        )
    
    def to_dict(self, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Convert the context entry to a dictionary.
        
        Args:
            include_metadata: Whether to include metadata fields
            
        Returns:
            Dictionary representation of the context entry
        """
        result = {
            "id": self.id,
            "content": self.content,
            "context_type": self.context_type,
            "source": self.source,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_metadata:
            result.update({
                "metadata": self.entry_metadata or {},
                "user_id": self.user_id,
                "session_id": self.session_id,
                "access_count": self.access_count,
                "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
                "relevance_score": self.relevance_score,
            })
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextEntry":
        """
        Create a ContextEntry from a dictionary.
        
        Args:
            data: Dictionary containing context entry data
            
        Returns:
            New ContextEntry instance
        """
        # Handle enum conversion
        if "context_type" in data and isinstance(data["context_type"], str):
            data["context_type"] = ContextType(data["context_type"])
        
        # Handle datetime conversion
        for field in ["created_at", "updated_at", "last_accessed_at"]:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
        
        return cls(**data)
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to this context entry."""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> bool:
        """
        Remove a tag from this context entry.
        
        Returns:
            True if tag was removed, False if tag wasn't present
        """
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
            return True
        return False
    
    def has_tag(self, tag: str) -> bool:
        """Check if this context entry has a specific tag."""
        return self.tags is not None and tag in self.tags
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update a metadata field."""
        if self.entry_metadata is None:
            self.entry_metadata = {}
        self.entry_metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata field value."""
        if self.entry_metadata is None:
            return default
        return self.entry_metadata.get(key, default)
    
    def record_access(self) -> None:
        """Record that this context entry was accessed."""
        self.access_count = (self.access_count or 0) + 1
        self.last_accessed_at = datetime.utcnow()
    
    def is_recent(self, days: int = 30) -> bool:
        """Check if this context entry was created recently."""
        if not self.created_at:
            return False
        delta = datetime.utcnow() - self.created_at.replace(tzinfo=None)
        return delta.days <= days
    
    def matches_filter(self, 
                      tags: Optional[List[str]] = None,
                      context_types: Optional[List[ContextType]] = None,
                      source_pattern: Optional[str] = None) -> bool:
        """
        Check if this context entry matches the given filters.
        
        Args:
            tags: List of tags to match (any match)
            context_types: List of context types to match
            source_pattern: Source pattern to match (substring)
            
        Returns:
            True if all specified filters match
        """
        # Check tags
        if tags:
            if not self.tags or not any(tag in self.tags for tag in tags):
                return False
        
        # Check context types
        if context_types:
            if self.context_type not in context_types:
                return False
        
        # Check source pattern
        if source_pattern:
            if not self.source or source_pattern.lower() not in self.source.lower():
                return False
        
        return True
