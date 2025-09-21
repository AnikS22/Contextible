#!/bin/bash

# ContextVault Desktop App Build Script
# This script builds the Tauri desktop application with embedded ContextVault server

set -e

echo "🚀 Building ContextVault Desktop Application"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="ContextVault"
VERSION="1.0.0"
BUILD_DIR="dist"
CONTEXTVAULT_DIR="../contextvault"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Please run this script from the contextvault-app directory${NC}"
    exit 1
fi

# Check if ContextVault source exists
if [ ! -d "$CONTEXTVAULT_DIR" ]; then
    echo -e "${RED}Error: ContextVault source directory not found at $CONTEXTVAULT_DIR${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Build Configuration:${NC}"
echo "  App Name: $APP_NAME"
echo "  Version: $VERSION"
echo "  Build Directory: $BUILD_DIR"
echo "  ContextVault Source: $CONTEXTVAULT_DIR"
echo ""

# Step 1: Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
npm install

# Step 2: Prepare ContextVault server
echo -e "${YELLOW}🔧 Preparing ContextVault server...${NC}"

# Create server directory in Tauri resources
mkdir -p src-tauri/resources/contextvault-server

# Copy ContextVault source
cp -r $CONTEXTVAULT_DIR/* src-tauri/resources/contextvault-server/

# Create a simple server startup script
cat > src-tauri/resources/contextvault-server/start_server.py << 'EOF'
#!/usr/bin/env python3
"""
ContextVault Server Startup Script for Desktop App
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Start the ContextVault server."""
    try:
        # Import and start the server
        from contextvault.main import app
        import uvicorn
        
        print("Starting ContextVault server...")
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x src-tauri/resources/contextvault-server/start_server.py

# Create requirements.txt for the embedded server
cat > src-tauri/resources/contextvault-server/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.13.0
httpx==0.25.2
aiofiles==23.2.0
click==8.1.7
rich==13.7.0
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
orjson==3.9.10
cryptography==41.0.8
passlib[bcrypt]==1.7.4
uuid==1.30
structlog==23.2.0
sentence-transformers==2.2.2
numpy==1.24.3
torch==2.1.0
transformers==4.35.0
scikit-learn==1.3.0
EOF

# Step 3: Create Python environment setup script
cat > src-tauri/resources/contextvault-server/setup_python_env.py << 'EOF'
#!/usr/bin/env python3
"""
Setup Python environment for ContextVault desktop app
"""

import subprocess
import sys
import os
from pathlib import Path

def setup_environment():
    """Set up Python environment for the desktop app."""
    try:
        # Install requirements
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("Python environment setup completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to setup Python environment: {e}")
        return False

if __name__ == "__main__":
    setup_environment()
EOF

# Step 4: Create app icons (placeholder)
echo -e "${YELLOW}🎨 Creating app icons...${NC}"
mkdir -p src-tauri/icons

# Create placeholder icons (in a real build, these would be proper icon files)
touch src-tauri/icons/32x32.png
touch src-tauri/icons/128x128.png
touch src-tauri/icons/128x128@2x.png
touch src-tauri/icons/icon.icns
touch src-tauri/icons/icon.ico
touch src-tauri/icons/icon.png

# Step 5: Update Tauri configuration for production
echo -e "${YELLOW}⚙️  Configuring Tauri for production...${NC}"

# Create production Tauri config
cat > src-tauri/tauri.conf.json << 'EOF'
{
  "build": {
    "beforeDevCommand": "",
    "beforeBuildCommand": "",
    "devPath": "../src",
    "distDir": "../public",
    "withGlobalTauri": false
  },
  "package": {
    "productName": "ContextVault",
    "version": "1.0.0"
  },
  "tauri": {
    "allowlist": {
      "all": false,
      "shell": {
        "all": false,
        "open": true
      },
      "dialog": {
        "all": false,
        "open": true,
        "save": true
      },
      "fs": {
        "all": true,
        "readFile": true,
        "writeFile": true,
        "readDir": true,
        "copyFile": true,
        "createDir": true,
        "removeDir": true,
        "removeFile": true,
        "renameFile": true,
        "exists": true
      },
      "path": {
        "all": true
      },
      "process": {
        "all": true,
        "exit": true,
        "relaunch": true
      },
      "notification": {
        "all": true
      },
      "system": {
        "all": false,
        "os": true,
        "version": true
      },
      "window": {
        "all": false,
        "close": true,
        "hide": true,
        "show": true,
        "maximize": true,
        "minimize": true,
        "unmaximize": true,
        "unminimize": true,
        "startDragging": true,
        "print": true
      }
    },
    "bundle": {
      "active": true,
      "targets": "all",
      "identifier": "com.contextvault.app",
      "icon": [
        "icons/32x32.png",
        "icons/128x128.png",
        "icons/128x128@2x.png",
        "icons/icon.icns",
        "icons/icon.ico"
      ],
      "resources": [
        "contextvault-server/**/*"
      ],
      "externalBin": [],
      "copyright": "Copyright © 2024 ContextVault Team",
      "category": "Productivity",
      "shortDescription": "Personal AI Memory Assistant",
      "longDescription": "ContextVault gives your AI models persistent memory, making responses more personalized and helpful.",
      "macOS": {
        "entitlements": null,
        "exceptionDomain": "",
        "frameworks": [],
        "providerShortName": null,
        "signingIdentity": null,
        "minimumSystemVersion": "10.13"
      },
      "windows": {
        "certificateThumbprint": null,
        "digestAlgorithm": "sha256",
        "timestampUrl": ""
      }
    },
    "security": {
      "csp": null
    },
    "systemTray": {
      "iconPath": "icons/icon.png",
      "iconAsTemplate": true,
      "menuOnLeftClick": false
    },
    "updater": {
      "active": false
    },
    "windows": [
      {
        "fullscreen": false,
        "resizable": true,
        "title": "ContextVault",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600
      }
    ]
  }
}
EOF

