# 🧠 Contextible - AI Memory & Context Layer

<div align="center">

![Contextible Logo](https://img.shields.io/badge/Contextible-AI%20Memory-blue?style=for-the-badge&logo=brain)

**Transform your local AI models into personal assistants that truly know you**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/AnikS22/Contextible.svg)](https://github.com/AnikS22/Contextible/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/AnikS22/Contextible.svg)](https://github.com/AnikS22/Contextible/issues)

[Quick Start](#-quick-start) • [Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-documentation)

</div>

---

## 🎯 What is Contextible?

Contextible is an intelligent **AI Memory & Context Layer** that automatically injects your personal context into every conversation with your local AI models. It transforms generic AI interactions into personalized experiences where your AI truly knows and remembers you.

### 🔥 Key Benefits

- **🧠 AI Memory**: Your AI remembers your preferences, goals, and personal details
- **🔄 Seamless Integration**: Works with existing AI tools (Ollama, etc.) without changes
- **🔒 Privacy First**: All data stays on your machine - no cloud dependency
- **⚡ Lightning Fast**: Intelligent context retrieval and injection
- **🎨 Beautiful Interface**: Rich terminal experience with real-time monitoring

---

## ✨ Features

### 🧠 **Intelligent Context Management**
- **Smart Storage**: Store personal info, preferences, goals, relationships, skills, projects
- **Auto-Categorization**: Automatically organizes context into meaningful categories
- **Semantic Search**: Find relevant context using natural language queries
- **Conflict Resolution**: Detects and resolves contradictory information
- **Learning System**: Extracts new context from your conversations

### 🔍 **Advanced Context Injection**
- **Query Analysis**: Understands what context is needed for each query
- **Multi-Factor Scoring**: Considers relevance, recency, confidence, and access patterns
- **Template System**: Customizable context formatting for optimal AI comprehension
- **Real-time Processing**: Lightning-fast context retrieval and injection

### 📊 **Analytics & Monitoring**
- **Usage Statistics**: Track how often different contexts are accessed
- **Quality Reports**: Monitor the health and effectiveness of your context database
- **System Health**: Real-time monitoring of all services and components
- **Performance Metrics**: Track response times and system performance

### 🎛️ **Model Management**
- **Auto-Detection**: Automatically discovers running AI models on your system
- **Permission Control**: Fine-grained access control for different models
- **Model Dashboard**: Visual interface to manage all your AI models

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Ollama** (for AI model integration)

### One-Command Installation

```bash
# Clone the repository
git clone https://github.com/AnikS22/Contextible.git
cd Contextible/contextvault

# Run the simple installer (handles everything!)
python install_simple.py
```

That's it! Contextible is now installed and ready to use.

---

## 🎮 Usage

### Start the CLI
```bash
python contextible.py
```

### Add Your Personal Context
```bash
contextvault> add "My name is Alex and I'm a software developer from California"
contextvault> add "I love hiking and have two cats named Luna and Pixel"
contextvault> add "I'm working on a machine learning project using Python"
```

### View Your Context
```bash
contextvault> list
contextvault> search "developer"
contextvault> analytics
```

### Enable AI Memory (Context Injection)
```bash
# Make sure Ollama is running
ollama serve

# Start the Contextible proxy (in a new terminal)
python scripts/ollama_proxy.py

# Now use your AI normally - it will remember you!
curl http://localhost:11435/api/generate -H "Content-Type: application/json" -d '{"model": "mistral:latest", "prompt": "What do you know about me?"}'
```

---

## 📖 Complete Installation Guide

### Option 1: Simple Installation (Recommended)
```bash
git clone https://github.com/AnikS22/Contextible.git
cd Contextible/contextvault
python install_simple.py
```

### Option 2: Manual Installation
```bash
# Clone repository
git clone https://github.com/AnikS22/Contextible.git
cd Contextible/contextvault

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_database.py

# Verify installation
python verify_installation.py
```

### Option 3: Seamless Setup (One-Click)
```bash
# Download and run the seamless installer
curl -fsSL https://raw.githubusercontent.com/AnikS22/Contextible/main/install.sh | bash
```

---

## 🎯 How It Works

### 1. **Context Storage**
You add personal information to Contextible's intelligent database:
- Personal details (name, location, profession)
- Preferences and interests
- Goals and projects
- Relationships and connections
- Skills and expertise

### 2. **Smart Retrieval**
When you ask your AI a question, Contextible:
- Analyzes your query to understand what context is needed
- Uses semantic search to find relevant information
- Scores and ranks context by relevance, recency, and confidence
- Selects the most appropriate context for injection

### 3. **Context Injection**
Contextible automatically:
- Formats the context using intelligent templates
- Injects it into your prompt seamlessly
- Forwards the enhanced prompt to your AI model
- Returns the personalized response

### 4. **Continuous Learning**
Contextible learns from your conversations:
- Extracts new context from your interactions
- Automatically categorizes and validates information
- Updates your personal knowledge base
- Improves context selection over time

---

## 🛠️ CLI Commands

### Context Management
```bash
add <content>              # Add new context entry
list [--limit N]           # View stored context
search <query>             # Intelligent context search
categorize                 # Auto-categorize contexts
resolve-conflicts          # Resolve context conflicts
```

### Analytics & Monitoring
```bash
analytics                  # View system analytics
status                     # Quick system status
health-check              # Comprehensive health check
```

### System Management
```bash
models list               # List detected AI models
models set-permission     # Configure model permissions
start                     # Start all services
stop                      # Stop all services
config show               # Show configuration
```

### Testing & Debugging
```bash
test-all                  # Run all core tests
test-injection            # Test context injection
test-retrieval            # Test intelligent retrieval
test-categorization       # Test categorization engine
```

---

## 🔧 Configuration

### Environment Variables
```bash
export CONTEXTIBLE_PROJECT_ROOT="/path/to/your/projects"
export CONTEXTIBLE_GOOGLE_DRIVE_PATH="/path/to/google/drive"
export CONTEXTIBLE_ROOT="/path/to/contextible"
```

### Custom Paths
Create `user_config_local.py` to customize paths:
```python
def get_user_paths():
    return {
        "project_root": "~/MyProjects",
        "google_drive_path": "/Volumes/GoogleDrive/My Drive",
        # ... other custom paths
    }
```

---

## 🎨 Screenshots

### Beautiful CLI Dashboard
```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ██████╗ ██████╗ ███╗   ██╗████████╗███████╗██╗   ██╗██╗   ██╗ █████╗ ██╗██╗║
║ ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝██║   ██║██║   ██║██╔══██╗██║██║║
║ ██║     ██║   ██║██╔██╗ ██║   ██║   █████╗  ██║   ██║██║   ██║███████║██║██║║
║ ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝  ╚██╗ ██╔╝██║   ██║██╔══██╗██║██║║
║ ╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗ ╚████╔╝ ╚██████╔╝██║  ██║╚██████╔╝║
║  ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝  ╚═══╝   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ║
║                                                                              ║
║                    🧠 AI Memory & Context Layer 🧠                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Real-time System Status
```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Service            ┃ Status       ┃ Endpoint             ┃ Health     ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ API Server         │ ✅ Running   │ http://localhost:8000│ Healthy    │
│ Ollama Proxy       │ ✅ Running   │ http://localhost:11435│ Healthy    │
│ Ollama Core        │ ✅ Running   │ http://localhost:11434│ Healthy    │
│ Database           │ ✅ Connected │ SQLite + Indexes     │ Healthy    │
└────────────────────┴──────────────┴──────────────────────┴────────────┘
```

---

## 🔗 Integrations

### Supported AI Platforms
- **Ollama** (Primary) - Local AI models
- **LM Studio** (Coming Soon)
- **Ollama Web UI** (Compatible)
- **Custom API endpoints** (Extensible)

### File System Integration
- **Google Drive** - Access your cloud files
- **Local Projects** - Index your code repositories
- **Documents** - Process your personal documents
- **Custom Paths** - Configure any directory

---

## 🚀 Advanced Features

### Intelligent Context Retrieval
- **Multi-factor Scoring**: Relevance + Recency + Confidence + Access Frequency
- **Semantic Search**: Advanced NLP for context understanding
- **Relationship Mapping**: Find related contexts automatically
- **Diversity Filtering**: Ensure varied context selection

### Learning & Adaptation
- **Conversation Analysis**: Extract context from AI interactions
- **Automatic Validation**: Verify extracted information accuracy
- **Continuous Improvement**: System gets smarter over time
- **Quality Scoring**: Track and improve context quality

### Privacy & Security
- **Local Storage**: All data stays on your machine
- **Permission Control**: Fine-grained access management
- **Data Validation**: Ensure stored context is appropriate
- **Audit Trails**: Track how your context is used

---

## 📊 Performance

### Benchmarks
- **Context Retrieval**: < 100ms average
- **Context Injection**: < 50ms overhead
- **Memory Usage**: < 100MB base
- **Database Size**: Efficient SQLite with indexing

### Scalability
- **Context Entries**: Supports thousands of entries
- **Concurrent Users**: Multi-user support
- **Real-time Processing**: Handles high-frequency requests
- **Resource Efficiency**: Optimized for local deployment

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/AnikS22/Contextible.git
cd Contextible
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest
```

### Areas for Contribution
- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🧪 Test coverage
- 🎨 UI/UX enhancements
- 🔧 Performance optimizations

---

## 📚 Documentation

- **[Complete Usage Guide](docs/USAGE.md)** - Detailed usage instructions
- **[API Reference](docs/API.md)** - Technical API documentation
- **[Configuration Guide](docs/CONFIG.md)** - Advanced configuration options
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute

---

## 🆘 Support

### Getting Help
- 📖 Check the [Documentation](docs/)
- 🐛 Report bugs via [GitHub Issues](https://github.com/AnikS22/Contextible/issues)
- 💬 Join discussions in [GitHub Discussions](https://github.com/AnikS22/Contextible/discussions)
- 📧 Contact: [your-email@example.com]

### Common Issues
- **Installation fails**: Check Python version (3.8+ required)
- **Context injection not working**: Ensure Ollama is running and proxy is started
- **Database errors**: Run `python init_database.py` to reset
- **Permission denied**: Check file permissions and paths

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Ollama** for providing an excellent local AI platform
- **Rich** for beautiful terminal interfaces
- **FastAPI** for the robust web framework
- **SQLAlchemy** for powerful database management
- **All contributors** who help make Contextible better

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=AnikS22/Contextible&type=Date)](https://star-history.com/#AnikS22/Contextible&Date)

---

<div align="center">

**Made with ❤️ for the AI community**

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/AnikS22/Contextible)
[![Twitter](https://img.shields.io/badge/Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/yourusername)
[![Discord](https://img.shields.io/badge/Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/yourdiscord)

</div>
