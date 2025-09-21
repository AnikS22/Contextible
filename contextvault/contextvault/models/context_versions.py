"""SQLAlchemy models for context versioning."""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, String, Text, func, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class ChangeType(str, Enum):
    """Enumeration of change types."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RESTORE = "restore"
    MERGE = "merge"


class ContextVersion(Base):
    """
    Model for storing context entry versions.
    
    Tracks all changes to context entries for audit trails,
    rollback capabilities, and version history.
    """
    
    __tablename__ = "context_versions"
    
    # Primary identifier
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier for the version"
    )
    
    # Version information
    context_id: Mapped[str] = mapped_column(
        String(36), 
        nullable=False,
        comment="ID of the context entry this version belongs to"
    )
    
    version_number: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        comment="Version number (1, 2, 3, etc.)"
    )
    
    # Change information
    change_type: Mapped[ChangeType] = mapped_column(
        nullable=False,
        comment="Type of change made"
    )
    
    changed_by: Mapped[str] = mapped_column(
        String(36), 
        nullable=False,
        comment="User ID who made the change"
    )
    
    change_reason: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Reason for the change"
    )
    
    # Content snapshots
    content: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        comment="Content at this version"
    )
    
    context_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Context type at this version"
    )
    
    context_category: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Context category at this version"
    )
    
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=list,
        comment="Tags at this version"
    )
    
    version_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=dict,
        comment="Metadata at this version"
    )
    
    # Change tracking
    changes_made: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=dict,
        comment="Detailed changes made in this version"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When this version was created"
    )
    
    def __repr__(self) -> str:
        """String representation of the version."""
        return (
            f"<ContextVersion(id='{self.id}', "
            f"context_id='{self.context_id}', "
            f"version={self.version_number}, "
            f"change_type='{self.change_type}')>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the version to a dictionary."""
        return {
            "id": self.id,
            "context_id": self.context_id,
            "version_number": self.version_number,
            "change_type": self.change_type.value if hasattr(self.change_type, 'value') else str(self.change_type),
            "changed_by": self.changed_by,
            "change_reason": self.change_reason,
            "content": self.content,
            "context_type": self.context_type,
            "context_category": self.context_category,
            "tags": self.tags or [],
            "version_metadata": self.version_metadata or {},
            "changes_made": self.changes_made or {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_version(cls,
                      context_id: str,
                      version_number: int,
                      change_type: ChangeType,
                      changed_by: str,
                      content: str,
                      context_type: str,
                      context_category: str,
                      tags: Optional[List[str]] = None,
                      version_metadata: Optional[Dict[str, Any]] = None,
                      change_reason: Optional[str] = None,
                      changes_made: Optional[Dict[str, Any]] = None) -> "ContextVersion":
        """
        Create a new context version.
        
        Args:
            context_id: ID of the context entry
            version_number: Version number
            change_type: Type of change
            changed_by: User who made the change
            content: Content at this version
            context_type: Context type
            context_category: Context category
            tags: Tags
            metadata: Metadata
            change_reason: Reason for change
            changes_made: Detailed changes
            
        Returns:
            New ContextVersion instance
        """
        return cls(
            context_id=context_id,
            version_number=version_number,
            change_type=change_type,
            changed_by=changed_by,
            content=content,
            context_type=context_type,
            context_category=context_category,
            tags=tags or [],
            version_metadata=version_metadata or {},
            change_reason=change_reason,
            changes_made=changes_made or {}
        )
