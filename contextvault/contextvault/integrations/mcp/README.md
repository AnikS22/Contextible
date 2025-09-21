# MCP Integration for ContextVault

This module provides integration with the Model Context Protocol (MCP) to connect local AI models with external data sources like calendars, email, filesystems, and more.

## Features

- **Local-first**: All data stays on your machine
- **Privacy-focused**: No cloud dependencies
- **Extensible**: Easy to add new MCP providers
- **Caching**: Intelligent caching for performance
- **Permissions**: Granular control per AI model
- **Context Injection**: Automatic context injection into AI prompts

## Supported MCP Providers

### Built-in Providers

1. **Calendar MCP** (`calendar`)
   - Recent calendar events
   - Upcoming scheduled events
   - Search calendar entries
   - Example endpoint: `stdio:calendar-mcp-server`

2. **Gmail MCP** (`gmail`)
   - Recent emails
   - Search emails
   - Email with deadlines/appointments
   - Example endpoint: `stdio:gmail-mcp-server`

3. **Filesystem MCP** (`filesystem`)
   - Recent file changes
   - File search
   - Files with date patterns
   - Example endpoint: `stdio:filesystem-mcp-server`

### Adding Custom MCP Providers

You can easily add custom MCP providers by:

1. Creating a new provider class extending `BaseMCPProvider`
2. Implementing the required methods
3. Registering it in the `MCPManager`

## Quick Start

### 1. Set up an MCP Server

First, you need to install and configure an MCP server. For example, for calendar integration:

```bash
# Install a calendar MCP server (example)
npm install -g @modelcontextprotocol/server-calendar
```

### 2. Add MCP Connection via API

```bash
curl -X POST "http://localhost:8000/api/mcp/connections" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Calendar",
    "provider_type": "calendar",
    "endpoint": "stdio:calendar-mcp-server",
    "config": {
      "calendar_id": "primary",
      "max_events": 50
    }
  }'
```

### 3. Enable for AI Model

```bash
curl -X POST "http://localhost:8000/api/mcp/providers" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": "your-connection-id",
    "model_id": "llama2",
    "enabled": true,
    "allowed_resources": ["calendar://primary"],
    "inject_recent_activity": true,
    "inject_scheduled_events": true
  }'
```

### 4. Test Context Injection

```bash
curl -X POST "http://localhost:8000/api/mcp/context" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "llama2",
    "context_type": "recent_activity",
    "limit": 10
  }'
```

## API Endpoints

### MCP Connections
- `GET /api/mcp/connections` - List all connections
- `POST /api/mcp/connections` - Create new connection
- `DELETE /api/mcp/connections/{id}` - Delete connection
- `GET /api/mcp/connections/{id}/status` - Get connection status
- `POST /api/mcp/connections/{id}/test` - Test connection

### MCP Providers
- `GET /api/mcp/providers` - List all providers
- `POST /api/mcp/providers` - Create new provider
- `PUT /api/mcp/providers/{id}` - Update provider
- `DELETE /api/mcp/providers/{id}` - Delete provider

### MCP Context
- `POST /api/mcp/context` - Get context for model
- `POST /api/mcp/search` - Search MCP data
- `GET /api/mcp/status` - Get overall status

## Configuration

### Connection Configuration

```json
{
  "name": "Human-readable name",
  "provider_type": "calendar|gmail|filesystem|custom",
  "endpoint": "stdio:command args",
  "config": {
    "custom_setting": "value"
  }
}
```

### Provider Configuration

```json
{
  "connection_id": "uuid",
  "model_id": "llama2",
  "enabled": true,
  "allowed_resources": ["resource://uri"],
  "allowed_tools": ["tool_name"],
  "cache_duration_seconds": 300,
  "max_requests_per_minute": 60,
  "inject_recent_activity": true,
  "inject_scheduled_events": true,
  "context_template": "Custom template: {data}"
}
```

## Popular MCP Servers

### Calendar
- **Google Calendar**: `@modelcontextprotocol/server-google-calendar`
- **Outlook**: `@modelcontextprotocol/server-outlook-calendar`

### Email
- **Gmail**: `@modelcontextprotocol/server-gmail`
- **Outlook**: `@modelcontextprotocol/server-outlook-mail`

### Filesystem
- **Local Files**: `@modelcontextprotocol/server-filesystem`
- **Git**: `@modelcontextprotocol/server-git`

### Development
- **GitHub**: `@modelcontextprotocol/server-github`
- **Linear**: `@modelcontextprotocol/server-linear`

## Security Considerations

1. **Local Only**: All MCP connections run locally
2. **No Cloud Data**: Data never leaves your machine
3. **Granular Permissions**: Control what each AI model can access
4. **Rate Limiting**: Built-in rate limiting per provider
5. **Caching**: Sensitive data cached locally only

## Troubleshooting

### Connection Issues
- Check MCP server is installed and running
- Verify endpoint format: `stdio:command args`
- Check server logs for errors

### Permission Issues
- Ensure provider is enabled for your model
- Check allowed_resources and allowed_tools
- Verify model_id matches your AI model

### Performance Issues
- Adjust cache_duration_seconds
- Reduce max_requests_per_minute
- Check MCP server performance

## Development

### Adding New Provider Types

1. Create provider class in `providers.py`
2. Register in `MCPManager._provider_types`
3. Update API schemas if needed
4. Add documentation

### Testing MCP Integration

```bash
# Test connection
curl -X POST "http://localhost:8000/api/mcp/connections/your-id/test"

# Get status
curl "http://localhost:8000/api/mcp/status"

# Search data
curl -X POST "http://localhost:8000/api/mcp/search" \
  -d '{"model_id": "llama2", "query": "meeting", "limit": 5}'
```

## Examples

### Calendar Integration
```bash
# Add Google Calendar
curl -X POST "http://localhost:8000/api/mcp/connections" \
  -d '{
    "name": "Google Calendar",
    "provider_type": "calendar",
    "endpoint": "stdio:@modelcontextprotocol/server-google-calendar",
    "config": {"calendar_id": "primary"}
  }'

# Enable for llama2
curl -X POST "http://localhost:8000/api/mcp/providers" \
  -d '{
    "connection_id": "connection-id",
    "model_id": "llama2",
    "enabled": true,
    "inject_scheduled_events": true
  }'
```

### Gmail Integration
```bash
# Add Gmail
curl -X POST "http://localhost:8000/api/mcp/connections" \
  -d '{
    "name": "Gmail",
    "provider_type": "gmail",
    "endpoint": "stdio:@modelcontextprotocol/server-gmail",
    "config": {"max_emails": 100}
  }'
```

This integration makes ContextVault incredibly powerful for local AI models to access real-world data while maintaining complete privacy and control.

