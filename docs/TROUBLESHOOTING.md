# 🚨 Troubleshooting Guide

This guide helps you resolve common issues with Contextible.

## 🐛 Common Issues

### Installation Problems

#### ❌ "Python version too old"
**Error**: `Python 3.8+ required`

**Solution**:
```bash
# Check your Python version
python --version

# Install Python 3.8+ if needed
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
# Windows: Download from python.org
```

#### ❌ "No module named 'contextvault'"
**Error**: Module import errors during installation

**Solution**:
```bash
# Make sure you're in the right directory
cd Contextible/contextvault

# Install dependencies first
pip install -r requirements.txt

# Run installation again
python install_simple.py
```

#### ❌ "Database setup failed"
**Error**: Database initialization errors

**Solution**:
```bash
# Try manual database setup
python init_database.py

# If that fails, check permissions
ls -la contextvault.db

# Reset database (WARNING: loses all data)
rm contextvault.db
python init_database.py
```

### CLI Issues

#### ❌ "Unknown command: [command]"
**Error**: CLI doesn't recognize commands

**Solution**:
```bash
# Make sure you're using the correct CLI
python contextible.py

# Check available commands
contextvault> help

# Use full command names
contextvault> search "query"  # Not just "search"
```

#### ❌ "Database connection failed"
**Error**: CLI can't connect to database

**Solution**:
```bash
# Check if database exists
ls -la *.db

# Initialize database if missing
python init_database.py

# Check file permissions
ls -la contextvault.db
```

#### ❌ "EOF when reading a line"
**Error**: Input prompts fail in non-interactive mode

**Solution**:
```bash
# Run CLI interactively
python contextible.py

# Use non-interactive commands
echo 'list' | python contextible.py
```

### Context Injection Issues

#### ❌ "Context Injection: Not Working"
**Error**: AI responses are generic, no personalization

**Solution**:
```bash
# Check if proxy is running
contextvault> status

# Start the proxy
python scripts/ollama_proxy.py

# Check Ollama is running
ollama serve

# Test the connection
curl http://localhost:11434/api/tags
```

#### ❌ "Connection refused" errors
**Error**: Can't connect to Ollama or proxy

**Solution**:
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama
ollama serve

# Check ports
lsof -i :11434  # Ollama
lsof -i :11435  # Proxy

# Kill conflicting processes
pkill -f ollama
```

#### ❌ "No context found" messages
**Error**: AI doesn't have any context to inject

**Solution**:
```bash
# Add some context first
contextvault> add "My name is Alex and I'm a developer"

# Check your context
contextvault> list

# Search for specific context
contextvault> search "developer"
```

### Performance Issues

#### ❌ Slow context retrieval
**Error**: Context injection takes too long

**Solution**:
```bash
# Check system health
contextvault> health-check

# Review analytics
contextvault> analytics

# Optimize database
# (Database optimization coming in future versions)
```

#### ❌ High memory usage
**Error**: Contextible uses too much RAM

**Solution**:
```bash
# Check memory usage
ps aux | grep python

# Restart services
pkill -f ollama_proxy.py
python scripts/ollama_proxy.py

# Check for memory leaks
contextvault> health-check
```

### Model Detection Issues

#### ❌ "No models detected"
**Error**: Contextible can't find your AI models

**Solution**:
```bash
# Check if Ollama is running
ollama list

# Start Ollama if not running
ollama serve

# Pull a model if needed
ollama pull mistral:latest

# Check model detection
contextvault> models list
```

#### ❌ "Model permission denied"
**Error**: Models can't access context

**Solution**:
```bash
# Check model permissions
contextvault> models list

# Set permissions
contextvault> models set-permission mistral:latest --allow personal

# Check configuration
contextvault> config show
```

## 🔍 Debugging Steps

### 1. Check System Status
```bash
contextvault> health-check
```

This comprehensive check will show:
- Database connectivity
- Service status
- Performance metrics
- Error logs

### 2. Verify Installation
```bash
python verify_installation.py
```

### 3. Test Individual Components
```bash
contextvault> test-all
contextvault> test-injection
contextvault> test-retrieval
```

### 4. Check Logs
```bash
# Check for error logs
ls -la *.log

# View recent logs
tail -f contextvault.log

