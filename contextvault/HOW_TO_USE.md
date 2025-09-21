# How to Use ContextVault 🚀

## 🎯 **Quick Start (5 minutes)**

### **1. Clone and Setup**
```bash
# Clone from either repository
git clone https://github.com/AnikS22/Contextive.git
cd Contextive

# Or clone from the specific contextvault repo
git clone https://github.com/AnikS22/contextvault.git
cd contextvault

# Initialize ContextVault
python -m contextvault.cli setup
```

### **2. Start ContextVault**
```bash
# Start the proxy (this makes your AI smarter)
python -m contextvault.cli start
```

### **3. Test It**
```bash
# Test that it's working
python -m contextvault.cli demo

# Or test with a real AI query
curl -X POST http://localhost:11435/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "What do you know about me?"}'
```

## 🧠 **How ContextVault Works**

### **The Magic:**
1. **You ask your AI a question** (like normal)
2. **ContextVault intercepts** the request
3. **It analyzes your question** to see what context you need
4. **It retrieves relevant information** from your stored context
5. **It injects that context** into the AI prompt
6. **Your AI responds** with personalized, informed answers

### **Example:**
**Without ContextVault:**
```
You: "What meetings do I have today?"
AI: "I don't have access to your calendar."
```

**With ContextVault:**
```
You: "What meetings do I have today?"
AI: "You have a team standup at 9 AM and a client call at 2 PM."
```

## 📝 **Adding Your Personal Context**

### **Method 1: Using the CLI**
```bash
# Add personal information
python -m contextvault.cli context add \
  --title "My Programming Preferences" \
  --content "I prefer Python and JavaScript, working on web development projects, and I use VS Code as my editor."

# Add project information
python -m contextvault.cli context add \
  --title "Current Project" \
  --content "Working on a React app with TypeScript for a client. Deadline is next Friday."

# Add personal details
python -m contextvault.cli context add \
  --title "About Me" \
  --content "I'm a software developer living in San Francisco, I have a cat named Whiskers, and I enjoy hiking on weekends."
```

### **Method 2: Using the Web Dashboard**
```bash
# Start the dashboard
python -m contextvault.cli system dashboard

# Open http://localhost:8080 in your browser
# Click "Add Context" and fill in your information
```

### **Method 3: Using the API**
```bash
# Add context via API
curl -X POST http://localhost:11435/api/context \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Schedule",
    "content": "I work 9-5, have lunch at 12, and prefer morning meetings.",
    "context_type": "schedule"
  }'
```

## 🔗 **Connecting External Data (MCP Integration)**

### **Google Calendar Integration**
```bash
# 1. Install calendar MCP server
npm install -g @modelcontextprotocol/server-calendar

# 2. Add calendar connection
python -m contextvault.cli mcp add "My Calendar" calendar "stdio:calendar-mcp-server" \
  --config '{"calendar_id": "primary"}'

# 3. Enable for your AI model
python -m contextvault.cli mcp enable mistral:latest connection-id "calendar.read"
```

### **Gmail Integration**
```bash
# 1. Install Gmail MCP server
npm install -g @modelcontextprotocol/server-gmail

# 2. Add Gmail connection
python -m contextvault.cli mcp add "My Gmail" gmail "stdio:gmail-mcp-server"

# 3. Enable for your AI model
python -m contextvault.cli mcp enable mistral:latest connection-id "email.read"
```

## 🎯 **Real-World Usage Examples**

### **Daily Planning**
```bash
# Ask about your schedule
curl -X POST http://localhost:11435/api/generate \
  -d '{"model": "mistral:latest", "prompt": "What does my day look like today?"}'

# Get project updates
curl -X POST http://localhost:11435/api/generate \
  -d '{"model": "mistral:latest", "prompt": "What should I work on today?"}'
```

### **Personal Assistant**
```bash
# Ask about your preferences
curl -X POST http://localhost:11435/api/generate \
  -d '{"model": "mistral:latest", "prompt": "What programming language should I learn next?"}'

# Get personalized advice
curl -X POST http://localhost:11435/api/generate \
  -d '{"model": "mistral:latest", "prompt": "Recommend a weekend activity for me."}'
```

