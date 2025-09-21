"""MCP client for communicating with MCP servers."""

import asyncio
import json
import logging
import subprocess
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class MCPRequest:
    """MCP request structure."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None


@dataclass
class MCPResponse:
    """MCP response structure."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPClient:
    """Client for communicating with MCP servers."""
    
    def __init__(self, connection_id: str, endpoint: str, config: Optional[Dict[str, Any]] = None):
        self.connection_id = connection_id
        self.endpoint = endpoint
        self.config = config or {}
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._capabilities: Dict[str, Any] = {}
        self._resources: List[Dict[str, Any]] = []
        self._tools: List[Dict[str, Any]] = []
        self._connected = False
        
    async def connect(self) -> bool:
        """Connect to MCP server."""
        try:
            if self.endpoint.startswith("stdio:"):
                # Stdio-based connection
                command = self.endpoint[6:].split()
                self.process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=0
                )
                logger.info(f"Connected to MCP server via stdio: {' '.join(command)}")
            else:
                # TCP/HTTP connection (future implementation)
                logger.warning(f"TCP/HTTP MCP connections not yet implemented: {self.endpoint}")
                return False
            
            # Initialize the connection
            await self._initialize()
            self._connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.connection_id}: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                logger.error(f"Error disconnecting from MCP server: {e}")
            finally:
                self.process = None
        
        self._connected = False
        logger.info(f"Disconnected from MCP server {self.connection_id}")
    
    async def _initialize(self) -> None:
        """Initialize MCP connection and get capabilities."""
        # Send initialize request
        init_request = MCPRequest(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "resources": {"subscribe": True, "listChanged": True},
                    "tools": {},
                    "prompts": {}
                },
                "clientInfo": {
                    "name": "contextvault",
                    "version": "0.1.0"
                }
            }
        )
        
        response = await self._send_request(init_request)
        if response and response.result:
            self._capabilities = response.result.get("capabilities", {})
            logger.info(f"MCP server capabilities: {self._capabilities}")
        
        # Get available resources
        await self._list_resources()
        
        # Get available tools
        await self._list_tools()
    
    async def _send_request(self, request: MCPRequest) -> Optional[MCPResponse]:
        """Send request to MCP server."""
        if not self.process or not self._connected:
            logger.error("MCP client not connected")
            return None
        
        request.id = self._request_id
        self._request_id += 1
        
        try:
            # Send request
            request_json = json.dumps({
                "jsonrpc": request.jsonrpc,
                "id": request.id,
                "method": request.method,
                "params": request.params
            }) + "\n"
            
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            
            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                logger.error("No response from MCP server")
                return None
            
            response_data = json.loads(response_line.strip())
            return MCPResponse(
                jsonrpc=response_data.get("jsonrpc"),
                id=response_data.get("id"),
                result=response_data.get("result"),
                error=response_data.get("error")
            )
            
        except Exception as e:
            logger.error(f"Error sending MCP request: {e}")
            return None
    
    async def _list_resources(self) -> None:
        """List available resources."""
        request = MCPRequest(method="resources/list")
        response = await self._send_request(request)
        
        if response and response.result:
            self._resources = response.result.get("resources", [])
            logger.info(f"Available MCP resources: {len(self._resources)}")
    
    async def _list_tools(self) -> None:
        """List available tools."""
        request = MCPRequest(method="tools/list")
        response = await self._send_request(request)
        
        if response and response.result:
            self._tools = response.result.get("tools", [])
            logger.info(f"Available MCP tools: {len(self._tools)}")
    
    async def get_resource(self, uri: str) -> Optional[Dict[str, Any]]:
        """Get resource content."""
        request = MCPRequest(
            method="resources/read",
            params={"uri": uri}
        )
        
        response = await self._send_request(request)
        if response and response.result:
            return response.result.get("contents", [{}])[0]
        
        return None
    
    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Call MCP tool."""
        request = MCPRequest(
            method="tools/call",
            params={
                "name": name,
                "arguments": arguments or {}
            }
        )
        
        response = await self._send_request(request)
        if response and response.result:
            return response.result
        
        return None
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities."""
        return self._capabilities
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Get available resources."""
        return self._resources
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get available tools."""
        return self._tools
    
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected and self.process and self.process.poll() is None


class MCPCache:
    """Cache for MCP responses."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, datetime] = {}
    
    def get(self, key: str, max_age_seconds: int = 300) -> Optional[Any]:
        """Get cached value if not expired."""
        if key not in self._cache:
            return None
        
        if key in self._timestamps:
            age = datetime.utcnow() - self._timestamps[key]
            if age.total_seconds() > max_age_seconds:
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
                return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Set cached value."""
        self._cache[key] = value
        self._timestamps[key] = datetime.utcnow()
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self._timestamps.clear()
    
    def cleanup_expired(self, max_age_seconds: int = 300) -> None:
        """Remove expired entries."""
        now = datetime.utcnow()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if (now - timestamp).total_seconds() > max_age_seconds
        ]
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