# Check system logs (macOS)
log show --predicate 'process == "python"' --last 1h
```

### 5. Reset Components
```bash
# Reset database (WARNING: loses data)
rm contextvault.db
python init_database.py

# Restart services
pkill -f ollama_proxy.py
python scripts/ollama_proxy.py

# Clear cache (if exists)
rm -rf __pycache__/
```

## 🛠️ Advanced Debugging

### Enable Verbose Logging
```bash
# Set debug environment variable
export CONTEXTIBLE_DEBUG=1

# Run with verbose output
python contextible.py
```

### Check Network Connections
```bash
# Test Ollama connection
curl -v http://localhost:11434/api/tags

# Test proxy connection
curl -v http://localhost:11435/health

# Check port availability
netstat -an | grep 11434
netstat -an | grep 11435
```

### Database Debugging
```bash
# Check database integrity
sqlite3 contextvault.db "PRAGMA integrity_check;"

# View table structure
sqlite3 contextvault.db ".schema"

# Check table contents
sqlite3 contextvault.db "SELECT COUNT(*) FROM context_entries;"
```

### Performance Profiling
```bash
# Check system resources
top -p $(pgrep -f contextible)

# Monitor network traffic
tcpdump -i lo port 11434

# Check disk usage
du -sh contextvault.db
```

## 📋 Diagnostic Checklist

When reporting issues, please include:

### System Information
- [ ] Operating System (macOS/Windows/Linux)
- [ ] Python version (`python --version`)
- [ ] Contextible version (from `contextvault> version`)
- [ ] Ollama version (`ollama --version`)

### Installation Details
- [ ] Installation method used
- [ ] Any error messages during installation
- [ ] Virtual environment used (yes/no)

### Current State
- [ ] Output of `contextvault> health-check`
- [ ] Output of `contextvault> status`
- [ ] List of running processes (`ps aux | grep -E "(ollama|contextible)"`)
- [ ] Network connections (`netstat -an | grep -E "(11434|11435)"`)

### Context Information
- [ ] Number of context entries (`contextvault> analytics`)
- [ ] Sample context entries (`contextvault> list --limit 5`)
- [ ] Search results (`contextvault> search "test"`)

### Error Details
- [ ] Exact error message
- [ ] Steps to reproduce the issue
- [ ] Expected vs actual behavior
- [ ] Screenshots or logs if applicable

## 🆘 Getting Help

### Before Asking for Help

1. **Read this guide** - Many issues are covered here
2. **Check existing issues** - Search [GitHub Issues](https://github.com/AnikS22/Contextible/issues)
3. **Try the diagnostic checklist** - Gather information about your system
4. **Test with minimal setup** - Try with just one context entry

### How to Report Issues

1. **Create a GitHub issue** with the diagnostic information above
2. **Use clear, descriptive titles** like "Context injection not working on macOS with Python 3.11"
3. **Include system information** and error messages
4. **Provide steps to reproduce** the issue
5. **Be patient** - We're volunteers helping in our spare time

### Community Support

- **GitHub Discussions**: [Ask questions and share tips](https://github.com/AnikS22/Contextible/discussions)
- **GitHub Issues**: [Report bugs and request features](https://github.com/AnikS22/Contextible/issues)
- **Documentation**: Check all docs in the `/docs` folder

### Emergency Workarounds

If Contextible is completely broken:

1. **Use CLI only** (without proxy):
   ```bash
   python contextible.py
   contextvault> add "your context"
   contextvault> list
   ```

2. **Direct Ollama** (without context injection):
   ```bash
   ollama run mistral:latest "your question"
   ```

3. **Reset everything**:
   ```bash
   rm -rf venv contextvault.db
   python install_simple.py
   ```

## 🔄 Recovery Procedures

### Complete Reset
```bash
# Stop all services
pkill -f ollama
pkill -f ollama_proxy.py

# Remove all data (WARNING: loses everything)
rm -rf venv contextvault.db *.log

# Fresh installation
python install_simple.py
```

### Backup and Restore
```bash
# Backup your context
cp contextvault.db contextvault.db.backup

# Restore if needed
cp contextvault.db.backup contextvault.db
```

---

If you're still having issues after following this guide, please create a GitHub issue with all the diagnostic information requested above.
