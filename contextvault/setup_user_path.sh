#!/bin/bash
# Contextible User PATH Setup Script

echo "🚀 Setting up Contextible in your user PATH..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTEXTIBLE_DIR="$SCRIPT_DIR"

# Add to ~/.zshrc
echo ""
echo "📝 Adding Contextible to your ~/.zshrc file..."
echo "export PATH=\"$CONTEXTIBLE_DIR:\$PATH\"" >> ~/.zshrc

echo "✅ Contextible added to your PATH!"
echo ""
echo "🔄 Please run this command to reload your shell:"
echo "   source ~/.zshrc"
echo ""
echo "🎯 After that, you can use 'contextible' from anywhere:"
echo "   contextible                    # Launch the dashboard"
echo "   contextible models list        # List AI models"
echo "   contextible add \"your context\"  # Add context"
echo ""
echo "🔧 To remove from PATH later, edit ~/.zshrc and remove the line:"
echo "   export PATH=\"$CONTEXTIBLE_DIR:\$PATH\""
