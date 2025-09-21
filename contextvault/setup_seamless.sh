#!/bin/bash

echo "🚀 Contextible - One-Click Seamless Setup"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "scripts/ollama_proxy.py" ]; then
    echo -e "${RED}❌ Please run this from the contextvault directory${NC}"
    exit 1
fi

# Stop any existing Ollama processes
echo -e "${YELLOW}⏸️  Stopping existing Ollama processes...${NC}"
pkill -f ollama || true
pkill -f "ollama_proxy" || true
sleep 2

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}❌ Ollama is not installed. Please install Ollama first:${NC}"
    echo "   curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
pip3 install -r requirements.txt

# Start Ollama on port 11436 (backup port)
echo -e "${YELLOW}🔄 Starting Ollama on port 11436...${NC}"
ollama serve --port 11436 &
OLLAMA_PID=$!
sleep 3

# Verify Ollama is running
if ! curl -s http://localhost:11436/api/tags > /dev/null; then
    echo -e "${RED}❌ Failed to start Ollama on port 11436${NC}"
    exit 1
fi

# Start ContextVault on port 11434 (Ollama's default port)
echo -e "${YELLOW}🎯 Starting ContextVault on Ollama's default port (11434)...${NC}"
python3 scripts/ollama_proxy.py --port 11434 --upstream-port 11436 &
CONTEXTVULT_PID=$!
sleep 3

# Verify ContextVault is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "${RED}❌ Failed to start ContextVault on port 11434${NC}"
    kill $OLLAMA_PID 2>/dev/null
    exit 1
fi

# Create stop script
cat > stop_contextible.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Contextible..."
pkill -f ollama
pkill -f "ollama_proxy"
echo "✅ Contextible stopped"
EOF
chmod +x stop_contextible.sh

# Save PIDs for cleanup
echo $OLLAMA_PID > .ollama.pid
echo $CONTEXTVULT_PID > .contextvault.pid

echo ""
echo -e "${GREEN}✅ SETUP COMPLETE!${NC}"
echo ""
echo -e "${BLUE}🎉 Contextible is now running seamlessly!${NC}"
echo "   • Ollama app works normally (no settings needed)"
echo "   • All AI clients work normally"
echo "   • Context injection happens automatically"
echo "   • AI learns from every conversation"
echo ""
echo -e "${YELLOW}🧪 Test it:${NC}"
echo "   1. Open Ollama app"
echo "   2. Ask: 'What do you know about me?'"
echo "   3. Watch it remember everything!"
echo ""
echo -e "${YELLOW}🛑 To stop: Run './stop_contextible.sh'${NC}"
echo ""
echo -e "${GREEN}🧠 Your AI now has persistent memory!${NC}"
