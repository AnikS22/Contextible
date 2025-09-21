# Google Calendar Integration with ContextVault MCP

This guide shows you how to connect Google Calendar to ContextVault using the Model Context Protocol (MCP), enabling your AI to understand and reference your calendar data.

## 🎯 **What This Enables**

With Google Calendar integration, your AI can:

- **Answer calendar questions**: "What meetings do I have today?"
- **Provide schedule context**: "What's my schedule like this week?"
- **Identify deadlines**: "Any important deadlines coming up?"
- **Personal appointments**: "Do I have any personal appointments?"
- **Meeting details**: "Who's attending my team meeting?"

## 🚀 **Setup Process**

### **Step 1: Install Calendar MCP Server**

```bash
# Install the calendar MCP server
npm install -g @modelcontextprotocol/server-calendar

# Or using pip (if available)
pip install mcp-server-calendar
```

### **Step 2: Configure Google Calendar Access**

#### **Option A: OAuth2 Setup (Recommended)**

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Calendar API

2. **Create OAuth2 Credentials**:
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the credentials JSON file

3. **Configure MCP Server**:
   ```bash
   # Set environment variables
   export GOOGLE_CREDENTIALS_PATH="/path/to/credentials.json"
   export GOOGLE_CALENDAR_ID="primary"  # or specific calendar ID
   ```

#### **Option B: Service Account (For Personal Use)**

1. **Create Service Account**:
   - In Google Cloud Console, go to "IAM & Admin" → "Service Accounts"
   - Create new service account
   - Download the service account key JSON

2. **Share Calendar**:
   - In Google Calendar, share your calendar with the service account email
   - Give "See all event details" permission

3. **Configure**:
   ```bash
   export GOOGLE_SERVICE_ACCOUNT_PATH="/path/to/service-account.json"
   export GOOGLE_CALENDAR_ID="your-calendar-id"
   ```

### **Step 3: Add MCP Connection to ContextVault**

```bash
# Add calendar connection
curl -X POST "http://localhost:11435/api/mcp/connections" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Google Calendar",
    "provider_type": "calendar",
    "endpoint": "stdio:calendar-mcp-server",
    "config": {
      "calendar_id": "primary",
      "max_events": 50,
      "credentials_path": "/path/to/credentials.json"
    }
  }'
```

### **Step 4: Enable for Your AI Model**

```bash
# Grant calendar access to your model
curl -X POST "http://localhost:11435/api/mcp/providers" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "mistral:latest",
    "connection_id": "google-calendar-connection-id",
    "enabled": true,
    "scopes": ["calendar.read"]
  }'
```

### **Step 5: Test the Integration**

```bash
# Test calendar integration
python -m contextvault.cli diagnose

# Test with a calendar query
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral:latest",
    "prompt": "What meetings do I have today?"
  }'
```

## 📊 **How It Works**

### **1. Query Analysis**

ContextVault analyzes your queries to determine if calendar context is needed:

```python
# Query analysis examples
"What meetings do I have today?" → calendar_events (today)
"What's my schedule this week?" → calendar_events (week)
"Any deadlines coming up?" → deadlines_and_urgent
"Do I have personal appointments?" → personal_events
```

### **2. Context Retrieval**

Based on the query analysis, appropriate calendar data is retrieved:

```python
# Context retrieval logic
if query_contains(["meeting", "schedule", "calendar"]):
    events = get_calendar_events(time_range="relevant")
    
if query_contains(["deadline", "urgent", "important"]):
    events = get_calendar_events(filter_type="deadlines")
    
if query_contains(["personal", "appointment"]):
    events = get_calendar_events(calendar="personal")
```

### **3. Context Injection**

Calendar data is formatted and injected into the AI prompt:

```
Previous Context:
Calendar Event:
- Title: Team Standup Meeting
- Date: 2025-09-19 at 09:00
- Location: Conference Room A
- Attendees: john@company.com, sarah@company.com
- Description: Daily team sync - discuss blockers and progress

Current Conversation:
User: What meetings do I have today?
```

### **4. Enhanced AI Response**

With calendar context, the AI provides specific, helpful responses:

**Without Context**: "I don't have access to your calendar information."