### **Work Context**
```bash
# Ask about your projects
curl -X POST http://localhost:11435/api/generate \
  -d '{"model": "mistral:latest", "prompt": "What are my current project priorities?"}'

# Get work-related suggestions
curl -X POST http://localhost:11435/api/generate \
  -d '{"model": "mistral:latest", "prompt": "How should I prepare for my client meeting?"}'
```

## 🛠️ **Management Commands**

### **Context Management**
```bash
# List all your context
python -m contextvault.cli context list

# Search context
python -m contextvault.cli context search "programming"

# Update context
python -m contextvault.cli context update context-id --content "Updated information"

# Delete context
python -m contextvault.cli context delete context-id
```

### **System Management**
```bash
# Check system status
python -m contextvault.cli system status

# View logs
python -m contextvault.cli system logs

# Start/stop services
python -m contextvault.cli system start
python -m contextvault.cli system stop

# Open web dashboard
python -m contextvault.cli system dashboard
```

### **MCP Management**
```bash
# List MCP connections
python -m contextvault.cli mcp list

# Check MCP status
python -m contextvault.cli mcp status

# Search MCP data
python -m contextvault.cli mcp search mistral:latest "meetings today"
```

## 🎨 **Customization**

### **Templates**
```bash
# List available templates
python -m contextvault.cli templates list

# Set active template
python -m contextvault.cli templates set assistant

# Preview template
python -m contextvault.cli templates preview assistant
```

### **Permissions**
```bash
# List permissions
python -m contextvault.cli permissions list

# Grant access to model
python -m contextvault.cli permissions grant mistral:latest "personal_info"

# Revoke access
python -m contextvault.cli permissions revoke mistral:latest "sensitive_data"
```

## 🧪 **Testing and Validation**

### **Run Tests**
```bash
# Test everything is working
python -m contextvault.cli test bulletproof

# Test MCP integration
python -m contextvault.cli mcp demo

# Test context effectiveness
python -m contextvault.cli test effectiveness
```

### **Diagnostics**
```bash
# Run full diagnostics
python -m contextvault.cli diagnose

# Check specific components
python -m contextvault.cli diagnose database
python -m contextvault.cli diagnose proxy
python -m contextvault.cli diagnose context
```

## 🌐 **Web Dashboard**

### **Access the Dashboard**
```bash
# Start the dashboard
python -m contextvault.cli system dashboard

# Open in browser: http://localhost:8080
```

### **Dashboard Features**
- **View Context**: See all your stored context
- **Add Context**: Easily add new information
- **System Status**: Monitor ContextVault health
- **MCP Connections**: Manage external data sources
- **Analytics**: See how context is being used

## 🚨 **Troubleshooting**

### **Common Issues**

**1. ContextVault not starting:**
```bash
# Check if Ollama is running
ollama list

# Check ContextVault status
python -m contextvault.cli system status

# View logs
python -m contextvault.cli system logs
```

**2. No context being injected:**
```bash
# Check if you have context stored
python -m contextvault.cli context list

# Test context retrieval
python -m contextvault.cli test context

# Check permissions
python -m contextvault.cli permissions list
```

**3. MCP connections not working:**
```bash
# Check MCP status
python -m contextvault.cli mcp status

# Test MCP integration
python -m contextvault.cli mcp demo

# Check connections
python -m contextvault.cli mcp list
```

## 🎯 **Pro Tips**

### **1. Start Simple**
- Begin with basic personal information
- Add context gradually
- Test with simple queries first

### **2. Use Specific Titles**
- "My Programming Preferences" instead of "Info"
- "Current Project Status" instead of "Work"
- "Personal Schedule" instead of "Schedule"

### **3. Regular Updates**
- Update context as your situation changes
- Remove outdated information
- Keep context relevant and fresh

### **4. Test Different Queries**
- Try various ways of asking questions
- Test edge cases
- See how context injection improves responses

## 🚀 **Next Steps**

1. **Add your personal context** using the CLI or dashboard
2. **Test with simple queries** to see the difference
3. **Connect external data sources** (calendar, email) if desired
4. **Customize templates and permissions** for your needs
5. **Share with the community** and get feedback

**Your AI is now a personal assistant that actually knows you! 🧠✨**
