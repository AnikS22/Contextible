# Contextible - AI Memory & Context Layer 🧠

Transform your local AI models into personal assistants that truly know you! Contextible adds persistent memory to any AI model, making every conversation more personalized and relevant.

## ✨ Features

- **🧠 Persistent Memory**: AI remembers who you are, your preferences, and your context
- **🔄 Automatic Learning**: Learns from every conversation to build better context
- **🎯 Seamless Integration**: Works with Ollama, LM Studio, and other AI clients
- **🔒 Privacy First**: All data stays on your machine
- **⚡ Lightning Fast**: Zero latency context injection
- **🎨 Beautiful CLI**: Rich terminal interface for managing your AI memory

## 🚀 Quick Start (30 seconds)

### Prerequisites
- macOS (Intel or Apple Silicon)
- Python 3.8+ 
- Ollama installed ([Download here](https://ollama.ai))

### Installation

```bash
# 1. Clone Contextible
git clone https://github.com/AnikS22/Contextible.git
cd Contextible/contextvault

# 2. One-command installation
python install_simple.py

# 3. Add some context about yourself
python contextible.py
# Type: add "My name is Alex and I'm a Python developer"
# Type: exit

# 4. IMPORTANT: Start the proxy for AI memory (in a NEW terminal)
ollama serve                    # Make sure Ollama is running
python scripts/ollama_proxy.py  # Start Contextible proxy

# 5. Test it! Your AI now remembers you!
# Open Ollama app and ask: "What do you know about me?"
```

**That's it!** Your AI now has persistent memory! 🎉

## ⚠️ IMPORTANT: Starting the Proxy

**Without the proxy, your AI won't remember you!** The proxy is what enables context injection.

### Method 1: Seamless Integration (RECOMMENDED)
```bash
# One command - Ollama Dashboard works normally!
python scripts/seamless_ollama_setup.py

# What this does:
# - Stops Ollama on port 11434
# - Starts Ollama on port 11436  
# - Starts our proxy on port 11434 (Ollama's default)
# - Ollama Dashboard → port 11434 → gets context injection automatically
```

### Method 2: Manual Setup
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Contextible proxy
cd Contextible/contextvault
python scripts/ollama_proxy.py

# Terminal 3: Use curl (Ollama app won't work)
curl http://localhost:11435/api/generate -d '{"model": "mistral:latest", "prompt": "What do you know about me?"}'
```

## 📱 How It Works

1. **You chat normally** with Ollama (no settings needed!)
2. **Contextible intercepts** your conversations via the proxy
3. **Adds your context** to make responses personalized
4. **Learns new facts** from every conversation
5. **Gets smarter** over time

## 🎯 Example

**Without Contextible:**
- You: "What should I eat for lunch?"
- AI: "I don't know your preferences, but here are some general suggestions..."

**With Contextible:**
- You: "What should I eat for lunch?"
- AI: "Since you love pizza and coffee, I'd recommend trying that new pizza place downtown with a coffee on the side!"

## 🛠️ Advanced Usage

### CLI Dashboard
```bash
# Launch the beautiful CLI dashboard
contextible

# Add context manually
contextible add "I'm a software engineer who loves Python"

# View your AI's memory
contextible list

# Search your context
contextible search "work"

# Manage AI models
contextible models list
```

### API Access
```bash
# Use Contextible's API directly
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:latest", "prompt": "What do you know about me?"}'
```

## 🔧 Configuration

### Model Permissions
Control which AI models can access which context:

```bash
# Allow all models access to all context
contextible models set-permission mistral:latest --allow-all

# Restrict access to specific context types
contextible models set-permission qwen3:4b --scope personal,work

# Deny access to specific models
contextible models set-permission codellama:13b --deny-all
```

### Context Types
- `personal` - Personal information, name, location
- `work` - Job, company, professional details  
- `preferences` - Likes, dislikes, preferences
- `notes` - Random facts, observations
- `goals` - Objectives, aspirations
- `relationships` - Family, friends, contacts
- `skills` - Abilities, expertise
- `projects` - Current and past projects

## 📊 Analytics

```bash
# View system analytics
contextible analytics

# Health check
contextible health-check

# Run comprehensive tests
contextible test-all
```

## 🔒 Privacy & Security

- **Local First**: All data stays on your machine
- **No Cloud**: Nothing is sent to external servers
- **Encrypted Storage**: Sensitive data can be encrypted
- **Granular Permissions**: Control exactly what each AI model can access
- **Audit Logs**: Track all context access and modifications

## 🆘 Troubleshooting

### Context Not Working?
1. Check if Contextible is running: `contextible status`
2. Verify Ollama is running: `curl http://localhost:11436/api/tags`
3. Test context injection: `contextible test-all`

### Permission Issues?
```bash
# Reset permissions for a model
contextible models remove-permission mistral:latest
contextible models set-permission mistral:latest --allow-all
```

### Port Conflicts?
```bash
# Check what's using port 11434
lsof -i :11434

# Restart Contextible
./stop_contextible.sh
./setup_seamless.sh
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Ollama](https://ollama.ai/)
- UI by [Rich](https://rich.readthedocs.io/)

---

**Made with ❤️ for the AI community**

*Transform your AI from a forgetful assistant to your personal digital companion!*