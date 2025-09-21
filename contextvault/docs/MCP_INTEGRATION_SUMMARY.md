# ContextVault MCP Integration: Complete Guide

## 🎯 **What is MCP Integration?**

ContextVault's MCP (Model Context Protocol) integration allows your AI models to access and understand external data sources like Google Calendar, Gmail, filesystems, and more. This creates a truly intelligent AI that knows your schedule, emails, and files.

## 🔗 **How It Works**

### **1. Data Source Connection**
- **MCP Servers**: Connect to external data sources (Calendar, Gmail, etc.)
- **Local Processing**: All data processing happens on your machine
- **Privacy First**: No data is sent to external services

### **2. Smart Context Analysis**
- **Query Analysis**: AI analyzes your questions to determine what data is needed
- **Context Selection**: Only relevant data is retrieved and injected
- **Intelligent Filtering**: Data is filtered based on query intent

### **3. Context Injection**
- **Automatic**: Context is injected automatically into AI prompts
- **Formatted**: Raw data is formatted into human-readable context
- **Relevant**: Only context that helps answer your question is included

## 📅 **Google Calendar Integration**

### **What Your AI Can Do**

**Before MCP Integration:**
```
User: "What meetings do I have today?"
AI: "I don't have access to your calendar information."
```

**After MCP Integration:**
```
User: "What meetings do I have today?"
AI: "You have a Team Standup Meeting at 9:00 AM in Conference Room A. 
     It's scheduled for 30 minutes and includes John, Sarah, and Mike 
     from your team. The meeting is for discussing daily blockers and progress."
```

### **Smart Query Recognition**

The system automatically detects when you need calendar information:

| Query Type | Keywords | Context Injected |
|------------|----------|------------------|
| **Today's Schedule** | "meetings today", "schedule today" | Today's events |
| **Deadlines** | "deadlines", "urgent", "due" | Upcoming deadlines |
| **Personal Appointments** | "personal", "appointment", "doctor" | Personal calendar events |
| **Week Overview** | "this week", "schedule overview" | Week's events |

### **Setup Process**

1. **Install Calendar MCP Server**:
   ```bash
   npm install -g @modelcontextprotocol/server-calendar
   ```

2. **Configure Google Calendar Access**:
   - Set up OAuth2 credentials or service account
   - Share calendar with service account

3. **Add to ContextVault**:
   ```bash
   python -m contextvault.cli mcp add "Google Calendar" calendar "stdio:calendar-mcp-server" --config '{"calendar_id": "primary"}'
   ```

4. **Enable for Your AI Model**:
   ```bash
   python -m contextvault.cli mcp enable mistral:latest connection-id "calendar.read"
   ```

## 📧 **Gmail Integration**

### **What Your AI Can Do**

**Email Context Examples:**
- "Any important emails I should check?"
- "What deadlines are mentioned in my emails?"
- "Who sent me the project update?"

### **Smart Email Analysis**

| Query Type | Context Retrieved |
|------------|-------------------|
| **Recent Emails** | Last 10 emails with summaries |
| **Deadline Emails** | Emails containing deadline keywords |
| **Important Emails** | Emails marked as important or from key contacts |
| **Project Updates** | Emails related to specific projects |

## 📁 **Filesystem Integration**

### **What Your AI Can Do**

**File Context Examples:**
- "What files did I work on recently?"
- "What's in my project folder?"
- "Any documents I should review?"

### **Smart File Analysis**

| Query Type | Context Retrieved |
|------------|-------------------|
| **Recent Files** | Recently modified files with metadata |
| **Project Files** | Files in specific project directories |
| **Document Search** | Files matching search criteria |

## 🧠 **Intelligent Context Injection**

### **Query Analysis Engine**

The system analyzes your queries to determine what context is needed:

```python
# Example query analysis
query = "What meetings do I have today?"

# Analysis results
keywords_detected = ["meetings", "today"]
context_type = "calendar_events"
time_filter = "today"
data_source = "calendar"

# Context retrieved and injected
calendar_events = get_calendar_events(date="today")
formatted_context = format_calendar_context(calendar_events)
inject_into_prompt(formatted_context)
```

### **Context Formatting**

Raw data is transformed into AI-friendly context:

**Raw Calendar Event:**
```json
{
  "title": "Team Meeting",
  "start_time": "2025-09-19T09:00:00Z",
  "attendees": ["john@company.com"],
  "location": "Conference Room A"
}
```

