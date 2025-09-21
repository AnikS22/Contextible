"""API endpoints for MCP (Model Context Protocol) integration."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db_session
from ..models.mcp import MCPConnection, MCPProvider
from ..integrations.mcp.manager import mcp_manager

router = APIRouter(prefix="/mcp", tags=["MCP"])


class MCPConnectionCreate(BaseModel):
    """Schema for creating MCP connections."""
    name: str = Field(..., min_length=1, max_length=255, description="Connection name")
    provider_type: str = Field(..., min_length=1, max_length=50, description="Provider type")
    endpoint: str = Field(..., min_length=1, max_length=500, description="MCP server endpoint")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Connection configuration")


class MCPConnectionResponse(BaseModel):
    """Schema for MCP connection responses."""
    id: str
    name: str
    provider_type: str
    endpoint: str
    config: Dict[str, Any]
    status: str
    last_connected_at: Optional[str] = None
    last_error: Optional[str] = None
    error_count: int
    capabilities: List[str]
    resources: List[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MCPProviderCreate(BaseModel):
    """Schema for creating MCP providers."""
    connection_id: str = Field(..., description="MCP connection ID")
    model_id: str = Field(..., min_length=1, max_length=255, description="AI model ID")
    enabled: bool = Field(default=True, description="Whether provider is enabled")
    allowed_resources: Optional[List[str]] = Field(default_factory=list, description="Allowed resources")
    allowed_tools: Optional[List[str]] = Field(default_factory=list, description="Allowed tools")
    cache_duration_seconds: int = Field(default=300, ge=60, le=3600, description="Cache duration")
    max_requests_per_minute: int = Field(default=60, ge=1, le=1000, description="Rate limit")
    inject_recent_activity: bool = Field(default=True, description="Inject recent activity")
    inject_scheduled_events: bool = Field(default=True, description="Inject scheduled events")
    context_template: Optional[str] = Field(None, description="Custom context template")


class MCPProviderResponse(BaseModel):
    """Schema for MCP provider responses."""
    id: str
    connection_id: str
    model_id: str
    enabled: bool
    allowed_resources: List[str]
    allowed_tools: List[str]
    cache_duration_seconds: int
    max_requests_per_minute: int
    inject_recent_activity: bool
    inject_scheduled_events: bool
    context_template: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MCPContextRequest(BaseModel):
    """Schema for MCP context requests."""
    model_id: str = Field(..., description="AI model ID")
    context_type: str = Field(default="recent_activity", description="Type of context")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")


class MCPSearchRequest(BaseModel):
    """Schema for MCP search requests."""
    model_id: str = Field(..., description="AI model ID")
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")


@router.get("/connections", response_model=List[MCPConnectionResponse])
async def get_mcp_connections(
    status: Optional[str] = Query(None, description="Filter by status"),
    provider_type: Optional[str] = Query(None, description="Filter by provider type"),
    db: Session = Depends(get_db_session)
):
    """Get all MCP connections."""
    query = db.query(MCPConnection)
    
    if status:
        query = query.filter(MCPConnection.status == status)
    if provider_type:
        query = query.filter(MCPConnection.provider_type == provider_type)
    
    connections = query.all()
    return [connection.to_dict() for connection in connections]


@router.post("/connections", response_model=MCPConnectionResponse)
async def create_mcp_connection(
    connection_data: MCPConnectionCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new MCP connection."""
    connection_id = await mcp_manager.add_connection(
        name=connection_data.name,
        provider_type=connection_data.provider_type,
        endpoint=connection_data.endpoint,
        config=connection_data.config
    )
    
    # Get the created connection
    connection = db.query(MCPConnection).filter(
        MCPConnection.id == connection_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return connection.to_dict()


@router.delete("/connections/{connection_id}")
async def delete_mcp_connection(
    connection_id: str,
    db: Session = Depends(get_db_session)
):
    """Delete an MCP connection."""
    success = await mcp_manager.remove_connection(connection_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return {"message": "Connection deleted successfully"}


@router.get("/connections/{connection_id}/status")
async def get_connection_status(connection_id: str):
    """Get detailed status of an MCP connection."""
    status = mcp_manager.get_connection_status()
    
    # Find specific connection
    for conn in status["connections"]:
        if conn["id"] == connection_id:
            return conn
    
    raise HTTPException(status_code=404, detail="Connection not found")


@router.get("/providers", response_model=List[MCPProviderResponse])
async def get_mcp_providers(
    model_id: Optional[str] = Query(None, description="Filter by model ID"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: Session = Depends(get_db_session)
):
    """Get all MCP providers."""
    query = db.query(MCPProvider)
    
    if model_id:
        query = query.filter(MCPProvider.model_id == model_id)
    if enabled is not None:
        query = query.filter(MCPProvider.enabled == enabled)
    
    providers = query.all()
    return [provider.to_dict() for provider in providers]


@router.post("/providers", response_model=MCPProviderResponse)
async def create_mcp_provider(
    provider_data: MCPProviderCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new MCP provider."""
    success = await mcp_manager.enable_provider_for_model(
        connection_id=provider_data.connection_id,
        model_id=provider_data.model_id,
        enabled=provider_data.enabled,
        allowed_resources=provider_data.allowed_resources,
        allowed_tools=provider_data.allowed_tools
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to create provider")
    
    # Get the created provider
    provider = db.query(MCPProvider).filter(
        MCPProvider.connection_id == provider_data.connection_id,
        MCPProvider.model_id == provider_data.model_id
    ).first()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return provider.to_dict()


@router.put("/providers/{provider_id}")
async def update_mcp_provider(
    provider_id: str,
    provider_data: MCPProviderCreate,
    db: Session = Depends(get_db_session)
):
    """Update an MCP provider."""
    provider = db.query(MCPProvider).filter(
        MCPProvider.id == provider_id
    ).first()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Update provider
    provider.enabled = provider_data.enabled
    provider.allowed_resources = provider_data.allowed_resources
    provider.allowed_tools = provider_data.allowed_tools
    provider.cache_duration_seconds = provider_data.cache_duration_seconds
    provider.max_requests_per_minute = provider_data.max_requests_per_minute
    provider.inject_recent_activity = provider_data.inject_recent_activity
    provider.inject_scheduled_events = provider_data.inject_scheduled_events
    provider.context_template = provider_data.context_template
    
    db.commit()
    
    return provider.to_dict()


@router.delete("/providers/{provider_id}")
async def delete_mcp_provider(
    provider_id: str,
    db: Session = Depends(get_db_session)
):
    """Delete an MCP provider."""
    provider = db.query(MCPProvider).filter(
        MCPProvider.id == provider_id
    ).first()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    db.delete(provider)
    db.commit()
    
    return {"message": "Provider deleted successfully"}


@router.post("/context")
async def get_mcp_context(request: MCPContextRequest):
    """Get MCP context for a specific model."""
    context = await mcp_manager.get_context_for_model(
        model_id=request.model_id,
        context_type=request.context_type,
        limit=request.limit
    )
    
    return {
        "model_id": request.model_id,
        "context_type": request.context_type,
        "context": context,
        "length": len(context)
    }


@router.post("/search")
async def search_mcp_data(request: MCPSearchRequest):
    """Search across MCP providers for a specific model."""
    results = await mcp_manager.search_mcp_data(
        model_id=request.model_id,
        query=request.query,
        limit=request.limit
    )
    
    return {
        "model_id": request.model_id,
        "query": request.query,
        "results": results,
        "total": len(results)
    }


@router.get("/status")
async def get_mcp_status():
    """Get overall MCP system status."""
    return mcp_manager.get_connection_status()


@router.post("/connections/{connection_id}/test")
async def test_mcp_connection(connection_id: str):
    """Test an MCP connection."""
    status = mcp_manager.get_connection_status()
    
    # Find specific connection
    for conn in status["connections"]:
        if conn["id"] == connection_id:
            if conn["connected"]:
                return {
                    "status": "success",
                    "message": "Connection is active",
                    "capabilities": conn["capabilities"],
                    "resources": conn["resources"],
                    "tools": conn["tools"]
                }
            else:
                return {
                    "status": "error",
                    "message": "Connection is not active"
                }
    
    raise HTTPException(status_code=404, detail="Connection not found")
