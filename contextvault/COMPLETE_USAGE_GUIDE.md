# 🎯 ContextVault - Complete Usage Guide

## **✅ VERIFIED WORKING SYSTEM**

After rigorous testing, ContextVault is **fully functional** with all components working correctly:

- ✅ Database initialization and management
- ✅ CLI commands for context and permission management  
- ✅ REST API endpoints for programmatic access
- ✅ Ollama proxy with context injection
- ✅ Permission system with granular access control
- ✅ Context retrieval and injection pipeline

---

## **🚀 Quick Start (5 Minutes)**

### **1. Initialize ContextVault**
```bash
cd contextvault
./contextvault-cli init
```

### **2. Add Your First Context**
```bash
./contextvault-cli context add "I am a software engineer who loves Python and testing"
```

### **3. Set Up Permissions for Your Model**
```bash
./contextvault-cli permissions add mistral:latest --scope="preferences,notes" --description="Personal assistant"
```

### **4. Start the ContextVault Services**
```bash
# Terminal 1: Start API server
./contextvault-cli serve

# Terminal 2: Start Ollama proxy  
./contextvault-cli proxy
```

### **5. Use Ollama with Context Injection**
```bash
# Instead of: curl http://localhost:11434/api/generate
# Use:        curl http://localhost:11435/api/generate

curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "What do you know about me?", "stream": false}'
```

---

## **📋 Complete Command Reference**

### **Database Management**
```bash
./contextvault-cli init                    # Initialize database
./contextvault-cli status                  # Check system status
```

### **Context Management**
```bash
# Add context
./contextvault-cli context add "Your context here"
./contextvault-cli context add "More context" --tags="work,important"

# List context
./contextvault-cli context list
./contextvault-cli context list --limit=10

# Search context
./contextvault-cli context search "keyword"
./contextvault-cli context search "python" --limit=5

# View specific context
./contextvault-cli context show <entry-id>

# Update context
./contextvault-cli context update <entry-id> "New content"

# Delete context
./contextvault-cli context delete <entry-id>

# Get statistics
./contextvault-cli context stats

# Cleanup old entries
./contextvault-cli context cleanup --days=30
```

### **Permission Management**
```bash
# Add permissions for a model
./contextvault-cli permissions add mistral:latest --scope="preferences,notes"
./contextvault-cli permissions add codellama:13b --scope="work,projects" --description="Work assistant"

# List permissions
./contextvault-cli permissions list

# Update permissions
./contextvault-cli permissions update <permission-id> --scope="preferences,notes,work"

# Delete permissions
./contextvault-cli permissions delete <permission-id>

# Check permissions
./contextvault-cli permissions check mistral:latest --scope="preferences"
```

### **Server Management**
```bash
# Start API server
./contextvault-cli serve

# Start Ollama proxy
./contextvault-cli proxy

# Export data
./contextvault-cli export --output=backup.json

# Import data
./contextvault-cli import-data --file=backup.json
```

---

## **🔌 API Endpoints**

### **Context API**
```bash
# List all context entries
GET http://localhost:8000/api/context/

# Search context
GET http://localhost:8000/api/context/search/{query}

# Get specific context
GET http://localhost:8000/api/context/{entry_id}

# Create context
POST http://localhost:8000/api/context/
{
  "content": "Your context here",
  "context_type": "text",
  "tags": ["tag1", "tag2"]
}

# Update context
PUT http://localhost:8000/api/context/{entry_id}
{
  "content": "Updated content"
}

# Delete context
DELETE http://localhost:8000/api/context/{entry_id}
```

### **Permissions API**
```bash
# List permissions
GET http://localhost:8000/api/permissions/

# Check permissions
POST http://localhost:8000/api/permissions/check
{
  "model_id": "mistral:latest",
  "context_entry_id": "entry-id",
  "scope": "preferences"
}

# Create permission
POST http://localhost:8000/api/permissions/
{
  "model_id": "mistral:latest",
  "scope": "preferences,notes",
  "description": "Personal assistant"
}
```

### **Health Check**
```bash
GET http://localhost:8000/health/
GET http://localhost:11435/health
```

---

## **🤖 How Context Injection Works**

### **1. Request Flow**
```
User Request → Ollama Proxy (11435) → Context Retrieval → Permission Check → Ollama (11434) → Response
```

### **2. Context Retrieval Process**
1. **Extract Model ID** from request
2. **Check Permissions** for the model
3. **Search Context** based on prompt keywords
4. **Filter by Permissions** (only allowed scopes)
5. **Inject Context** into prompt using template
6. **Forward to Ollama** with enhanced prompt

### **3. Context Template**
```python
def get_context_template() -> str:
    return """Previous Context:
{context_entries}

Current Conversation:
{user_prompt}"""
```

### **4. Example Context Injection**
**Original Prompt:**
```
"What do you know about my preferences?"
```

