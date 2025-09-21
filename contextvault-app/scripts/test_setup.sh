#!/bin/bash

# ContextVault Desktop App Test Setup Script
# This script tests if the Tauri app can be built and run

set -e

echo "🧪 Testing ContextVault Desktop App Setup"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Error: Please run this script from the contextvault-app directory${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js: $NODE_VERSION${NC}"
else
    echo -e "${RED}❌ Node.js not found. Please install Node.js${NC}"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅ npm: $NPM_VERSION${NC}"
else
    echo -e "${RED}❌ npm not found. Please install npm${NC}"
    exit 1
fi

# Check Rust
if command -v rustc &> /dev/null; then
    RUST_VERSION=$(rustc --version)
    echo -e "${GREEN}✅ Rust: $RUST_VERSION${NC}"
else
    echo -e "${RED}❌ Rust not found. Please install Rust from https://rustup.rs/${NC}"
    exit 1
fi

# Check Cargo
if command -v cargo &> /dev/null; then
    CARGO_VERSION=$(cargo --version)
    echo -e "${GREEN}✅ Cargo: $CARGO_VERSION${NC}"
else
    echo -e "${RED}❌ Cargo not found. Please install Rust toolchain${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Installing dependencies...${NC}"

# Install npm dependencies
if npm install; then
    echo -e "${GREEN}✅ npm dependencies installed${NC}"
else
    echo -e "${RED}❌ Failed to install npm dependencies${NC}"
    exit 1
fi

echo -e "${BLUE}🔧 Checking project structure...${NC}"

# Check required files
REQUIRED_FILES=(
    "src/index.html"
    "src/styles.css"
    "src/app.js"
    "src-tauri/Cargo.toml"
    "src-tauri/src/main.rs"
    "src-tauri/tauri.conf.json"
    "package.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ Missing: $file${NC}"
        exit 1
    fi
done

echo -e "${BLUE}🎯 Testing Tauri CLI...${NC}"

# Check if Tauri CLI is available
if command -v tauri &> /dev/null; then
    echo -e "${GREEN}✅ Tauri CLI is available${NC}"
else
    echo -e "${YELLOW}⚠️  Installing Tauri CLI...${NC}"
    npm install -g @tauri-apps/cli
fi

echo -e "${BLUE}🔨 Testing build process...${NC}"

# Test if the project can be built (without actually building)
if tauri info; then
    echo -e "${GREEN}✅ Tauri project configuration is valid${NC}"
else
    echo -e "${RED}❌ Tauri project configuration has issues${NC}"
    exit 1
fi

echo -e "${BLUE}🧪 Testing development mode...${NC}"

# Test if the project can start in dev mode (for a few seconds)
echo -e "${YELLOW}Starting development server for 10 seconds...${NC}"
timeout 10s npm run tauri dev || true

echo ""
echo -e "${GREEN}🎉 ContextVault Desktop App Setup Test Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo -e "  ✅ All prerequisites installed"
echo -e "  ✅ Project structure is correct"
echo -e "  ✅ Dependencies installed"
echo -e "  ✅ Tauri configuration is valid"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo -e "  1. Run 'npm run tauri dev' to start development mode"
echo -e "  2. Run 'npm run tauri build' to build the application"
echo -e "  3. Use './scripts/build_app.sh' for production builds"
echo ""
echo -e "${GREEN}Your ContextVault desktop app is ready for development! 🎯${NC}"
