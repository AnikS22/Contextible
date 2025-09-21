"""Pydantic schemas for ContextVault API."""

from .context import (
    ContextEntryBase,
    ContextEntryCreate,
    ContextEntryUpdate,
    ContextEntryResponse,
    ContextEntryBrief,
    ContextQuery,
    ContextQueryResponse,
    ContextStats,
    BulkContextOperation,
    BulkOperationResult,
)

from .permissions import (
    PermissionBase,
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    PermissionSummary,
    PermissionCheck,
    PermissionCheckResult,
    ModelPermissionsSummary,
    BulkPermissionOperation,
    PermissionTemplate,
    PermissionAuditEntry,
)

from .responses import (
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
    WebSocketMessage,
    APIResponse,
)

__all__ = [
    # Context schemas
    "ContextEntryBase",
    "ContextEntryCreate", 
    "ContextEntryUpdate",
    "ContextEntryResponse",
    "ContextEntryBrief",
    "ContextQuery",
    "ContextQueryResponse",
    "ContextStats",
    "BulkContextOperation",
    "BulkOperationResult",
    
    # Permission schemas
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate", 
    "PermissionResponse",
    "PermissionSummary",
    "PermissionCheck",
    "PermissionCheckResult",
    "ModelPermissionsSummary",
    "BulkPermissionOperation",
    "PermissionTemplate",
    "PermissionAuditEntry",
    
    # Response schemas
    "SuccessResponse",
    "ErrorResponse",
    "ValidationErrorResponse",
    "PaginatedResponse",
    "HealthResponse",
    "ExportResponse",
    "ImportResponse",
    "BatchOperationResponse",
    "SearchResponse",
    "SystemStatsResponse",
    "ConfigResponse",
    "WebSocketMessage",
    "APIResponse",
]
