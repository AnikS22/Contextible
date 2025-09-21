"""Pydantic schemas for context-related API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

class ContextEntryBase(BaseModel):
    """Base schema for context entries."""
    
    content: str = Field(..., min_length=1, max_length=50000, description="Context content")
    context_type: str = Field(default="text", description="Type of context")
    source: Optional[str] = Field(None, max_length=255, description="Source of the context")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata", alias="entry_metadata")
    user_id: Optional[str] = Field(None, description="User ID (for multi-user support)")
    session_id: Optional[str] = Field(None, description="Session ID")


class ContextEntryCreate(ContextEntryBase):
    """Schema for creating context entries."""
    pass


class ContextEntryUpdate(BaseModel):
    """Schema for updating context entries."""
    
    content: Optional[str] = Field(None, min_length=1, max_length=50000)
    context_type: Optional[str] = Field(None)
    source: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)


class ContextEntryResponse(ContextEntryBase):
    """Schema for context entry responses."""
    
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    access_count: int = Field(default=0, description="Number of times accessed")
    last_accessed_at: Optional[datetime] = Field(None, description="Last access timestamp")
    relevance_score: Optional[float] = Field(None, description="Relevance score")
    
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class ContextEntryBrief(BaseModel):
    """Brief schema for context entries (for lists)."""
    
    id: str
    content: str = Field(..., max_length=200, description="Truncated content")
    context_type: str
    tags: List[str]
    created_at: datetime
    access_count: int
    
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class ContextQuery(BaseModel):
    """Schema for context query parameters."""
    
    model: Optional[str] = Field(None, description="AI model requesting context")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    context_types: Optional[List[str]] = Field(None, description="Filter by context types")
    source: Optional[str] = Field(None, description="Filter by source pattern")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum number of entries")
    offset: int = Field(default=0, ge=0, description="Number of entries to skip")
    since: Optional[datetime] = Field(None, description="Only entries after this timestamp")
    include_metadata: bool = Field(default=False, description="Include full metadata")
    search: Optional[str] = Field(None, max_length=500, description="Search query")


class ContextQueryResponse(BaseModel):
    """Schema for context query responses."""
    
    entries: List[ContextEntryResponse] = Field(..., description="Context entries")
    total: int = Field(..., description="Total number of matching entries")
    offset: int = Field(..., description="Offset used in query")
    limit: int = Field(..., description="Limit used in query")
    has_more: bool = Field(..., description="Whether there are more results")
    query_time_ms: Optional[int] = Field(None, description="Query execution time")


class ContextStats(BaseModel):
    """Schema for context statistics."""
    
    total_entries: int = Field(..., description="Total number of context entries")
    entries_by_type: Dict[str, int] = Field(..., description="Count by context type")
    entries_by_tag: Dict[str, int] = Field(..., description="Count by tag")
    most_accessed: List[ContextEntryBrief] = Field(..., description="Most accessed entries")
    recent_entries: List[ContextEntryBrief] = Field(..., description="Recent entries")
    oldest_entry: Optional[datetime] = Field(None, description="Oldest entry timestamp")
    newest_entry: Optional[datetime] = Field(None, description="Newest entry timestamp")
    total_characters: int = Field(default=0, description="Total character count")
    average_access_count: float = Field(default=0.0, description="Average access count")
    
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class BulkContextOperation(BaseModel):
    """Schema for bulk context operations."""
    
    operation: str = Field(..., description="Operation type (delete, update_tags, etc.)")
    entry_ids: List[str] = Field(..., min_items=1, max_items=1000, description="Entry IDs")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Operation parameters")


class BulkOperationResult(BaseModel):
    """Schema for bulk operation results."""
    
    operation: str = Field(..., description="Operation that was performed")
    total_requested: int = Field(..., description="Total entries requested for operation")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    processing_time_ms: Optional[int] = Field(None, description="Processing time")
