# 📖 Complete Usage Guide

This guide covers everything you need to know about using Contextible effectively.

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/AnikS22/Contextible.git
cd Contextible/contextvault
python install_simple.py
```

### 2. First Run
```bash
python contextible.py
```

### 3. Add Your Context
```bash
contextvault> add "My name is Alex and I'm a software developer"
contextvault> add "I love hiking and photography"
contextvault> add "I'm working on a Python project"
```

### 4. Enable AI Memory
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Contextible proxy
python scripts/ollama_proxy.py

# Terminal 3: Use your AI with memory!
curl http://localhost:11435/api/generate -H "Content-Type: application/json" -d '{"model": "mistral:latest", "prompt": "What do you know about me?"}'
```

## 🧠 Context Management

### Adding Context

#### Basic Addition
```bash
contextvault> add "I am a software engineer who specializes in Python and machine learning"
```

#### Structured Context
```bash
contextvault> add "Personal: My name is Sarah, I live in Seattle, and I have two dogs"
contextvault> add "Professional: I work at Microsoft as a Senior Software Engineer"
contextvault> add "Interests: I love rock climbing, cooking Italian food, and reading sci-fi novels"
```

#### Project Context
```bash
contextvault> add "Project: I'm building a recommendation system using TensorFlow and Python"
contextvault> add "Goal: I want to learn more about deep learning and neural networks"
```

### Viewing Context

#### List All Context
```bash
contextvault> list
```

#### List with Limit
```bash
contextvault> list --limit 10
```

#### Search Context
```bash
contextvault> search "software engineer"
contextvault> search "Python"
contextvault> search "machine learning"
```

### Context Categories

Contextible automatically categorizes your context into:

- **Personal Info**: Name, location, basic details
- **Preferences**: Likes, dislikes, interests
- **Goals**: Objectives, aspirations, targets
- **Relationships**: Family, friends, colleagues
- **Skills**: Technical abilities, expertise
- **Work**: Job, company, role
- **Projects**: Current and past projects
- **Technical**: Programming languages, tools, frameworks

## 🔍 Advanced Search

### Semantic Search
Contextible uses intelligent search that understands meaning:

```bash
contextvault> search "programming"
# Finds: "Python developer", "software engineer", "coding", etc.

contextvault> search "hobbies"
# Finds: "rock climbing", "photography", "cooking", etc.
```

### Search Tips
- Use natural language: "What do I know about machine learning?"
- Be specific: "Python projects" vs "programming"
- Use synonyms: "job" will find "work", "career", "profession"

## 📊 Analytics & Monitoring

### View Analytics
```bash
contextvault> analytics
```

Shows:
- Total context entries
- Recent activity
- Context by type
- Usage statistics
- Quality metrics

### System Status
```bash
contextvault> status
```

Displays:
- Service health
- Database status
- Context injection status
- Performance metrics

### Health Check
```bash
contextvault> health-check
```

Comprehensive system diagnostics:
- All service statuses
- Database connectivity
- Performance benchmarks
- Error logs

## 🤖 AI Integration

### Ollama Integration

#### Start Ollama
```bash
ollama serve
```

#### Start Contextible Proxy
```bash
python scripts/ollama_proxy.py
```

#### Use with Ollama
```bash
# Direct API calls
curl http://localhost:11435/api/generate -H "Content-Type: application/json" -d '{"model": "mistral:latest", "prompt": "What do you know about me?"}'

# Ollama CLI
ollama run mistral:latest "What are my current projects?"

# Ollama Web UI
# Just use the web interface normally - context injection happens automatically
```

### Model Management

#### List Detected Models
```bash
contextvault> models list
```

#### Set Model Permissions
```bash
contextvault> models set-permission mistral:latest --allow personal --allow professional
```

#### Remove Model Permissions
```bash
contextvault> models remove-permission mistral:latest
```

## 🔧 Configuration

### Environment Variables

Set these in your shell profile (`~/.zshrc`, `~/.bashrc`):

```bash
# Project paths
export CONTEXTIBLE_PROJECT_ROOT="/Users/yourname/Projects"
export CONTEXTIBLE_GOOGLE_DRIVE_PATH="/Volumes/GoogleDrive/My Drive"

# Contextible paths
export CONTEXTIBLE_ROOT="/Users/yourname/Contextible"
export CONTEXTIBLE_CONTEXTVAULT_ROOT="/Users/yourname/Contextible/contextvault"

# Other paths
export CONTEXTIBLE_DESKTOP_PATH="/Users/yourname/Desktop"
export CONTEXTIBLE_DOCUMENTS_PATH="/Users/yourname/Documents"
export CONTEXTIBLE_DOWNLOADS_PATH="/Users/yourname/Downloads"
export CONTEXTIBLE_DEV_ROOT="/Users/yourname/Development"
```

