"""MCP provider implementations for different data sources."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .client import MCPClient, MCPCache

logger = logging.getLogger(__name__)


class BaseMCPProvider(ABC):
    """Base class for MCP providers."""
    
    def __init__(self, client: MCPClient, cache: MCPCache):
        self.client = client
        self.cache = cache
        self.provider_type = "base"
    
    @abstractmethod
    async def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity/events."""
        pass
    
    @abstractmethod
    async def get_scheduled_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get scheduled events."""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for content."""
        pass
    
    def format_context(self, data: List[Dict[str, Any]], template: Optional[str] = None) -> str:
        """Format data as context string."""
        if not data:
            return ""
        
        if template:
            # Use custom template
            return template.format(data=data)
        
        # Default formatting
        context_parts = []
        for item in data:
            if isinstance(item, dict):
                context_parts.append(f"- {item.get('title', item.get('summary', str(item)))}")
                if item.get('date'):
                    context_parts.append(f"  Date: {item['date']}")
                if item.get('description'):
                    context_parts.append(f"  Description: {item['description']}")
        
        return "\n".join(context_parts)


class CalendarMCPProvider(BaseMCPProvider):
    """MCP provider for calendar data."""
    
    def __init__(self, client: MCPClient, cache: MCPCache):
        super().__init__(client, cache)
        self.provider_type = "calendar"
    
    async def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent calendar events."""
        cache_key = f"calendar_recent_{limit}"
        cached = self.cache.get(cache_key, max_age_seconds=300)
        if cached:
            return cached
        
        try:
            # Try to get recent events from calendar MCP
            events = []
            
            # Look for calendar resources
            resources = self.client.get_resources()
            calendar_resources = [r for r in resources if 'calendar' in r.get('name', '').lower()]
            
            for resource in calendar_resources:
                content = await self.client.get_resource(resource['uri'])
                if content:
                    # Parse calendar events from content
                    events.extend(self._parse_calendar_events(content))
            
            # Limit results
            events = events[:limit]
            
            # Cache results
            self.cache.set(cache_key, events)
            return events
            
        except Exception as e:
            logger.error(f"Error getting recent calendar activity: {e}")
            return []
    
    async def get_scheduled_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming calendar events."""
        cache_key = f"calendar_upcoming_{days_ahead}"
        cached = self.cache.get(cache_key, max_age_seconds=600)
        if cached:
            return cached
        
        try:
            # Try to get upcoming events
            events = []
            
            # Use tools if available
            tools = self.client.get_tools()
            calendar_tools = [t for t in tools if 'calendar' in t.get('name', '').lower()]
            
            for tool in calendar_tools:
                if 'list_events' in tool.get('name', ''):
                    result = await self.client.call_tool(
                        tool['name'],
                        {
                            'days_ahead': days_ahead,
                            'limit': 20
                        }
                    )
                    if result:
                        events.extend(self._parse_tool_events(result))
            
            # Cache results
            self.cache.set(cache_key, events)
            return events
            
        except Exception as e:
            logger.error(f"Error getting scheduled calendar events: {e}")
            return []
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search calendar events."""
        cache_key = f"calendar_search_{query}_{limit}"
        cached = self.cache.get(cache_key, max_age_seconds=600)
        if cached:
            return cached
        
        try:
            events = []
            
            # Use search tools if available
            tools = self.client.get_tools()
            search_tools = [t for t in tools if 'search' in t.get('name', '').lower()]
            
            for tool in search_tools:
                result = await self.client.call_tool(
                    tool['name'],
                    {
                        'query': query,
                        'limit': limit
                    }
                )
                if result:
                    events.extend(self._parse_tool_events(result))
            
            # Cache results
            self.cache.set(cache_key, events)
            return events
            
        except Exception as e:
            logger.error(f"Error searching calendar: {e}")
            return []
    
    def _parse_calendar_events(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse calendar events from MCP content."""
        events = []
        
        # Try to extract events from different content formats
        if 'events' in content:
            events = content['events']
        elif 'items' in content:
            events = content['items']
        elif isinstance(content, list):
            events = content
        
        # Normalize event format
        normalized_events = []
        for event in events:
            if isinstance(event, dict):
                normalized_events.append({
                    'title': event.get('title', event.get('summary', 'Untitled')),
                    'date': event.get('start', event.get('date', event.get('datetime'))),
                    'description': event.get('description', event.get('details', '')),
                    'location': event.get('location', ''),
                    'type': 'calendar_event'
                })
        
        return normalized_events
    
    def _parse_tool_events(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse events from tool results."""
        events = []
        
        if 'events' in result:
            events = result['events']
        elif 'items' in result:
            events = result['items']
        elif isinstance(result, list):
            events = result
        
        return self._parse_calendar_events({'events': events})


class GmailMCPProvider(BaseMCPProvider):
    """MCP provider for Gmail data."""
    
    def __init__(self, client: MCPClient, cache: MCPCache):
        super().__init__(client, cache)
        self.provider_type = "gmail"
    
    async def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent emails."""
        cache_key = f"gmail_recent_{limit}"
        cached = self.cache.get(cache_key, max_age_seconds=300)
        if cached:
            return cached
        
        try:
            emails = []
            
            # Look for email resources
            resources = self.client.get_resources()
            email_resources = [r for r in resources if 'gmail' in r.get('name', '').lower()]
            
            for resource in email_resources:
                content = await self.client.get_resource(resource['uri'])
                if content:
                    emails.extend(self._parse_emails(content))
            
            # Limit results
            emails = emails[:limit]
            
            # Cache results
            self.cache.set(cache_key, emails)
            return emails
            
        except Exception as e:
            logger.error(f"Error getting recent Gmail activity: {e}")
            return []
    
    async def get_scheduled_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get emails with upcoming deadlines or appointments."""
        cache_key = f"gmail_upcoming_{days_ahead}"
        cached = self.cache.get(cache_key, max_age_seconds=600)
        if cached:
            return cached
        
        try:
            emails = []
            
            # Use tools to find emails with dates
            tools = self.client.get_tools()
            search_tools = [t for t in tools if 'search' in t.get('name', '').lower()]
            
            for tool in search_tools:
                result = await self.client.call_tool(
                    tool['name'],
                    {
                        'query': 'has:attachment OR subject:(deadline OR meeting OR appointment)',
                        'limit': 20
                    }
                )
                if result:
                    emails.extend(self._parse_tool_emails(result))
            
            # Cache results
            self.cache.set(cache_key, emails)
            return emails
            
        except Exception as e:
            logger.error(f"Error getting upcoming Gmail events: {e}")
            return []
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search emails."""
        cache_key = f"gmail_search_{query}_{limit}"
        cached = self.cache.get(cache_key, max_age_seconds=600)
        if cached:
            return cached
        
        try:
            emails = []
            
            # Use search tools
            tools = self.client.get_tools()
            search_tools = [t for t in tools if 'search' in t.get('name', '').lower()]
            
            for tool in search_tools:
                result = await self.client.call_tool(
                    tool['name'],
                    {
                        'query': query,
                        'limit': limit
                    }
                )
                if result:
                    emails.extend(self._parse_tool_emails(result))
            
            # Cache results
            self.cache.set(cache_key, emails)
            return emails
            
        except Exception as e:
            logger.error(f"Error searching Gmail: {e}")
            return []
    
    def _parse_emails(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse emails from MCP content."""
        emails = []
        
        if 'messages' in content:
            emails = content['messages']
        elif 'items' in content:
            emails = content['items']
        elif isinstance(content, list):
            emails = content
        
        # Normalize email format
        normalized_emails = []
        for email in emails:
            if isinstance(email, dict):
                normalized_emails.append({
                    'title': email.get('subject', email.get('title', 'No Subject')),
                    'date': email.get('date', email.get('timestamp')),
                    'description': email.get('snippet', email.get('body', '')),
                    'sender': email.get('from', email.get('sender', '')),
                    'type': 'email'
                })
        
        return normalized_emails
    
    def _parse_tool_emails(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse emails from tool results."""
        emails = []
        
        if 'messages' in result:
            emails = result['messages']
        elif 'items' in result:
            emails = result['items']
        elif isinstance(result, list):
            emails = result
        
        return self._parse_emails({'messages': emails})


class FilesystemMCPProvider(BaseMCPProvider):
    """MCP provider for filesystem data."""
    
    def __init__(self, client: MCPClient, cache: MCPCache):
        super().__init__(client, cache)
        self.provider_type = "filesystem"
    
    async def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently modified files."""
        cache_key = f"filesystem_recent_{limit}"
        cached = self.cache.get(cache_key, max_age_seconds=300)
        if cached:
            return cached
        
        try:
            files = []
            
            # Use filesystem tools
            tools = self.client.get_tools()
            fs_tools = [t for t in tools if 'file' in t.get('name', '').lower()]
            
            for tool in fs_tools:
                if 'list_recent' in tool.get('name', ''):
                    result = await self.client.call_tool(
                        tool['name'],
                        {
                            'limit': limit,
                            'days': 7
                        }
                    )
                    if result:
                        files.extend(self._parse_files(result))
            
            # Cache results
            self.cache.set(cache_key, files)
            return files
            
        except Exception as e:
            logger.error(f"Error getting recent filesystem activity: {e}")
            return []
    
    async def get_scheduled_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get files with upcoming deadlines (based on filename patterns)."""
        cache_key = f"filesystem_upcoming_{days_ahead}"
        cached = self.cache.get(cache_key, max_age_seconds=600)
        if cached:
            return cached
        
        try:
            files = []
            
            # Look for files with date patterns
            tools = self.client.get_tools()
            search_tools = [t for t in tools if 'search' in t.get('name', '').lower()]
            
            for tool in search_tools:
                result = await self.client.call_tool(
                    tool['name'],
                    {
                        'pattern': '*deadline* OR *due* OR *meeting*',
                        'limit': 20
                    }
                )
                if result:
                    files.extend(self._parse_files(result))
            
            # Cache results
            self.cache.set(cache_key, files)
            return files
            
        except Exception as e:
            logger.error(f"Error getting upcoming filesystem events: {e}")
            return []
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search files."""
        cache_key = f"filesystem_search_{query}_{limit}"
        cached = self.cache.get(cache_key, max_age_seconds=600)
        if cached:
            return cached
        
        try:
            files = []
            
            # Use search tools
            tools = self.client.get_tools()
            search_tools = [t for t in tools if 'search' in t.get('name', '').lower()]
            
            for tool in search_tools:
                result = await self.client.call_tool(
                    tool['name'],
                    {
                        'query': query,
                        'limit': limit
                    }
                )
                if result:
                    files.extend(self._parse_files(result))
            
            # Cache results
            self.cache.set(cache_key, files)
            return files
            
        except Exception as e:
            logger.error(f"Error searching filesystem: {e}")
            return []
    
    def _parse_files(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse files from MCP content."""
        files = []
        
        if 'files' in content:
            files = content['files']
        elif 'items' in content:
            files = content['items']
        elif isinstance(content, list):
            files = content
        
        # Normalize file format
        normalized_files = []
        for file in files:
            if isinstance(file, dict):
                normalized_files.append({
                    'title': file.get('name', file.get('filename', 'Unknown')),
                    'date': file.get('modified', file.get('date')),
                    'description': file.get('path', file.get('description', '')),
                    'size': file.get('size'),
                    'type': 'file'
                })
        
        return normalized_files
