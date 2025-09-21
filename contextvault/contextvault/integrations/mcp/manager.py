"""MCP manager for orchestrating MCP connections and providers."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from contextvault.database import get_db_session
from contextvault.models.mcp import MCPConnection, MCPProvider
from .client import MCPClient, MCPCache
from .providers import (
    BaseMCPProvider,
    CalendarMCPProvider,
    GmailMCPProvider,
    FilesystemMCPProvider,
)

logger = logging.getLogger(__name__)


class MCPManager:
    """Manages MCP connections and providers."""
    
    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}
        self._providers: Dict[str, BaseMCPProvider] = {}
        self._caches: Dict[str, MCPCache] = {}
        self._provider_types = {
            "calendar": CalendarMCPProvider,
            "gmail": GmailMCPProvider,
            "email": GmailMCPProvider,  # Alias
            "filesystem": FilesystemMCPProvider,
            "files": FilesystemMCPProvider,  # Alias
        }
    
    async def initialize(self) -> None:
        """Initialize MCP manager and connect to configured servers."""
        logger.info("Initializing MCP manager...")
        
        db = next(get_db_session())
        try:
            # Get all active connections
            connections = db.query(MCPConnection).filter(
                MCPConnection.status == "active"
            ).all()
            
            for connection in connections:
                await self._connect_connection(connection)
            
            logger.info(f"MCP manager initialized with {len(self._clients)} connections")
            
        finally:
            db.close()
    
    async def shutdown(self) -> None:
        """Shutdown MCP manager and disconnect all clients."""
        logger.info("Shutting down MCP manager...")
        
        for client in self._clients.values():
            await client.disconnect()
        
        self._clients.clear()
        self._providers.clear()
        self._caches.clear()
        
        logger.info("MCP manager shutdown complete")
    
    async def add_connection(
        self,
        name: str,
        provider_type: str,
        endpoint: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new MCP connection."""
        import uuid
        
        connection_id = str(uuid.uuid4())
        
        db = next(get_db_session())
        try:
            # Create connection record
            connection = MCPConnection(
                id=connection_id,
                name=name,
                provider_type=provider_type,
                endpoint=endpoint,
                config=config or {},
                status="connecting"
            )
            
            db.add(connection)
            db.commit()
            
            # Try to connect
            success = await self._connect_connection(connection)
            
            if success:
                connection.status = "active"
                connection.record_success()
            else:
                connection.status = "error"
                connection.record_error("Failed to connect during setup")
            
            db.commit()
            
            logger.info(f"Added MCP connection {name} ({connection_id}): {connection.status}")
            return connection_id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding MCP connection: {e}")
            raise
        finally:
            db.close()
    
    async def remove_connection(self, connection_id: str) -> bool:
        """Remove an MCP connection."""
        db = next(get_db_session())
        try:
            connection = db.query(MCPConnection).filter(
                MCPConnection.id == connection_id
            ).first()
            
            if not connection:
                return False
            
            # Disconnect client
            if connection_id in self._clients:
                await self._clients[connection_id].disconnect()
                del self._clients[connection_id]
            
            # Remove providers
            provider_ids = [
                p.id for p in connection.providers
            ]
            for provider_id in provider_ids:
                if provider_id in self._providers:
                    del self._providers[provider_id]
            
            # Remove cache
            if connection_id in self._caches:
                del self._caches[connection_id]
            
            # Remove from database
            db.delete(connection)
            db.commit()
            
            logger.info(f"Removed MCP connection {connection_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error removing MCP connection: {e}")
            return False
        finally:
            db.close()
    
    async def enable_provider_for_model(
        self,
        connection_id: str,
        model_id: str,
        enabled: bool = True,
        allowed_resources: Optional[List[str]] = None,
        allowed_tools: Optional[List[str]] = None
    ) -> bool:
        """Enable/disable MCP provider for specific model."""
        import uuid
        
        db = next(get_db_session())
        try:
            # Find existing provider
            provider = db.query(MCPProvider).filter(
                MCPProvider.connection_id == connection_id,
                MCPProvider.model_id == model_id
            ).first()
            
            if provider:
                # Update existing
                provider.enabled = enabled
                if allowed_resources is not None:
                    provider.allowed_resources = allowed_resources
                if allowed_tools is not None:
                    provider.allowed_tools = allowed_tools
            else:
                # Create new provider
                provider = MCPProvider(
                    id=str(uuid.uuid4()),
                    connection_id=connection_id,
                    model_id=model_id,
                    enabled=enabled,
                    allowed_resources=allowed_resources or [],
                    allowed_tools=allowed_tools or []
                )
                db.add(provider)
            
            db.commit()
            
            # Update in-memory provider if it exists
            if provider.id in self._providers:
                # Recreate provider with new settings
                await self._create_provider(provider)
            
            logger.info(f"Updated MCP provider for model {model_id}: enabled={enabled}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating MCP provider: {e}")
            return False
        finally:
            db.close()
    
    async def get_context_for_model(
        self,
        model_id: str,
        context_type: str = "recent_activity",
        limit: int = 10
    ) -> str:
        """Get MCP context for specific model."""
        context_parts = []
        
        # Get enabled providers for this model
        db = next(get_db_session())
        try:
            providers = db.query(MCPProvider).join(MCPConnection).filter(
                MCPProvider.model_id == model_id,
                MCPProvider.enabled == True,
                MCPConnection.status == "active"
            ).all()
            
            for provider in providers:
                if provider.id in self._providers:
                    mcp_provider = self._providers[provider.id]
                    
                    try:
                        if context_type == "recent_activity":
                            if provider.inject_recent_activity:
                                data = await mcp_provider.get_recent_activity(limit)
                                if data:
                                    context = mcp_provider.format_context(
                                        data, 
                                        provider.context_template
                                    )
                                    if context:
                                        context_parts.append(f"## {mcp_provider.provider_type.title()} Recent Activity\n{context}")
                        
                        elif context_type == "scheduled_events":
                            if provider.inject_scheduled_events:
                                data = await mcp_provider.get_scheduled_events(7)
                                if data:
                                    context = mcp_provider.format_context(
                                        data, 
                                        provider.context_template
                                    )
                                    if context:
                                        context_parts.append(f"## {mcp_provider.provider_type.title()} Upcoming Events\n{context}")
                        
                    except Exception as e:
                        logger.error(f"Error getting context from provider {provider.id}: {e}")
            
        finally:
            db.close()
        
        return "\n\n".join(context_parts)
    
    async def search_mcp_data(
        self,
        model_id: str,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search across all MCP providers for a model."""
        results = []
        
        # Get enabled providers for this model
        db = next(get_db_session())
        try:
            providers = db.query(MCPProvider).join(MCPConnection).filter(
                MCPProvider.model_id == model_id,
                MCPProvider.enabled == True,
                MCPConnection.status == "active"
            ).all()
            
            for provider in providers:
                if provider.id in self._providers:
                    mcp_provider = self._providers[provider.id]
                    
                    try:
                        data = await mcp_provider.search(query, limit)
                        for item in data:
                            item['source'] = mcp_provider.provider_type
                            item['provider_id'] = provider.id
                        results.extend(data)
                        
                    except Exception as e:
                        logger.error(f"Error searching provider {provider.id}: {e}")
            
        finally:
            db.close()
        
        return results[:limit]
    
    async def _connect_connection(self, connection: MCPConnection) -> bool:
        """Connect to an MCP server."""
        try:
            # Create client
            client = MCPClient(
                connection.connection_id,
                connection.endpoint,
                connection.config
            )
            
            # Connect
            success = await client.connect()
            
            if success:
                # Store client
                self._clients[connection.id] = client
                
                # Create cache
                cache = MCPCache()
                self._caches[connection.id] = cache
                
                # Create providers
                providers = connection.providers
                for provider in providers:
                    await self._create_provider(provider)
                
                logger.info(f"Connected to MCP server {connection.name}")
                return True
            else:
                logger.error(f"Failed to connect to MCP server {connection.name}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to MCP server {connection.name}: {e}")
            return False
    
    async def _create_provider(self, provider: MCPProvider) -> None:
        """Create MCP provider instance."""
        if provider.connection_id not in self._clients:
            return
        
        client = self._clients[provider.connection_id]
        cache = self._caches[provider.connection_id]
        
        # Get provider class
        provider_class = self._provider_types.get(provider.connection.provider_type)
        if not provider_class:
            logger.warning(f"Unknown MCP provider type: {provider.connection.provider_type}")
            return
        
        # Create provider instance
        mcp_provider = provider_class(client, cache)
        self._providers[provider.id] = mcp_provider
        
        logger.info(f"Created MCP provider {provider.id} for model {provider.model_id}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get status of all MCP connections."""
        status = {
            "total_connections": len(self._clients),
            "active_connections": 0,
            "providers": len(self._providers),
            "connections": []
        }
        
        for connection_id, client in self._clients.items():
            connection_status = {
                "id": connection_id,
                "connected": client.is_connected(),
                "capabilities": client.get_capabilities(),
                "resources": len(client.get_resources()),
                "tools": len(client.get_tools())
            }
            status["connections"].append(connection_status)
            
            if client.is_connected():
                status["active_connections"] += 1
        
        return status


# Global MCP manager instance
mcp_manager = MCPManager()
