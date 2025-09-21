#!/bin/bash

echo "🚀 Contextible - AI Memory & Context Layer"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "✅ Ollama installed!"
else
    echo "✅ Ollama already installed"
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3 first:"
    echo "   https://www.python.org/downloads/"
    exit 1
fi

# Clone the repository if not already present
if [ ! -d "contextible" ]; then
    echo "📥 Cloning Contextible..."
    git clone https://github.com/AnikS22/Contextible.git
fi

cd contextible

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Run setup
echo "⚙️  Setting up Contextible..."
./setup_seamless.sh

echo ""
echo -e "${GREEN}🎉 Installation complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Open Ollama app"
echo "2. Ask: 'What do you know about me?'"
echo "3. Start chatting with your AI that has memory!"
echo ""
echo -e "${YELLOW}Need help? Run: contextible help${NC}"