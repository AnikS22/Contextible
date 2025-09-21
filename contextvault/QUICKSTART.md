# ContextVault Quick Start Guide

Welcome to ContextVault! This guide will get you up and running in minutes.

## 🚀 Installation & Setup

### 1. Install Dependencies

```bash
# Install the package in development mode
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Initialize the database and create default permissions
python scripts/init_db.py

# Or use the CLI
python -m contextvault.cli.main init
```

### 3. Start the API Server

```bash
# Start the main API server
python -m contextvault.cli.main serve

# Or directly with uvicorn
uvicorn contextvault.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## 📝 Basic Usage

### Adding Context via CLI

```bash
# Add your first context entry
python -m contextvault.cli.main context add "I prefer dark mode interfaces" --type preference --tags ui,preferences

# Add a coding note
python -m contextvault.cli.main context add "Use async/await for I/O operations in Python" --type note --tags coding,python

# Add a personal preference
python -m contextvault.cli.main context add "I'm working on a FastAPI project called ContextVault" --type text --tags project,work
```

### Setting Up Model Permissions

```bash
# Give llama2 access to preferences and notes
python -m contextvault.cli.main permissions add llama2 --scope "preferences,notes" --name "Llama 2"

# Give codellama broader access for coding help
python -m contextvault.cli.main permissions add codellama --scope "preferences,notes,text" --name "Code Llama" --max-entries 100

# Create a restricted permission
python -m contextvault.cli.main permissions add mistral --scope "preferences" --max-entries 25 --max-age-days 14
```

### Using the API

```bash
# Get context entries (with permission filtering)
curl "http://localhost:8000/api/context/?model=llama2&limit=10"

# Add context via API
curl -X POST "http://localhost:8000/api/context/" \
  -H "Content-Type: application/json" \
  -d '{"content": "I love Python programming", "context_type": "preference", "tags": ["coding", "python"]}'

# Check permissions
curl -X POST "http://localhost:8000/api/permissions/check" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "llama2", "scope": "preferences"}'
```

## 🔗 Ollama Integration

### 1. Start the Ollama Proxy

```bash
# Make sure Ollama is running on port 11434
ollama serve

# Start the ContextVault proxy on port 11435
python scripts/ollama_proxy.py

# Or via CLI
python -m contextvault.cli.main proxy
```

### 2. Use Ollama with Context Injection

Instead of calling Ollama directly:
```bash
# OLD: Direct Ollama call
curl http://localhost:11434/api/generate \
  -d '{"model": "llama2", "prompt": "What are my preferences?"}'
```

Use the ContextVault proxy:
```bash
# NEW: With automatic context injection
curl http://localhost:11435/api/generate \
  -d '{"model": "llama2", "prompt": "What are my preferences?"}'
```

The proxy will automatically:
1. Check if `llama2` has permissions
2. Find relevant context based on your prompt
3. Inject the context into your prompt
4. Forward the enhanced request to Ollama
5. Return the response with your personal context included

## 📊 Monitoring & Management

### View System Status

```bash
# Check overall system status
python -m contextvault.cli.main status

# Get context statistics
python -m contextvault.cli.main context stats

# List all models and their permissions
python -m contextvault.cli.main permissions models
```

### Data Management

```bash
# Export your data
python -m contextvault.cli.main export backup.json

# Import data
python -m contextvault.cli.main import backup.json

# Search your context
python -m contextvault.cli.main context search "python programming"

# List recent entries
python -m contextvault.cli.main context list --limit 10
```

## 🔧 Configuration

Edit `.env` file to customize:

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env
```

Key settings:
- `DATABASE_URL`: Database location
- `API_PORT`: API server port
- `OLLAMA_PORT`: Ollama server port  
- `PROXY_PORT`: Proxy server port
- `MAX_CONTEXT_ENTRIES`: Max entries per query
- `MAX_CONTEXT_LENGTH`: Max characters per context

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=contextvault --cov-report=html
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔍 Example Workflow

Here's a complete example workflow:

```bash
# 1. Initialize
python -m contextvault.cli.main init

# 2. Add some personal context
python -m contextvault.cli.main context add "I'm a Python developer working on AI projects" --type text --tags work,python,ai
python -m contextvault.cli.main context add "I prefer using PyCharm as my IDE" --type preference --tags tools,ide
python -m contextvault.cli.main context add "I'm learning about vector databases and embeddings" --type note --tags learning,ai,databases

# 3. Set up model permissions
python -m contextvault.cli.main permissions add llama2 --scope "preferences,notes,text" --max-entries 50

# 4. Start servers
python -m contextvault.cli.main serve &  # Start API in background
python -m contextvault.cli.main proxy &  # Start proxy in background

# 5. Test context injection
curl http://localhost:11435/api/generate \
  -d '{"model": "llama2", "prompt": "What IDE should I use for Python development?"}' \
  -H "Content-Type: application/json"

# The response will include context about your PyCharm preference!
```

## 🆘 Troubleshooting

### Common Issues

1. **Database errors**: Run `python -m contextvault.cli.main init`
2. **Port conflicts**: Check `.env` and adjust ports
3. **Ollama not found**: Ensure Ollama is running on port 11434
4. **Permission denied**: Check file permissions with `chmod +x scripts/*.py`

### Getting Help

```bash
# CLI help
python -m contextvault.cli.main --help
python -m contextvault.cli.main context --help
python -m contextvault.cli.main permissions --help

# Check system status
python -m contextvault.cli.main status

# View logs (if configured)
tail -f contextvault.log
```

## 🎉 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Add more context**: Use the CLI or API to add your preferences, notes, and information
3. **Configure permissions**: Set up fine-grained access control for different models
4. **Try different models**: Test with various Ollama models
5. **Integrate with your workflow**: Use the API in your applications

Happy context vaulting! 🚀