**With Context**: "You have a Team Standup Meeting today at 9:00 AM in Conference Room A. It's scheduled for 30 minutes and includes John, Sarah, and Mike from your team. The meeting is for discussing daily blockers and progress."

## 🔧 **Configuration Options**

### **Calendar MCP Server Configuration**

```json
{
  "calendar_id": "primary",
  "max_events": 50,
  "time_range_days": 30,
  "include_personal": true,
  "include_work": true,
  "credentials_path": "/path/to/credentials.json"
}
```

### **ContextVault MCP Provider Settings**

```json
{
  "model_id": "mistral:latest",
  "enabled": true,
  "scopes": ["calendar.read"],
  "cache_duration": 300,
  "max_context_events": 10
}
```

## 🛠️ **Troubleshooting**

### **Common Issues**

**1. Authentication Errors**
```bash
# Check credentials
python -m contextvault.cli diagnose

# Verify Google Calendar API is enabled
# Check OAuth2 credentials are valid
```

**2. No Calendar Data**
```bash
# Check MCP connection status
curl http://localhost:11435/api/mcp/connections

# Verify calendar permissions
# Ensure calendar is shared with service account
```

**3. Context Not Injecting**
```bash
# Check provider permissions
curl http://localhost:11435/api/mcp/providers

# Verify model has calendar access
python -m contextvault.cli permissions list
```

### **Debug Mode**

```bash
# Enable debug logging
export CONTEXTVAULT_DEBUG=true
python -m contextvault.cli start

# Check logs
python -m contextvault.cli logs
```

## 📈 **Advanced Features**

### **Multiple Calendars**

```bash
# Add multiple calendar connections
curl -X POST "http://localhost:11435/api/mcp/connections" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Work Calendar",
    "provider_type": "calendar",
    "endpoint": "stdio:calendar-mcp-server",
    "config": {
      "calendar_id": "work@company.com",
      "max_events": 30
    }
  }'
```

### **Custom Context Templates**

```bash
# Set calendar-specific template
python -m contextvault.cli templates set calendar_aware

# Create custom template for calendar queries
python -m contextvault.cli templates preview calendar_aware
```

### **Smart Filtering**

The system automatically filters calendar data based on query context:

- **Time-based**: Today, this week, next month
- **Type-based**: Meetings, appointments, deadlines
- **Calendar-based**: Work vs personal
- **Urgency-based**: Important vs routine events

## 🔒 **Privacy & Security**

- **Local-first**: All calendar data stays on your machine
- **No cloud storage**: ContextVault doesn't store your calendar data
- **Secure authentication**: Uses Google's OAuth2 or service accounts
- **Granular permissions**: Control which models can access calendar data
- **Audit logging**: Track all calendar data access

## 🎯 **Example Use Cases**

### **Daily Planning**
```
User: "What's my schedule like today?"
AI: "You have a busy day ahead: Team Standup at 9 AM, Client Call at 2 PM, and Project Review at 4 PM. You have a 1-hour break between 12-1 PM for lunch."
```

### **Meeting Preparation**
```
User: "Who's attending my team meeting?"
AI: "Your Team Standup Meeting at 9 AM includes John (Engineering), Sarah (Product), and Mike (Design). The meeting is in Conference Room A and focuses on daily blockers and progress updates."
```

### **Deadline Management**
```
User: "Any important deadlines coming up?"
AI: "Yes, you have a critical deadline: Q1 project deliverables are due this Friday at 5 PM. You also have a client presentation scheduled for next Tuesday at 10 AM."
```

### **Personal Schedule**
```
User: "Do I have any personal appointments this week?"
AI: "You have a doctor's appointment on Tuesday at 2:30 PM at City Medical Center, and lunch with Sarah on Wednesday at 12 PM at Downtown Cafe."
```

## 🚀 **Next Steps**

1. **Set up the integration** using the steps above
2. **Test with your calendar** to ensure it's working
3. **Configure permissions** for your AI models
4. **Try different query types** to see the smart context injection
5. **Add more calendars** if you have multiple Google accounts

**Your AI now has access to your calendar and can provide intelligent, context-aware responses about your schedule! 📅🤖**