**Formatted Context:**
```
Calendar Event:
- Title: Team Meeting
- Date: 2025-09-19 at 09:00
- Location: Conference Room A
- Attendees: john@company.com
```

## 🔧 **CLI Management**

### **MCP Connection Management**

```bash
# List all MCP connections
python -m contextvault.cli mcp list

# Add new connection
python -m contextvault.cli mcp add "My Calendar" calendar "stdio:calendar-mcp-server"

# Enable for model
python -m contextvault.cli mcp enable mistral:latest connection-id "calendar.read"

# Check status
python -m contextvault.cli mcp status

# Search MCP data
python -m contextvault.cli mcp search mistral:latest "meetings today"
```

### **Provider Management**

```bash
# List providers
python -m contextvault.cli mcp providers

# Enable/disable providers
python -m contextvault.cli mcp enable mistral:latest connection-id "calendar.read,email.read"
```

## 🎯 **Real-World Examples**

### **Daily Planning Assistant**

```
User: "What's my schedule like today?"
AI: "You have a busy day ahead:
     - 9:00 AM: Team Standup (30 min, Conference Room A)
     - 2:00 PM: Client Call (1 hour, Zoom)
     - 4:00 PM: Project Review (1 hour, Conference Room B)
     
     You have breaks at 12-1 PM and 3-4 PM for lunch and prep time."
```

### **Deadline Management**

```
User: "Any important deadlines coming up?"
AI: "Yes, you have two critical deadlines:
     - Friday 5 PM: Q1 project deliverables (client submission)
     - Tuesday 10 AM: Client presentation preparation
     
     I also see an email from your manager mentioning a budget review due next week."
```

### **Meeting Preparation**

```
User: "Who's attending my team meeting?"
AI: "Your Team Standup Meeting at 9 AM includes:
     - John (Engineering Lead)
     - Sarah (Product Manager) 
     - Mike (Designer)
     
     The meeting is in Conference Room A and focuses on daily blockers and progress updates."
```

## 🔒 **Privacy & Security**

### **Local-First Architecture**
- **No Cloud Storage**: All data stays on your machine
- **Local Processing**: MCP servers run locally
- **Secure Authentication**: Uses official APIs (Google OAuth2, etc.)
- **Audit Logging**: Track all data access

### **Granular Permissions**
- **Model-Level**: Control which AI models can access which data
- **Scope-Based**: Fine-grained permissions (read, write, specific calendars)
- **Connection-Level**: Enable/disable specific data sources

## 🚀 **Getting Started**

### **Quick Setup**

1. **Install ContextVault**:
   ```bash
   git clone https://github.com/yourusername/contextvault.git
   cd contextvault && python -m contextvault.cli setup
   ```

2. **Add Google Calendar**:
   ```bash
   # Install calendar MCP server
   npm install -g @modelcontextprotocol/server-calendar
   
   # Add to ContextVault
   python -m contextvault.cli mcp add "Calendar" calendar "stdio:calendar-mcp-server"
   ```

3. **Enable for Your AI**:
   ```bash
   python -m contextvault.cli mcp enable mistral:latest connection-id "calendar.read"
   ```

4. **Test It**:
   ```bash
   python -m contextvault.cli mcp demo
   curl http://localhost:11435/api/generate -d '{"model":"mistral:latest","prompt":"What meetings do I have today?"}'
   ```

### **Available Data Sources**

- **📅 Google Calendar**: Meetings, appointments, deadlines
- **📧 Gmail**: Recent emails, important messages, deadlines
- **📁 Filesystem**: Recent files, project documents, search results
- **🔍 Custom MCP Servers**: Extensible for any data source

## 🎉 **Benefits**

### **Dramatically Improved AI Responses**
- **Specific Information**: AI knows your actual schedule, emails, files
- **Contextual Answers**: Responses based on real data, not generic advice
- **Proactive Insights**: AI can identify patterns and suggest actions

### **Seamless Integration**
- **Automatic**: Context injection happens automatically
- **Intelligent**: Only relevant context is included
- **Fast**: Optimized for real-time responses

### **Privacy-First**
- **Local Processing**: All data stays on your machine
- **No External Dependencies**: Works completely offline
- **Secure**: Uses official APIs and authentication

**Your AI now has access to your calendar, emails, and files - making it a truly intelligent personal assistant that knows your life! 🧠📅📧**