# Step 6: Build the application
echo -e "${YELLOW}🔨 Building Tauri application...${NC}"

# Determine target platform
PLATFORM=$(uname -s)
if [[ "$PLATFORM" == "Darwin" ]]; then
    TARGET="x86_64-apple-darwin"
    echo -e "${BLUE}Building for macOS...${NC}"
elif [[ "$PLATFORM" == "Linux" ]]; then
    TARGET="x86_64-unknown-linux-gnu"
    echo -e "${BLUE}Building for Linux...${NC}"
else
    TARGET="x86_64-pc-windows-msvc"
    echo -e "${BLUE}Building for Windows...${NC}"
fi

# Build the app
npm run tauri build -- --target $TARGET

# Step 7: Post-build setup
echo -e "${YELLOW}📋 Post-build setup...${NC}"

# Create installer scripts
mkdir -p $BUILD_DIR

# macOS installer script
cat > $BUILD_DIR/install_macos.sh << 'EOF'
#!/bin/bash
echo "Installing ContextVault..."
echo "1. Drag ContextVault.app to Applications folder"
echo "2. Run the app from Applications"
echo "3. The app will automatically start ContextVault server"
echo ""
echo "First time setup:"
echo "- The app will download Python dependencies (one-time setup)"
echo "- Make sure Ollama is installed and running"
echo "- ContextVault will create a proxy on port 11435"
EOF

# Windows installer script
cat > $BUILD_DIR/install_windows.bat << 'EOF'
@echo off
echo Installing ContextVault...
echo 1. Run ContextVault_1.0.0_x64_en-US.msi
echo 2. Follow the installation wizard
echo 3. Launch ContextVault from Start Menu
echo.
echo First time setup:
echo - The app will download Python dependencies (one-time setup)
echo - Make sure Ollama is installed and running
echo - ContextVault will create a proxy on port 11435
pause
EOF

chmod +x $BUILD_DIR/install_macos.sh

# Create README for users
cat > $BUILD_DIR/README.txt << 'EOF'
ContextVault Desktop Application
===============================

Welcome to ContextVault! This desktop application gives your AI models persistent memory.

Quick Start:
1. Install Ollama from https://ollama.ai
2. Download and run a model: ollama run mistral
3. Launch ContextVault
4. Add some context about yourself
5. Use Ollama with ContextVault proxy: http://localhost:11435

Features:
- Personal AI memory that persists across conversations
- Simple web interface for managing your context
- Automatic Ollama proxy configuration
- System tray integration
- Offline operation (no internet required)

Usage:
- Add context entries about your preferences, projects, and background
- ContextVault automatically injects relevant context into AI responses
- Manage permissions to control which AI models can access your data

Support:
- Check the dashboard for system status
- Use the settings panel to configure Ollama connection
- View your context entries in the "My Context" section

System Requirements:
- macOS 10.13+, Windows 10+, or Linux
- Python 3.8+ (automatically managed)
- Ollama installed and running
- 100MB free disk space

For more information, visit: https://github.com/contextvault/contextvault
EOF

# Step 8: Create distribution packages
echo -e "${YELLOW}📦 Creating distribution packages...${NC}"

if [[ "$PLATFORM" == "Darwin" ]]; then
    # Create macOS DMG (if dmgbuild is available)
    if command -v dmgbuild &> /dev/null; then
        echo -e "${BLUE}Creating macOS DMG...${NC}"
        dmgbuild -s <(echo 'format = "UDBZ"') "$APP_NAME" "$BUILD_DIR/${APP_NAME}.dmg"
    else
        echo -e "${YELLOW}Note: dmgbuild not found. Install with: pip install dmgbuild${NC}"
    fi
fi

# Step 9: Summary
echo ""
echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo ""
echo -e "${BLUE}📁 Build artifacts:${NC}"
echo "  - Application bundle: src-tauri/target/$TARGET/release/bundle/"
echo "  - Installer scripts: $BUILD_DIR/"
echo "  - Documentation: $BUILD_DIR/README.txt"
echo ""
echo -e "${BLUE}🚀 Next steps:${NC}"
echo "  1. Test the application bundle"
echo "  2. Create proper app icons"
echo "  3. Sign the application (for distribution)"
echo "  4. Upload to distribution channels"
echo ""
echo -e "${GREEN}ContextVault Desktop App is ready! 🎉${NC}"
