"""Pydantic schemas for API responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict


class SuccessResponse(BaseModel):
    """Standard success response schema."""
    
    success: bool = Field(default=True, description="Whether the operation was successful")
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    success: bool = Field(default=False, description="Whether the operation was successful")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Any] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for debugging")


class ValidationErrorResponse(ErrorResponse):
    """Response schema for validation errors."""
    
    error: str = Field(default="validation_error", description="Error type")
    validation_errors: List[Dict[str, Any]] = Field(..., description="Detailed validation errors")


class PaginatedResponse(BaseModel):
    """Schema for paginated responses."""
    
    items: List[Any] = Field(..., description="Items in this page")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-based)")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    has_next: bool = Field(..., description="Whether there is a next page")
    
    @classmethod
    def create(cls, items: List[Any], total: int, page: int, per_page: int):
        """Create a paginated response."""
        pages = (total + per_page - 1) // per_page  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_prev=page > 1,
            has_next=page < pages
        )


class HealthResponse(BaseModel):
    """Schema for health check responses."""
    
    status: str = Field(..., description="Health status (healthy, degraded, unhealthy)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    
    # Component health
    database: Dict[str, Any] = Field(..., description="Database health status")
    integrations: Dict[str, Any] = Field(default_factory=dict, description="Integration health status")
    
    # System metrics
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU usage percentage")
    disk_usage_percent: Optional[float] = Field(None, description="Disk usage percentage")
    
    # Application metrics
    total_context_entries: int = Field(default=0, description="Total context entries")
    total_permissions: int = Field(default=0, description="Total permission rules")
    total_sessions: int = Field(default=0, description="Total sessions")
    
    # Warnings and issues
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    issues: List[str] = Field(default_factory=list, description="Issue messages")


class ExportResponse(BaseModel):
    """Schema for export operation responses."""
    
    export_id: str = Field(..., description="Unique export identifier")
    format: str = Field(..., description="Export format (json, csv, etc.)")
    total_entries: int = Field(..., description="Total entries exported")
    file_size_bytes: int = Field(..., description="Size of export file")
    download_url: Optional[str] = Field(None, description="Download URL (if applicable)")
    expires_at: Optional[datetime] = Field(None, description="When the export expires")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Export creation time")
    
    # Export statistics
    entries_by_type: Dict[str, int] = Field(default_factory=dict, description="Count by context type")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="Date range of exported data")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Filters that were applied")


class ImportResponse(BaseModel):
    """Schema for import operation responses."""
    
    import_id: str = Field(..., description="Unique import identifier")
    status: str = Field(..., description="Import status (processing, completed, failed)")
    total_records: int = Field(default=0, description="Total records in import file")
    processed_records: int = Field(default=0, description="Records processed so far")
    successful_imports: int = Field(default=0, description="Successfully imported records")
    failed_imports: int = Field(default=0, description="Failed import records")
    
    # Progress tracking
    progress_percent: float = Field(default=0.0, description="Import progress percentage")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    # Error tracking
    errors: List[str] = Field(default_factory=list, description="Import error messages")
    warnings: List[str] = Field(default_factory=list, description="Import warning messages")
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Import start time")
    completed_at: Optional[datetime] = Field(None, description="Import completion time")


class BatchOperationResponse(BaseModel):
    """Schema for batch operation responses."""
    
    operation_id: str = Field(..., description="Unique operation identifier")
    operation_type: str = Field(..., description="Type of batch operation")
    total_items: int = Field(..., description="Total items to process")
    processed_items: int = Field(default=0, description="Items processed so far")
    successful_items: int = Field(default=0, description="Successfully processed items")
    failed_items: int = Field(default=0, description="Failed items")
    
    # Status and progress
    status: str = Field(..., description="Operation status")
    progress_percent: float = Field(default=0.0, description="Progress percentage")
    
    # Results
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Operation results")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Operation start time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    completed_at: Optional[datetime] = Field(None, description="Operation completion time")


class SearchResponse(BaseModel):
    """Schema for search operation responses."""
    
    query: str = Field(..., description="Search query")
    total_results: int = Field(..., description="Total number of results")
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    
    # Search metadata
    search_time_ms: int = Field(..., description="Search execution time in milliseconds")
    search_type: str = Field(default="text", description="Type of search performed")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Filters applied to search")
    
    # Pagination
    offset: int = Field(default=0, description="Results offset")
    limit: int = Field(..., description="Results limit")
    has_more: bool = Field(..., description="Whether there are more results")
    
    # Suggestions
    suggestions: List[str] = Field(default_factory=list, description="Search suggestions")
    did_you_mean: Optional[str] = Field(None, description="Alternative query suggestion")


class SystemStatsResponse(BaseModel):
    """Schema for system statistics responses."""
    
    # Database statistics
    total_context_entries: int = Field(default=0, description="Total context entries")
    total_permissions: int = Field(default=0, description="Total permission rules")
    total_sessions: int = Field(default=0, description="Total sessions")
    
    # Storage statistics
    database_size_bytes: int = Field(default=0, description="Database size in bytes")
    total_content_length: int = Field(default=0, description="Total character count of all content")
    average_entry_length: float = Field(default=0.0, description="Average entry length")
    
    # Activity statistics
    entries_created_today: int = Field(default=0, description="Entries created today")
    entries_accessed_today: int = Field(default=0, description="Entries accessed today")
    most_active_models: List[Dict[str, Any]] = Field(default_factory=list, description="Most active models")
    
    # Performance statistics
    average_query_time_ms: float = Field(default=0.0, description="Average query time")
    cache_hit_rate: float = Field(default=0.0, description="Cache hit rate percentage")
    
    # Time-based statistics
    stats_date: datetime = Field(default_factory=datetime.utcnow, description="Statistics date")
    data_retention_days: int = Field(default=90, description="Data retention period")
    
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class ConfigResponse(BaseModel):
    """Schema for configuration responses."""
    
    version: str = Field(..., description="Application version")
    environment: str = Field(default="production", description="Environment name")
    
    # Feature flags
    features: Dict[str, bool] = Field(default_factory=dict, description="Enabled features")
    
    # Limits and quotas
    max_context_entries: int = Field(..., description="Maximum context entries")
    max_context_length: int = Field(..., description="Maximum context length")
    max_file_size_mb: int = Field(default=10, description="Maximum file size for uploads")
    
    # Integration status
    integrations: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Integration status")
    
    # Client configuration
    api_base_url: str = Field(..., description="API base URL")
    websocket_url: Optional[str] = Field(None, description="WebSocket URL if available")
    
    # Security settings
    require_authentication: bool = Field(default=False, description="Whether authentication is required")
    allowed_origins: List[str] = Field(default_factory=list, description="Allowed CORS origins")


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages."""
    
    type: str = Field(..., description="Message type")
    data: Any = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    id: Optional[str] = Field(None, description="Message ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request/response")


# Union type for all possible API responses
APIResponse = Union[
    SuccessResponse,
    ErrorResponse,
    ValidationErrorResponse,
    PaginatedResponse,
    HealthResponse,
    ExportResponse,
    ImportResponse,
    BatchOperationResponse,
    SearchResponse,
    SystemStatsResponse,
    ConfigResponse,
]
