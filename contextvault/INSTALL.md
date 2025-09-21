# ContextVault Installation Guide

## 🚀 **Quick Installation**

### **Option 1: Git Clone (Recommended for Developers)**

```bash
# Clone the repository
git clone https://github.com/yourusername/contextvault.git
cd contextvault

# Install dependencies
pip install -r requirements.txt

# Initialize ContextVault
python -m contextvault.cli setup

# Start ContextVault
python -m contextvault.cli start
```

### **Option 2: Automated Installer**

```bash
# Download and run the installer
curl -fsSL https://raw.githubusercontent.com/yourusername/contextvault/main/install.sh | bash
```

### **Option 3: Manual Installation**

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Start Ollama
ollama serve &

# 3. Install a model
ollama pull mistral:latest

# 4. Clone ContextVault
git clone https://github.com/yourusername/contextvault.git
cd contextvault

# 5. Install Python dependencies
pip install -r requirements.txt

# 6. Setup ContextVault
python -m contextvault.cli setup

# 7. Start ContextVault
python -m contextvault.cli start
```

## 📋 **Prerequisites**

- **Python 3.8+** (3.11+ recommended)
- **Ollama** with at least one model (e.g., `mistral:latest`)
- **Git** (for cloning)

## 🔧 **Post-Installation**

### **Test Installation**

```bash
# Quick test
python -m contextvault.cli test

# Comprehensive test
python -m contextvault.cli test bulletproof

# Run demo
python -m contextvault.cli demo
```

### **Start Services**

```bash
# Start ContextVault proxy
python -m contextvault.cli start

# Start web dashboard (optional)
python -m contextvault.cli dashboard
```

### **Verify Installation**

```bash
# Check status
python -m contextvault.cli status

# Check health
python -m contextvault.cli health

# Run diagnostics
python -m contextvault.cli diagnose
```

## 🎯 **Usage**

### **Basic Usage**

Instead of connecting directly to Ollama:
```bash
# OLD WAY (generic responses)
curl http://localhost:11434/api/generate -d '{"model":"mistral:latest","prompt":"What pets do I have?"}'

# NEW WAY (personalized responses)
curl http://localhost:11435/api/generate -d '{"model":"mistral:latest","prompt":"What pets do I have?"}'
```

### **CLI Commands**

```bash
# System management
python -m contextvault.cli start
python -m contextvault.cli stop
python -m contextvault.cli status

# Context management
python -m contextvault.cli context add "I love Python programming"
python -m contextvault.cli context list
python -m contextvault.cli context search "programming"

# Permission management
python -m contextvault.cli permissions list
python -m contextvault.cli permissions grant mistral:latest preferences,notes

# Template management
python -m contextvault.cli templates list
python -m contextvault.cli templates set direct_instruction

# Testing and validation
python -m contextvault.cli test
python -m contextvault.cli demo
python -m contextvault.cli diagnose
```

### **Web Dashboard**

Access the web dashboard at `http://localhost:8080` for:
- System monitoring
- Context management
- Permission configuration
- Usage analytics

## 🛠️ **Configuration**

### **Main Config File**

Edit `~/.contextvault/config.yaml`:

```yaml
server:
  host: "127.0.0.1"
  port: 11435

ollama:
  host: "127.0.0.1"
  port: 11434

context:
  max_length: 2000
  max_entries: 10
  default_template: "direct_instruction"

logging:
  level: "INFO"
```

### **Configuration Commands**

```bash
# Show current config
python -m contextvault.cli config show

# Set config values
python -m contextvault.cli config set server.port 11436

# Validate config
python -m contextvault.cli config validate
```

## 🔌 **API Integration**

### **Python Integration**

```python
import requests

# Add context
requests.post('http://localhost:11435/api/context/add', json={
    'content': 'I prefer Python over JavaScript',
    'context_type': 'preference',
    'tags': ['programming']
})

# Use AI with context
response = requests.post('http://localhost:11435/api/generate', json={
    'model': 'mistral:latest',
    'prompt': 'What should I learn next?'
})
print(response.json()['response'])
```

### **Shell Integration**

```bash
#!/bin/bash

# Add context
curl -X POST http://localhost:11435/api/context/add \
  -H "Content-Type: application/json" \
  -d '{"content": "I work as a software engineer", "context_type": "note"}'

# Get AI response
curl -X POST http://localhost:11435/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "What do I do for work?"}' | \
  jq -r '.response'
```

## 🚨 **Troubleshooting**

### **Common Issues**

**ContextVault not starting:**
```bash
python -m contextvault.cli diagnose
python -m contextvault.cli fix
```

**No context being injected:**
```bash
# Check permissions
python -m contextvault.cli permissions list

# Check context entries
python -m contextvault.cli context list

# Test context retrieval
python -m contextvault.cli context search "test"
```

**Ollama connection issues:**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### **Logs and Debugging**

```bash
# View logs
python -m contextvault.cli logs

# Enable debug mode
export CONTEXTVAULT_DEBUG=true
python -m contextvault.cli start
```

### **Reset Installation**

```bash
# Reset to defaults
python -m contextvault.cli config reset

# Reinitialize database
rm ~/.contextvault/contextvault.db
python -m contextvault.cli setup
```

## 📚 **Next Steps**

1. **Add your personal context:**
   ```bash
   python -m contextvault.cli context add "I am a software engineer who loves Python"
   python -m contextvault.cli context add "I have two cats named Luna and Pixel"
   ```

2. **Configure permissions:**
   ```bash
   python -m contextvault.cli permissions grant mistral:latest preferences,notes,personal
   ```

3. **Test with your data:**
   ```bash
   python -m contextvault.cli demo
   ```

4. **Integrate with your tools:**
   - Use the API endpoints in your scripts
   - Set up the web dashboard for monitoring
   - Configure templates for your use case

## 🆘 **Support**

- **Documentation**: [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/contextvault/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/contextvault/discussions)

---

**ContextVault is now ready to give your AI models persistent memory! 🧠**
