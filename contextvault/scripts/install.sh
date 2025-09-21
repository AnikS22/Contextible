#!/bin/bash

# ContextVault One-Click Installer
# This script installs ContextVault with all dependencies and sets up everything needed

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTEXTVAULT_DIR="$HOME/.contextvault"
PYTHON_VERSION="3.11"
REQUIRED_PYTHON_VERSION="3.8"

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ContextVault Installer                    ║"
    echo "║              AI Memory for Local AI Models                   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${YELLOW}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed"
        return 1
    fi
    return 0
}

# Main installation function
install_contextvault() {
    print_header
    
    print_step "Checking system requirements..."
    
    # Check if running on supported OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="Linux"
    else
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    print_success "Detected OS: $OS"
    
    # Check Python installation
    if ! check_command python3; then
        print_error "Python 3 is required but not installed"
        print_info "Please install Python 3.8+ from https://python.org"
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION_CHECK=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYTHON_VERSION_NUM=$(python3 -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')")
    REQUIRED_VERSION_NUM=$(echo $REQUIRED_PYTHON_VERSION | tr -d '.')
    
    if [ "$PYTHON_VERSION_NUM" -lt "$REQUIRED_VERSION_NUM" ]; then
        print_error "Python $PYTHON_VERSION_CHECK found, but $REQUIRED_PYTHON_VERSION+ is required"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION_CHECK is compatible"
    
    # Check for Ollama
    if ! check_command ollama; then
        print_info "Ollama not found. Installing Ollama..."
        install_ollama
    else
        print_success "Ollama is already installed"
    fi
    
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_info "Starting Ollama service..."
        start_ollama
    else
        print_success "Ollama is running"
    fi
    
    # Check for required Ollama models
    check_ollama_models
    
    print_step "Installing ContextVault..."
    
    # Create ContextVault directory
    mkdir -p "$CONTEXTVAULT_DIR"
    cd "$CONTEXTVAULT_DIR"
    
    # Download ContextVault (assuming we're in the source directory)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    CONTEXTVAULT_SOURCE_DIR="$(dirname "$SCRIPT_DIR")"
    
    if [ -d "$CONTEXTVAULT_SOURCE_DIR" ]; then
        print_info "Copying ContextVault from source directory..."
        cp -r "$CONTEXTVAULT_SOURCE_DIR"/* "$CONTEXTVAULT_DIR/"
    else
        print_error "ContextVault source directory not found"
        print_info "Please run this installer from the ContextVault directory"
        exit 1
    fi
    
    # Install Python dependencies
    print_step "Installing Python dependencies..."
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
    
    # Initialize ContextVault
    print_step "Initializing ContextVault..."
    
    export PYTHONPATH="$CONTEXTVAULT_DIR"
    
    # Initialize database
    python -c "
from contextvault.database import init_database
init_database()
print('Database initialized')
"
    
    # Create default permissions
    python -c "
from contextvault.database import get_db_context
from contextvault.models.permissions import Permission

with get_db_context() as db:
    # Check if permissions already exist
    existing = db.query(Permission).filter(Permission.model_id == 'mistral:latest').first()
    
    if not existing:
        permission = Permission(
            model_id='mistral:latest',
            model_name='Mistral (Latest)',
            scope='personal,work,preferences,notes',
            is_active=True
        )
        db.add(permission)
        db.commit()
        print('Default permissions created')
    else:
        print('Permissions already exist')
"
    
    # Add sample context
    python -c "
from contextvault.database import get_db_context
from contextvault.models.context import ContextEntry

with get_db_context() as db:
    # Check if context already exists
    existing_count = db.query(ContextEntry).count()
    
    if existing_count == 0:
        sample_entries = [
            {
                'content': 'I am a software engineer who loves Python and testing. I prefer detailed explanations and want to understand how systems work.',
                'context_type': 'preference',
                'source': 'sample',
                'tags': ['python', 'testing', 'software', 'engineering']
            },
            {
                'content': 'I have two cats named Luna and Pixel. They are playful and love string toys.',
                'context_type': 'note',
                'source': 'sample',
                'tags': ['pets', 'cats', 'luna', 'pixel']
            },
            {
                'content': 'I drive a Tesla Model 3 and live in San Francisco. I enjoy hiking and rock climbing.',
                'context_type': 'note',
                'source': 'sample',
                'tags': ['tesla', 'san francisco', 'hiking', 'rock climbing']
            }
        ]
        
        for entry_data in sample_entries:
            entry = ContextEntry(**entry_data)
            db.add(entry)
        
        db.commit()
        print('Sample context added')
    else:
        print('Context entries already exist')
"
    
    print_success "ContextVault initialized"
    
    # Create startup scripts
    create_startup_scripts
    
    # Run bulletproof test
    print_step "Running system validation..."
    if python scripts/bulletproof_test.py; then
        print_success "System validation passed"
    else
        print_error "System validation failed - please check the output above"
        exit 1
    fi
    
    # Installation complete
    print_success "ContextVault installation complete!"
    print_info ""
    print_info "ContextVault has been installed to: $CONTEXTVAULT_DIR"
    print_info ""
    print_info "To start ContextVault:"
    print_info "  cd $CONTEXTVAULT_DIR"
    print_info "  source venv/bin/activate"
    print_info "  python scripts/ollama_proxy.py"
    print_info ""
    print_info "Or use the convenience script:"
    print_info "  $CONTEXTVAULT_DIR/start_contextvault.sh"
    print_info ""
    print_info "To test ContextVault:"
    print_info "  curl http://localhost:11435/api/generate -X POST -H 'Content-Type: application/json' -d '{\"model\": \"mistral:latest\", \"prompt\": \"What pets do I have?\", \"stream\": false}'"
    print_info ""
    print_info "ContextVault is now ready to give your AI models persistent memory! 🚀"
}

install_ollama() {
    print_info "Installing Ollama..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if check_command brew; then
            brew install ollama
        else
            print_info "Homebrew not found. Please install Ollama manually from https://ollama.ai"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
    
    print_success "Ollama installed"
}

start_ollama() {
    print_info "Starting Ollama service..."
    
    # Start Ollama in background
    nohup ollama serve > /dev/null 2>&1 &
    
    # Wait for Ollama to start
    for i in {1..10}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            print_success "Ollama started"
            return 0
        fi
        sleep 1
    done
    
    print_error "Failed to start Ollama"
    exit 1
}

check_ollama_models() {
    print_step "Checking Ollama models..."
    
    # Get available models
    MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = [model['name'] for model in data.get('models', [])]
    print(' '.join(models))
except:
    print('')
")
    
    if [ -z "$MODELS" ]; then
        print_info "No Ollama models found. Installing mistral:latest..."
        ollama pull mistral:latest
        print_success "mistral:latest installed"
    else
        print_success "Found models: $MODELS"
        
        # Check if mistral:latest is available
        if [[ "$MODELS" == *"mistral:latest"* ]]; then
            print_success "mistral:latest is available"
        else
            print_info "Installing mistral:latest..."
            ollama pull mistral:latest
            print_success "mistral:latest installed"
        fi
    fi
}

create_startup_scripts() {
    print_step "Creating startup scripts..."
    
    # Create start script
    cat > "$CONTEXTVAULT_DIR/start_contextvault.sh" << 'EOF'
#!/bin/bash
# ContextVault Startup Script

cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH="$(pwd)"

echo "🚀 Starting ContextVault..."
python scripts/ollama_proxy.py
EOF
    
    chmod +x "$CONTEXTVAULT_DIR/start_contextvault.sh"
    
    # Create test script
    cat > "$CONTEXTVAULT_DIR/test_contextvault.sh" << 'EOF'
#!/bin/bash
# ContextVault Test Script

cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH="$(pwd)"

echo "🧪 Testing ContextVault..."
python scripts/bulletproof_test.py
EOF
    
    chmod +x "$CONTEXTVAULT_DIR/test_contextvault.sh"
    
    # Create demo script
    cat > "$CONTEXTVAULT_DIR/demo_contextvault.sh" << 'EOF'
#!/bin/bash
# ContextVault Demo Script

cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH="$(pwd)"

echo "🎯 Running ContextVault Demo..."
python scripts/final_demo.py
EOF
    
    chmod +x "$CONTEXTVAULT_DIR/demo_contextvault.sh"
    
    print_success "Startup scripts created"
}

# Main execution
main() {
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        print_error "Please do not run this installer as root"
        exit 1
    fi
    
    # Check if ContextVault is already installed
    if [ -d "$CONTEXTVAULT_DIR" ]; then
        print_info "ContextVault appears to be already installed at $CONTEXTVAULT_DIR"
        read -p "Do you want to reinstall? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Installation cancelled"
            exit 0
        fi
        
        print_info "Removing existing installation..."
        rm -rf "$CONTEXTVAULT_DIR"
    fi
    
    # Run installation
    install_contextvault
    
    print_success "🎉 ContextVault installation complete!"
}

# Run main function
main "$@"
