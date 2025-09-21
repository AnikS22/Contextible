"""MCP (Model Context Protocol) integration for ContextVault."""

from .client import MCPClient
from .manager import MCPManager
from .providers import (
    CalendarMCPProvider,
    GmailMCPProvider,
    FilesystemMCPProvider,
    BaseMCPProvider,
)
from contextvault.models.mcp import MCPConnection, MCPProvider

__all__ = [
    "MCPClient",
    "MCPManager", 
    "CalendarMCPProvider",
    "GmailMCPProvider",
    "FilesystemMCPProvider",
    "BaseMCPProvider",
    "MCPConnection",
    "MCPProvider",
]
