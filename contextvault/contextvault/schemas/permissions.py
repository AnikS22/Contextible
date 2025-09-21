"""Pydantic schemas for permission-related API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class PermissionBase(BaseModel):
    """Base schema for permissions."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str = Field(..., min_length=1, max_length=255, description="AI model identifier")
    model_name: Optional[str] = Field(None, max_length=255, description="Human-readable model name")
    scope: Optional[str] = Field(None, description="Comma-separated list of allowed scopes")
    rules: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Detailed permission rules")
    is_active: bool = Field(default=True, description="Whether this permission is active")
    allow_all: bool = Field(default=False, description="Whether to allow unrestricted access")
    deny_all: bool = Field(default=False, description="Whether to deny all access")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the permission")


class PermissionCreate(PermissionBase):
    """Schema for creating permissions."""
    pass


class PermissionUpdate(BaseModel):
    """Schema for updating permissions."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    model_name: Optional[str] = Field(None, max_length=255)
    scope: Optional[str] = Field(None)
    rules: Optional[Dict[str, Any]] = Field(None)
    is_active: Optional[bool] = Field(None)
    allow_all: Optional[bool] = Field(None)
    deny_all: Optional[bool] = Field(None)
    description: Optional[str] = Field(None, max_length=1000)


class PermissionResponse(PermissionBase):
    """Schema for permission responses."""
    
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Who created this permission")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    usage_count: int = Field(default=0, description="Number of times used")
    
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=()
    )


class PermissionSummary(BaseModel):
    """Brief schema for permission summaries."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    id: str
    model_id: str
    model_name: Optional[str]
    scope: Optional[str]
    is_active: bool
    allow_all: bool
    deny_all: bool
    usage_count: int
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=()
    )


class PermissionCheck(BaseModel):
    """Schema for permission check requests."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str = Field(..., description="AI model to check permissions for")
    context_entry_id: Optional[str] = Field(None, description="Specific context entry to check")
    scope: Optional[str] = Field(None, description="Scope to check access for")
    tags: Optional[List[str]] = Field(None, description="Tags to check access for")
    context_type: Optional[str] = Field(None, description="Context type to check")


class PermissionCheckResult(BaseModel):
    """Schema for permission check results."""
    
    allowed: bool = Field(..., description="Whether access is allowed")
    reason: str = Field(..., description="Reason for the decision")
    applicable_permissions: List[str] = Field(..., description="IDs of applicable permissions")
    denied_by: Optional[str] = Field(None, description="What specifically denied access")
    allowed_scopes: List[str] = Field(default_factory=list, description="Scopes the model has access to")
    check_time_ms: Optional[int] = Field(None, description="Time taken to check permissions")


class ModelPermissionsSummary(BaseModel):
    """Schema for summarizing all permissions for a model."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str = Field(..., description="AI model identifier")
    model_name: Optional[str] = Field(None, description="Human-readable model name")
    total_permissions: int = Field(..., description="Total number of permission rules")
    active_permissions: int = Field(..., description="Number of active permission rules")
    allowed_scopes: List[str] = Field(..., description="All allowed scopes")
    has_unrestricted_access: bool = Field(..., description="Whether model has unrestricted access")
    is_denied_access: bool = Field(..., description="Whether model is denied all access")
    last_used: Optional[datetime] = Field(None, description="Last time permissions were used")
    usage_count: int = Field(default=0, description="Total usage count across all permissions")


class BulkPermissionOperation(BaseModel):
    """Schema for bulk permission operations."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    operation: str = Field(..., description="Operation type")
    model_ids: Optional[List[str]] = Field(None, description="Model IDs to operate on")
    permission_ids: Optional[List[str]] = Field(None, description="Permission IDs to operate on")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Operation parameters")


class PermissionTemplate(BaseModel):
    """Schema for permission templates."""
    
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    scope: str = Field(..., description="Default scope")
    rules: Dict[str, Any] = Field(..., description="Default rules")


class PermissionAuditEntry(BaseModel):
    """Schema for permission audit entries."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    timestamp: datetime = Field(..., description="When the action occurred")
    action: str = Field(..., description="What action was performed")
    model_id: str = Field(..., description="Which model was involved")
    permission_id: Optional[str] = Field(None, description="Which permission was involved")
    context_entry_id: Optional[str] = Field(None, description="Which context entry was accessed")
    result: str = Field(..., description="Result of the action (allowed/denied)")
    reason: Optional[str] = Field(None, description="Reason for the result")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")