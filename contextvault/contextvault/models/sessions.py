"""SQLAlchemy models for session tracking."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, String, Text, func, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Session(Base):
    """
    Model for tracking AI interaction sessions.
    
    Records when AI models access context, what context was used,
    and other session-related metadata for auditing and analytics.
    """
    
    __tablename__ = "sessions"
    
    # Primary identifier
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier for the session"
    )
    
    # Model and user identification
    model_id: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        index=True,
        comment="Identifier for the AI model that was used"
    )
    
    model_name: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        comment="Human-readable name for the model"
    )
    
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        nullable=True,
        comment="User ID who initiated the session"
    )
    
    # Session metadata
    session_type: Mapped[str] = mapped_column(
        String(50), 
        default="chat",
        comment="Type of session (chat, completion, embedding, etc.)"
    )
    
    source: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        comment="Source of the session (ollama, api, cli, etc.)"
    )
    
    # Context usage tracking
    context_used: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=list,
        comment="List of context entries that were injected"
    )
    
    context_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="Number of context entries used in this session"
    )
    
    total_context_length: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="Total character length of all injected context"
    )
    
    # Request/response data
    original_prompt: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Original user prompt before context injection"
    )
    
    final_prompt: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Final prompt sent to model after context injection"
    )
    
    response_summary: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Summary or excerpt of the model's response"
    )
    
    # Performance metrics
    processing_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True,
        comment="Time taken to process context injection (milliseconds)"
    )
    
    model_response_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True,
        comment="Time taken by the model to respond (milliseconds)"
    )
    
    # Session status and flags
    success: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="Whether the session completed successfully"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Error message if the session failed"
    )
    
    # Additional metadata
    session_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=lambda: {},
        comment="Additional session metadata as JSON"
    )
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the session started"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        comment="When the session completed"
    )
    
    def __repr__(self) -> str:
        """String representation of the session."""
        return (
            f"<Session(id='{self.id}', "
            f"model_id='{self.model_id}', "
            f"context_count={self.context_count}, "
            f"success={self.success})>"
        )
    
    def to_dict(self, include_content: bool = False) -> Dict[str, Any]:
        """
        Convert the session to a dictionary.
        
        Args:
            include_content: Whether to include full prompt/response content
            
        Returns:
            Dictionary representation of the session
        """
        result = {
            "id": self.id,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "user_id": self.user_id,
            "session_type": self.session_type,
            "source": self.source,
            "context_count": self.context_count,
            "total_context_length": self.total_context_length,
            "processing_time_ms": self.processing_time_ms,
            "model_response_time_ms": self.model_response_time_ms,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.session_metadata or {},
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        
        if include_content:
            result.update({
                "context_used": self.context_used or [],
                "original_prompt": self.original_prompt,
                "final_prompt": self.final_prompt,
                "response_summary": self.response_summary,
            })
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """
        Create a Session from a dictionary.
        
        Args:
            data: Dictionary containing session data
            
        Returns:
            New Session instance
        """
        # Handle datetime conversion
        for field in ["started_at", "completed_at"]:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field].replace("Z", "+00:00"))
        
        return cls(**data)
    
    def add_context_entry(self, context_entry_data: Dict[str, Any]) -> None:
        """Add a context entry to this session's usage tracking."""
        if self.context_used is None:
            self.context_used = []
        
        self.context_used.append(context_entry_data)
        self.context_count = len(self.context_used)
        
        # Update total context length
        content_length = len(context_entry_data.get("content", ""))
        self.total_context_length = (self.total_context_length or 0) + content_length
    
    def complete_session(self, 
                        success: bool = True, 
                        error_message: Optional[str] = None,
                        response_summary: Optional[str] = None) -> None:
        """Mark the session as completed."""
        self.completed_at = datetime.utcnow()
        self.success = success
        if error_message:
            self.error_message = error_message
        if response_summary:
            self.response_summary = response_summary
    
    def get_duration_ms(self) -> Optional[int]:
        """Get the total session duration in milliseconds."""
        if not self.started_at or not self.completed_at:
            return None
        
        delta = self.completed_at - self.started_at
        return int(delta.total_seconds() * 1000)
    
    def get_total_time_ms(self) -> Optional[int]:
        """Get the total processing + model response time in milliseconds."""
        processing_time = self.processing_time_ms or 0
        response_time = self.model_response_time_ms or 0
        
        if processing_time == 0 and response_time == 0:
            return None
        
        return processing_time + response_time
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata field."""
        if self.session_metadata is None:
            self.session_metadata = {}
        self.session_metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata field value."""
        if self.session_metadata is None:
            return default
        return self.session_metadata.get(key, default)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the context used in this session."""
        if not self.context_used:
            return {
                "count": 0,
                "total_length": 0,
                "types": [],
                "tags": [],
            }
        
        context_types = []
        all_tags = []
        
        for entry in self.context_used:
            entry_type = entry.get("context_type")
            if entry_type and entry_type not in context_types:
                context_types.append(entry_type)
            
            entry_tags = entry.get("tags", [])
            for tag in entry_tags:
                if tag not in all_tags:
                    all_tags.append(tag)
        
        return {
            "count": self.context_count,
            "total_length": self.total_context_length,
            "types": context_types,
            "tags": all_tags,
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this session."""
        return {
            "processing_time_ms": self.processing_time_ms,
            "model_response_time_ms": self.model_response_time_ms,
            "total_time_ms": self.get_total_time_ms(),
            "duration_ms": self.get_duration_ms(),
            "context_count": self.context_count,
            "context_length": self.total_context_length,
            "context_per_ms": (
                self.total_context_length / self.processing_time_ms 
                if self.processing_time_ms and self.processing_time_ms > 0 
                else None
            ),
        }
    
    @classmethod
    def create_session(cls, 
                      model_id: str, 
                      session_type: str = "chat",
                      source: Optional[str] = None,
                      user_id: Optional[str] = None) -> "Session":
        """
        Create a new session with basic information.
        
        Args:
            model_id: The AI model identifier
            session_type: Type of session (chat, completion, etc.)
            source: Source of the session
            user_id: User who initiated the session
            
        Returns:
            New Session instance
        """
        return cls(
            model_id=model_id,
            session_type=session_type,
            source=source,
            user_id=user_id,
        )
