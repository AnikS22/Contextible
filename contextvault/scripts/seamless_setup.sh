#!/bin/bash

echo "🚀 Setting up Contextible for seamless Ollama integration..."

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not running. Please start Ollama first."
    exit 1
fi

# Stop Ollama temporarily
echo "⏸️  Stopping Ollama temporarily..."
pkill -f ollama

# Wait a moment
sleep 2

# Start Ollama on port 11436 instead of 11434
echo "🔄 Starting Ollama on port 11436..."
ollama serve --port 11436 &
sleep 3

# Start ContextVault on port 11434 (Ollama's default port)
echo "🎯 Starting ContextVault on port 11434 (Ollama's default)..."
cd "$(dirname "$0")"
python scripts/ollama_proxy.py --port 11434 --upstream-port 11436 &
sleep 3

echo "✅ Setup complete!"
echo ""
echo "🎉 Now any Ollama client will automatically use ContextVault!"
echo "   - Ollama app: Works normally (no settings needed)"
echo "   - Ollama Web UI: Works normally"
echo "   - Any AI client: Works normally"
echo ""
echo "🧠 Your AI now has persistent memory!"
echo ""
echo "To test: Open Ollama app and ask 'What do you know about me?'"
