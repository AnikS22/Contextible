#!/bin/bash
# Contextible Installation Script

echo "🚀 Installing Contextible..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTEXTIBLE_DIR="$SCRIPT_DIR"

# Create a symlink to make contextible available globally
echo "📁 Creating global symlink..."
sudo ln -sf "$CONTEXTIBLE_DIR/contextible.py" /usr/local/bin/contextible

# Make the script executable
chmod +x "$CONTEXTIBLE_DIR/contextible.py"

echo "✅ Contextible installed successfully!"
echo ""
echo "🎯 You can now use 'contextible' from anywhere:"
echo "   contextible                    # Launch the dashboard"
echo "   contextible models list        # List AI models"
echo "   contextible add \"your context\"  # Add context"
echo ""
echo "🔧 If you need to uninstall:"
echo "   sudo rm /usr/local/bin/contextible"
