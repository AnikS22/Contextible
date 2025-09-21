#!/bin/bash

echo "🛑 Stopping ContextVault..."

# Stop ContextVault processes
if [ -f .contextvault_server.pid ]; then
    SERVER_PID=$(cat .contextvault_server.pid)
    if kill $SERVER_PID 2>/dev/null; then
        echo "✅ Stopped ContextVault server (PID: $SERVER_PID)"
    fi
    rm .contextvault_server.pid
fi

if [ -f .contextvault_proxy.pid ]; then
    PROXY_PID=$(cat .contextvault_proxy.pid)
    if kill $PROXY_PID 2>/dev/null; then
        echo "✅ Stopped ContextVault proxy (PID: $PROXY_PID)"
    fi
    rm .contextvault_proxy.pid
fi

# Also try to kill any remaining ContextVault processes
pkill -f "contextvault.main" 2>/dev/null && echo "✅ Stopped remaining ContextVault processes"
pkill -f "ollama_proxy.py" 2>/dev/null && echo "✅ Stopped remaining proxy processes"

echo "✅ ContextVault stopped"
echo ""
echo "💡 Your Ollama is back to normal (no persistent memory)"
echo "   Use: ./scripts/start_contextvault.sh to restart"