**Enhanced Prompt (after injection):**
```
Previous Context:
I prefer Python over JavaScript for backend development. I like using FastAPI and SQLAlchemy.

Current Conversation:
What do you know about my preferences?
```

---

## **🔐 Permission System**

### **Scopes**
- `preferences` - Personal preferences and settings
- `notes` - Notes and documentation
- `work` - Work-related information
- `projects` - Project-specific context
- `secrets` - Sensitive information (restricted)

### **Permission Rules**
- **Model-specific**: Each AI model has its own permissions
- **Scope-based**: Control what types of context each model can access
- **Granular**: Fine-grained control over context access
- **Auditable**: All access attempts are logged

### **Example Permission Setup**
```bash
# Personal assistant with access to preferences and notes
./contextvault-cli permissions add mistral:latest --scope="preferences,notes"

# Work assistant with access to work and projects
./contextvault-cli permissions add codellama:13b --scope="work,projects"

# Restricted model with no access
./contextvault-cli permissions add deepseek-coder:6.7b --scope=""
```

---

## **📊 Monitoring and Debugging**

### **Check System Status**
```bash
./contextvault-cli status
```

### **View Context Access**
```bash
# Check access counts
./contextvault-cli context list
# Look for "Access Count" column

# Check specific entry
./contextvault-cli context show <entry-id>
```

### **Test Context Injection**
```bash
# Test with a model that has permissions
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "What do you know about me?", "stream": false}'

# Test with a model that has NO permissions
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "codellama:13b", "prompt": "What do you know about me?", "stream": false}'
```

### **API Health Checks**
```bash
# Check API server
curl http://localhost:8000/health/

# Check proxy
curl http://localhost:11435/health
```

---

## **🎯 Real-World Usage Examples**

### **Personal Assistant Setup**
```bash
# 1. Add personal context
./contextvault-cli context add "I live in San Francisco and work as a software engineer"
./contextvault-cli context add "I prefer Python, use VS Code, and love testing"

# 2. Set up permissions
./contextvault-cli permissions add mistral:latest --scope="preferences,notes"

# 3. Use with context injection
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "Where do I live and what do I do?", "stream": false}'
```

### **Work Assistant Setup**
```bash
# 1. Add work context
./contextvault-cli context add "Current project: ContextVault - local AI context management"
./contextvault-cli context add "Tech stack: Python, FastAPI, SQLAlchemy, Ollama"

# 2. Set up permissions
./contextvault-cli permissions add codellama:13b --scope="work,projects"

# 3. Use for work-related queries
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "codellama:13b", "prompt": "What am I working on?", "stream": false}'
```

### **Multi-Model Setup**
```bash
# Different models for different purposes
./contextvault-cli permissions add mistral:latest --scope="preferences,notes" --description="Personal"
./contextvault-cli permissions add codellama:13b --scope="work,projects" --description="Work"
./contextvault-cli permissions add deepseek-coder:6.7b --scope="" --description="No context access"
```

---

## **🔧 Troubleshooting**

### **Common Issues**

**1. "Address already in use"**
```bash
# Kill existing processes
pkill -f contextvault
# Then restart
./contextvault-cli serve
./contextvault-cli proxy
```

**2. "Model not found"**
```bash
# Check available models
curl http://localhost:11435/api/tags

# Add permissions for existing models
./contextvault-cli permissions add <model-name> --scope="preferences"
```

**3. "No context injection happening"**
```bash
# Check permissions
./contextvault-cli permissions list

# Check context entries
./contextvault-cli context list

# Test with simple query
curl -X POST "http://localhost:11435/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "Hello", "stream": false}'
```

**4. "Permission denied"**
```bash
# Check model permissions
./contextvault-cli permissions check <model-name> --scope="preferences"

# Add permissions if missing
./contextvault-cli permissions add <model-name> --scope="preferences,notes"
```

---

## **📈 Performance Tips**

### **Optimize Context Entries**
- Keep entries focused and specific
- Use tags for better organization
- Regular cleanup of old entries
- Avoid very long context entries

### **Model Selection**
- Use smaller models for simple tasks
- Use larger models for complex reasoning
- Set appropriate permissions per model

### **System Resources**
- Monitor memory usage via status command
- Use SSD storage for better performance
- Consider PostgreSQL for production use

---

## **🎉 Success Indicators**

You'll know ContextVault is working when:

✅ **Context injection**: Models respond with personal context  
✅ **Permission enforcement**: Models without permissions respond generically  
✅ **Access tracking**: Context entry access counts increase  
✅ **Health checks**: All endpoints return healthy status  
✅ **CLI commands**: All commands work without errors  

---

## **🚀 Next Steps**

1. **Add More Context**: Build up your personal knowledge base
2. **Fine-tune Permissions**: Adjust scope access per model
3. **Monitor Usage**: Check access patterns and optimize
4. **Scale Up**: Consider PostgreSQL for production use
5. **Integrate**: Use with your favorite AI applications

---

**ContextVault is now ready for production use! 🎉**
