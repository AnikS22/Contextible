"""Database models for MCP (Model Context Protocol) integration."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, JSON, 
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base


class MCPConnectionStatus(PyEnum):
    """Status of MCP connections."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONNECTING = "connecting"


class MCPProviderType(PyEnum):
    """Types of MCP providers."""
    CALENDAR = "calendar"
    EMAIL = "email"
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    API = "api"
    CUSTOM = "custom"


class MCPConnection(Base):
    """MCP connection configuration and status."""
    
    __tablename__ = "mcp_connections"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        comment="Unique connection ID"
    )
    
    # Connection details
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        comment="Human-readable connection name"
    )
    
    provider_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        comment="Type of MCP provider"
    )
    
    endpoint: Mapped[str] = mapped_column(
        String(500), 
        nullable=False, 
        comment="MCP server endpoint (e.g., stdio command or TCP address)"
    )
    
    # Configuration
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=lambda: {},
        comment="MCP connection configuration"
    )
    
    # Status and metadata
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default=MCPConnectionStatus.INACTIVE.value,
        comment="Connection status"
    )
    
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        comment="Last successful connection timestamp"
    )
    
    last_error: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Last error message if any"
    )
    
    error_count: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Number of consecutive errors"
    )
    
    # Capabilities and resources
    capabilities: Mapped[Optional[List[str]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=list,
        comment="List of MCP capabilities (tools, resources, prompts)"
    )
    
    resources: Mapped[Optional[List[str]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=list,
        comment="List of available MCP resources"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="Creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )
    
    # Relationships
    providers = relationship(
        "MCPProvider", 
        back_populates="connection",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_mcp_connections_status", "status"),
        Index("ix_mcp_connections_provider_type", "provider_type"),
        Index("ix_mcp_connections_name", "name"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type,
            "endpoint": self.endpoint,
            "config": self.config or {},
            "status": self.status,
            "last_connected_at": self.last_connected_at.isoformat() if self.last_connected_at else None,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "capabilities": self.capabilities or [],
            "resources": self.resources or [],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def is_healthy(self) -> bool:
        """Check if connection is healthy."""
        return self.status == MCPConnectionStatus.ACTIVE.value and self.error_count < 5
    
    def record_success(self) -> None:
        """Record successful connection."""
        self.status = MCPConnectionStatus.ACTIVE.value
        self.last_connected_at = datetime.utcnow()
        self.last_error = None
        self.error_count = 0
    
    def record_error(self, error: str) -> None:
        """Record connection error."""
        self.status = MCPConnectionStatus.ERROR.value
        self.last_error = error
        self.error_count += 1


class MCPProvider(Base):
    """MCP provider configuration for specific AI models."""
    
    __tablename__ = "mcp_providers"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        comment="Unique provider ID"
    )
    
    # Relationships
    connection_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("mcp_connections.id", ondelete="CASCADE"),
        nullable=False,
        comment="MCP connection ID"
    )
    
    model_id: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        comment="AI model ID that can use this provider"
    )
    
    # Configuration
    enabled: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="Whether this provider is enabled for the model"
    )
    
    # Access control
    allowed_resources: Mapped[Optional[List[str]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=list,
        comment="List of allowed MCP resources for this model"
    )
    
    allowed_tools: Mapped[Optional[List[str]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=list,
        comment="List of allowed MCP tools for this model"
    )
    
    # Caching and limits
    cache_duration_seconds: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=300,  # 5 minutes
        comment="Cache duration for MCP responses"
    )
    
    max_requests_per_minute: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=60,
        comment="Rate limit for MCP requests"
    )
    
    # Context injection settings
    inject_recent_activity: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="Whether to inject recent activity context"
    )
    
    inject_scheduled_events: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="Whether to inject scheduled events context"
    )
    
    context_template: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Custom template for context injection"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="Creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )
    
    # Relationships
    connection = relationship("MCPConnection", back_populates="providers")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint("connection_id", "model_id", name="uq_mcp_provider_connection_model"),
        Index("ix_mcp_providers_model_id", "model_id"),
        Index("ix_mcp_providers_enabled", "enabled"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "model_id": self.model_id,
            "enabled": self.enabled,
            "allowed_resources": self.allowed_resources or [],
            "allowed_tools": self.allowed_tools or [],
            "cache_duration_seconds": self.cache_duration_seconds,
            "max_requests_per_minute": self.max_requests_per_minute,
            "inject_recent_activity": self.inject_recent_activity,
            "inject_scheduled_events": self.inject_scheduled_events,
            "context_template": self.context_template,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def can_access_resource(self, resource: str) -> bool:
        """Check if model can access specific resource."""
        if not self.enabled:
            return False
        if not self.allowed_resources:
            return True  # No restrictions
        return resource in self.allowed_resources
    
    def can_use_tool(self, tool: str) -> bool:
        """Check if model can use specific tool."""
        if not self.enabled:
            return False
        if not self.allowed_tools:
            return True  # No restrictions
        return tool in self.allowed_tools
