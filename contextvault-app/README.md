# ContextVault Desktop Application

A beautiful, user-friendly desktop application that gives your AI models persistent memory through ContextVault.

## 🚀 Features

- **One-Click Setup**: No technical knowledge required
- **Beautiful UI**: Modern, intuitive interface for managing your context
- **System Tray Integration**: Runs quietly in the background
- **Auto-Configuration**: Automatically sets up Ollama proxy
- **Offline Operation**: Works completely offline (except for AI models)
- **Cross-Platform**: Works on macOS, Windows, and Linux

## 📦 Installation

### macOS
1. Download `ContextVault.dmg`
2. Drag to Applications folder
3. Launch from Applications

### Windows
1. Download `ContextVault_Setup.exe`
2. Run the installer
3. Launch from Start Menu

### Linux
1. Download `ContextVault.AppImage`
2. Make executable: `chmod +x ContextVault.AppImage`
3. Run: `./ContextVault.AppImage`

## 🎯 Quick Start

1. **Install Ollama** (if not already installed):
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows - download from https://ollama.ai
   ```

2. **Download a model**:
   ```bash
   ollama run mistral
   ```

3. **Launch ContextVault**:
   - The app will start automatically
   - Look for the ContextVault icon in your system tray

4. **Add your context**:
   - Click "Add Context" in the app
   - Tell ContextVault about yourself, your preferences, and projects
   - Example: "I am a software engineer who loves Python and FastAPI"

5. **Use with Ollama**:
   - Instead of: `curl http://localhost:11434/api/generate`
   - Use: `curl http://localhost:11435/api/generate`
   - Your context will be automatically injected!

## 🖥️ Interface Overview

### Dashboard
- **System Status**: See if ContextVault and Ollama are running
- **Quick Actions**: Start/stop server, refresh status
- **AI Knowledge**: Preview of what AI knows about you
- **Recent Activity**: Track your context usage

### My Context
- **Add Context**: Create new context entries about yourself
- **Manage Entries**: Edit, delete, or organize your context
- **Tags**: Organize context with tags (work, personal, projects, etc.)
- **Types**: Categorize as preferences, notes, events, or files

### Permissions
- **Model Access**: Control which AI models can access your context
- **Privacy Controls**: Fine-grained permission management
- **Audit Logs**: See which models accessed your data

### Settings
- **Ollama Configuration**: Set host, port, and connection settings
- **Server Settings**: Configure ContextVault server and proxy ports
- **Auto-Start**: Choose whether to start automatically with the app

## 🔧 Advanced Configuration

### Custom Ollama Settings
- **Host**: Default `localhost` (change if Ollama runs on another machine)
- **Port**: Default `11434` (change if Ollama uses a different port)
- **Models**: ContextVault works with any Ollama model

### ContextVault Settings
- **Server Port**: Default `8000` (where ContextVault API runs)
- **Proxy Port**: Default `11435` (where ContextVault proxy runs)
- **Auto-Start**: Automatically start ContextVault when app launches

## 🛠️ Development

### Building from Source

1. **Prerequisites**:
   ```bash
   # Install Node.js and npm
   # Install Rust and Cargo
   # Install Tauri CLI
   npm install -g @tauri-apps/cli
   ```

2. **Clone and Build**:
   ```bash
   git clone https://github.com/contextvault/contextvault-app
   cd contextvault-app
   npm install
   npm run tauri dev    # Development mode
   npm run tauri build  # Production build
   ```

3. **Build Scripts**:
   ```bash
   # Use the automated build script
   ./scripts/build_app.sh
   ```

### Project Structure
```
contextvault-app/
├── src/                    # Frontend (HTML/CSS/JS)
├── src-tauri/             # Rust backend
│   ├── src/main.rs        # Tauri app logic
│   ├── resources/         # ContextVault server files
│   └── tauri.conf.json    # Tauri configuration
├── scripts/               # Build and deployment scripts
└── package.json          # Node.js dependencies
```

## 🔒 Privacy & Security

- **Local Storage**: All context data is stored locally on your machine
- **No Internet Required**: ContextVault works completely offline
- **Permission System**: Control which AI models can access your data
- **Encrypted Storage**: Sensitive data is encrypted at rest
- **Audit Logs**: Track all access to your context data

## 🐛 Troubleshooting

### ContextVault Won't Start
1. Check if port 8000 is available
2. Try restarting the application
3. Check the system tray for error notifications

### Ollama Connection Issues
1. Verify Ollama is running: `ollama list`
2. Check Ollama port (default 11434)
3. Test connection: `curl http://localhost:11434/api/tags`

### Context Not Being Used
1. Ensure you have context entries added
2. Check that you're using the proxy port (11435)
3. Verify the AI model has permission to access your context

### Performance Issues
1. Limit the number of context entries (recommended: <100)
2. Use shorter, more focused context entries
3. Restart the ContextVault server periodically

## 📚 Learn More

- **ContextVault Core**: [GitHub Repository](https://github.com/contextvault/contextvault)
- **Documentation**: [ContextVault Docs](https://docs.contextvault.ai)
- **Community**: [Discord Server](https://discord.gg/contextvault)
- **Support**: [GitHub Issues](https://github.com/contextvault/contextvault/issues)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 🙏 Acknowledgments

- Built with [Tauri](https://tauri.app/) for the desktop framework
- Powered by [ContextVault](https://github.com/contextvault/contextvault) for AI memory
- Integrates with [Ollama](https://ollama.ai/) for local AI models

---

**Made with ❤️ by the ContextVault Team**