### Custom Configuration File

Create `user_config_local.py`:

```python
import os

def get_user_paths():
    return {
        "project_root": os.path.expanduser("~/MyCustomProjects"),
        "google_drive_path": "/Volumes/GoogleDrive/My Drive",
        "contextible_root": "~/MyCustomContextible",
        "desktop_path": "~/Desktop",
        "documents_path": "~/Documents",
        "downloads_path": "~/Downloads",
        "dev_root": "~/Code",
    }

def get_custom_path(path_type: str, default: str = None):
    paths = get_user_paths()
    return paths.get(path_type, default or "")
```

## 🧪 Testing & Debugging

### Run All Tests
```bash
contextvault> test-all
```

### Individual Tests
```bash
contextvault> test-injection      # Test context injection
contextvault> test-retrieval      # Test intelligent retrieval
contextvault> test-categorization # Test categorization engine
contextvault> test-conflicts      # Test conflict resolution
```

### Debug Commands
```bash
contextvault> health-check        # Comprehensive diagnostics
contextvault> config show         # Show current configuration
contextvault> status              # Quick system status
```

## 💡 Best Practices

### Context Quality

#### Good Context Examples
```bash
# Specific and detailed
contextvault> add "I'm a Senior Python Developer at Google, specializing in machine learning and data pipelines"

# Personal and relevant
contextvault> add "I have a fear of heights but love hiking in the mountains"

# Project-specific
contextvault> add "Currently working on a recommendation system using TensorFlow and PostgreSQL"
```

#### Poor Context Examples
```bash
# Too vague
contextvault> add "I like programming"

# Too generic
contextvault> add "I work in tech"

# Not useful
contextvault> add "Today is Tuesday"
```

### Context Organization

#### Use Categories
```bash
# Personal information
contextvault> add "Personal: My name is John, I'm 28, and I live in San Francisco"

# Professional details
contextvault> add "Professional: I work as a DevOps Engineer at Netflix, focusing on Kubernetes and AWS"

# Interests and hobbies
contextvault> add "Interests: I love playing guitar, reading science fiction, and brewing craft beer"

# Current projects
contextvault> add "Project: Building a CI/CD pipeline for microservices using Jenkins and Docker"
```

#### Regular Updates
```bash
# Update outdated information
contextvault> add "Updated: I've moved from Seattle to Portland for my new job at Intel"

# Add new skills
contextvault> add "Skills: Recently learned Rust and am building a web server with Actix"
```

### Privacy & Security

#### Sensitive Information
- Avoid storing passwords, API keys, or financial information
- Be careful with personal addresses and phone numbers
- Consider what you'd be comfortable sharing with an AI

#### Data Management
```bash
# Regular cleanup
contextvault> list  # Review your context
contextvault> search "old"  # Find outdated information

# Remove sensitive context
# (Note: Contextible doesn't have a delete command yet - coming soon!)
```

## 🚨 Troubleshooting

### Common Issues

#### Installation Problems
```bash
# Python version too old
python --version  # Should be 3.8+

# Missing dependencies
pip install -r requirements.txt

# Database issues
python init_database.py
```

#### Context Injection Not Working
```bash
# Check if proxy is running
contextvault> status

# Restart proxy
python scripts/ollama_proxy.py

# Check Ollama
ollama list
ollama serve
```

#### Performance Issues
```bash
# Check system health
contextvault> health-check

# Review analytics
contextvault> analytics

# Clear old context (coming soon)
```

### Getting Help

1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Search [GitHub Issues](https://github.com/AnikS22/Contextible/issues)
3. Join [GitHub Discussions](https://github.com/AnikS22/Contextible/discussions)
4. Create a new issue with:
   - Your OS and Python version
   - Error messages
   - Steps to reproduce

## 🔮 Advanced Usage

### Custom Templates
Create custom context injection templates for different types of queries.

### API Integration
Use Contextible's API to integrate with other tools and workflows.

### Batch Operations
Import context from files, databases, or other systems.

### Multi-User Support
Set up Contextible for multiple users with separate context databases.

---

For more advanced topics, see the [API Reference](API.md) and [Configuration Guide](CONFIG.md).
