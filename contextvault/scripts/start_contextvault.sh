#!/bin/bash

echo "🚀 ContextVault - Easy Setup"
echo "============================"
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama is not running on port 11434"
    echo "Please start Ollama first:"
    echo "  • Open Ollama app, or"
    echo "  • Run: ollama serve"
    echo ""
    exit 1
fi

echo "✅ Ollama is running on port 11434"

# Check if ContextVault is already running
if curl -s http://localhost:11435/health > /dev/null 2>&1; then
    echo "✅ ContextVault is already running on port 11435"
    echo ""
    echo "🎯 Your Ollama is now enhanced with persistent memory!"
    echo ""
    echo "📱 To use ContextVault:"
    echo "   Change your Ollama client from:"
    echo "   ❌ http://localhost:11434"
    echo "   ✅ http://localhost:11435"
    echo ""
    echo "🧪 Test it:"
    echo "   curl http://localhost:11435/api/generate -d '{\"model\": \"mistral:latest\", \"prompt\": \"What do you know about me?\"}'"
    echo ""
    exit 0
fi

echo "🚀 Starting ContextVault..."

# Start the FastAPI server
echo "   Starting ContextVault server..."
python -m contextvault.main &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Start the proxy
echo "   Starting ContextVault proxy..."
python scripts/ollama_proxy.py &
PROXY_PID=$!

# Wait for proxy to start
sleep 3

# Test if everything is working
if curl -s http://localhost:11435/health > /dev/null 2>&1; then
    echo ""
    echo "✅ ContextVault is now running!"
    echo ""
    echo "🎯 Your Ollama is enhanced with persistent memory!"
    echo ""
    echo "📱 To use ContextVault:"
    echo "   Change your Ollama client from:"
    echo "   ❌ http://localhost:11434"
    echo "   ✅ http://localhost:11435"
    echo ""
    echo "🧪 Test it:"
    echo "   curl http://localhost:11435/api/generate -d '{\"model\": \"mistral:latest\", \"prompt\": \"What do you know about me?\"}'"
    echo ""
    echo "📊 Monitor ContextVault:"
    echo "   python scripts/monitor_contextvault.py"
    echo ""
    echo "🛑 To stop ContextVault:"
    echo "   kill $SERVER_PID $PROXY_PID"
    echo ""
    
    # Save PIDs for easy stopping
    echo $SERVER_PID > .contextvault_server.pid
    echo $PROXY_PID > .contextvault_proxy.pid
    
else
    echo "❌ Failed to start ContextVault"
    kill $SERVER_PID $PROXY_PID 2>/dev/null
    exit 1
fi
