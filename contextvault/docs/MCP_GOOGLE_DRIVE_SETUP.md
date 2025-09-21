# Google Drive Integration with ContextVault

## 🎯 Complete Setup Guide

This guide shows you how to connect ContextVault to Google Drive so your AI can access your project files, documents, and cloud storage.

## 📋 Prerequisites

1. **Node.js installed** (for MCP servers)
2. **Google Cloud Project** with Drive API enabled
3. **ContextVault running** with MCP support

## 🚀 Step-by-Step Setup

### Step 1: Install Google Drive MCP Server

```bash
# Install the filesystem MCP server (works with mounted Google Drive)
npm install -g @modelcontextprotocol/server-filesystem

# Or install the official Google Drive MCP server
npm install -g @modelcontextprotocol/server-google-drive
```

### Step 2: Set Up Google Drive API

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create a new project** or select existing one
3. **Enable Google Drive API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"
4. **Create OAuth Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the credentials JSON file

### Step 3: Mount Google Drive Locally

#### Option A: Using Google Drive Desktop App
```bash
# Install Google Drive for Desktop
# Download from: https://www.google.com/drive/download/

# Drive will be mounted at:
# macOS: ~/Google Drive
# Windows: C:\Users\[username]\Google Drive
# Linux: ~/Google Drive
```

#### Option B: Using rclone (Advanced)
```bash
# Install rclone
brew install rclone  # macOS
# or
curl https://rclone.org/install.sh | sudo bash  # Linux

# Configure Google Drive
rclone config

# Mount Google Drive
mkdir ~/GoogleDrive
rclone mount gdrive: ~/GoogleDrive --daemon
```

### Step 4: Add MCP Connection to ContextVault

```bash
# Add filesystem MCP connection (for mounted Google Drive)
python -m contextvault.cli mcp add \
  --name "google-drive-files" \
  --endpoint "stdio:filesystem-server" \
  --config '{"root_path": "/Users/aniksahai/Google Drive"}'

# Add Google Drive API connection
python -m contextvault.cli mcp add \
  --name "google-drive-api" \
  --endpoint "stdio:google-drive-server" \
  --config '{"credentials_path": "/path/to/credentials.json"}'
```

### Step 5: Enable for AI Models

```bash
# Enable Google Drive access for your AI models
python -m contextvault.cli mcp enable \
  --connection "google-drive-files" \
  --model "mistral:latest"

python -m contextvault.cli mcp enable \
  --connection "google-drive-api" \
  --model "mistral:latest"
```

### Step 6: Test the Integration

```bash
# Test Google Drive access
curl -X POST http://localhost:11435/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral:latest",
    "prompt": "What files do I have in my Google Drive? Can you help me find my project documents?"
  }'
```

## 🔧 Configuration Options

### Filesystem MCP Server Configuration

```json
{
  "root_path": "/Users/aniksahai/Google Drive",
  "allowed_extensions": [".txt", ".md", ".py", ".js", ".json", ".csv"],
  "max_file_size": "10MB",
  "read_only": false
}
```

### Google Drive API Configuration

```json
{
  "credentials_path": "/path/to/credentials.json",
  "scopes": [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file"
  ],
  "cache_path": "/tmp/google-drive-cache"
}
```

## 📁 Project Integration Workflow

### 1. Organize Your Google Drive

```
Google Drive/
├── Projects/
│   ├── ContextVault/
│   │   ├── docs/
│   │   ├── code/
│   │   └── planning/
│   ├── OtherProject/
│   └── Archive/
├── Research/
├── Personal/
└── Work/
```

### 2. Add Project Context

```bash
# Add project folder context
python -m contextvault.cli context add \
  "My ContextVault project files are stored in Google Drive at Projects/ContextVault/" \
  --type note \
  --tags project,google-drive,filepath

# Add project planning context
python -m contextvault.cli context add \
  "I use Google Drive for project documentation and planning documents" \
  --type preference \
  --tags workflow,google-drive,planning
```

### 3. AI Project Planning

```bash
# Ask AI to help with project planning
curl -X POST http://localhost:11435/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral:latest",
    "prompt": "Help me create a project plan for ContextVault. Check my Google Drive for existing planning documents and build upon them."
  }'
```

## 🔍 Available MCP Commands

### List MCP Connections
```bash
python -m contextvault.cli mcp list
```

### Check MCP Status
```bash
python -m contextvault.cli mcp status
```

### Search Google Drive Content
```bash
python -m contextvault.cli mcp search \
  --connection "google-drive-files" \
  --query "project planning"
```

### View MCP Providers
```bash
python -m contextvault.cli mcp providers
```

## 🚨 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Check file permissions
   ls -la "/Users/aniksahai/Google Drive"
   
   # Fix permissions if needed
   chmod -R 755 "/Users/aniksahai/Google Drive"
   ```

2. **MCP Server Not Starting**
   ```bash
   # Check if MCP server is installed
   which filesystem-server
   
   # Reinstall if needed
   npm install -g @modelcontextprotocol/server-filesystem
   ```

3. **Google Drive Not Mounted**
   ```bash
   # Check if Google Drive is mounted
   mount | grep -i google
   
   # Restart Google Drive app
   # or remount with rclone
   rclone mount gdrive: ~/GoogleDrive --daemon
   ```

4. **API Quota Exceeded**
   - Check Google Cloud Console for quota limits
   - Consider using filesystem MCP instead of API MCP
   - Implement caching for frequently accessed files

## 🎯 Advanced Features

### Automatic Project Detection

ContextVault can automatically detect and index your projects:

```bash
# Add auto-detection context
python -m contextvault.cli context add \
  "ContextVault automatically indexes all files in my Google Drive Projects/ folder for AI access" \
  --type note \
  --tags automation,google-drive,indexing
```

### Cross-Project Context Sharing

```bash
# Enable cross-project learning
python -m contextvault.cli context add \
  "I want AI to learn from all my projects and share insights between them" \
  --type preference \
  --tags cross-project,learning,insights
```

## 📊 Monitoring

### Check Integration Status
```bash
python -m contextvault.cli system status
```

### View MCP Analytics
```bash
python -m contextvault.cli mcp analytics
```

### Monitor Google Drive Usage
```bash
python -m contextvault.cli context list --source "google-drive"
```

## 🎉 Success!

Once set up, your AI will have access to:

- ✅ **All Google Drive files and folders**
- ✅ **Project documents and planning files**
- ✅ **Research papers and notes**
- ✅ **Cross-project insights and patterns**
- ✅ **Automatic context learning from file access**

Your AI now has complete access to your digital project ecosystem! 🚀
