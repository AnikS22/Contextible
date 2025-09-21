#!/bin/bash

echo "🚀 ContextVault Simple Installer"
echo "================================"
echo ""
echo "This will install ContextVault in 3 simple steps:"
echo "1. Install Python dependencies"
echo "2. Start ContextVault"
echo "3. Test it works"
echo ""

# Step 1: Install dependencies
echo "📦 Step 1: Installing dependencies..."
pip install -r requirements.txt

# Step 2: Start ContextVault
echo "🚀 Step 2: Starting ContextVault..."
python -m contextvault.main &
sleep 3

# Step 3: Test it works
echo "🧪 Step 3: Testing ContextVault..."
python scripts/simple_test.py

echo ""
echo "✅ ContextVault is now running!"
echo ""
echo "🎯 How to use it:"
echo "• Instead of: curl http://localhost:11434/api/generate ..."
echo "• Use:        curl http://localhost:11435/api/generate ..."
echo ""
echo "📱 Your AI models now have persistent memory!"
echo "They'll remember everything you tell them across all conversations."
