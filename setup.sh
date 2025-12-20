#!/bin/bash

# ╔═══════════════════════════════════════════════════════════════════╗
# ║   FinanceGhost Autonomous - Setup Script                          ║
# ║   Installs all dependencies for backend and frontend              ║
# ╚═══════════════════════════════════════════════════════════════════╝

set -e

echo "
╔═══════════════════════════════════════════════════════════════════╗
║          FINANCEGHOST AUTONOMOUS - SETUP                          ║
╚═══════════════════════════════════════════════════════════════════╝
"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Navigate to project root
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

echo -e "${BLUE}📁 Project root: ${PROJECT_ROOT}${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════════
# System Dependencies Check
# ═══════════════════════════════════════════════════════════════════

echo -e "${YELLOW}🔍 Checking system dependencies...${NC}"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python: ${PYTHON_VERSION}${NC}"
else
    echo -e "${RED}✗ Python3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

# Check Bun
if command -v bun &> /dev/null; then
    BUN_VERSION=$(bun --version)
    echo -e "${GREEN}✓ Bun: ${BUN_VERSION}${NC}"
else
    echo -e "${RED}✗ Bun not found. Installing...${NC}"
    curl -fsSL https://bun.sh/install | bash
    export PATH="$HOME/.bun/bin:$PATH"
fi

# Check Tesseract (optional)
if command -v tesseract &> /dev/null; then
    echo -e "${GREEN}✓ Tesseract OCR installed${NC}"
else
    echo -e "${YELLOW}⚠ Tesseract not found. OCR will use fallback mode.${NC}"
    echo -e "${YELLOW}  To install: brew install tesseract${NC}"
fi

# Check Poppler (optional)
if command -v pdftoppm &> /dev/null; then
    echo -e "${GREEN}✓ Poppler (PDF tools) installed${NC}"
else
    echo -e "${YELLOW}⚠ Poppler not found. PDF processing may be limited.${NC}"
    echo -e "${YELLOW}  To install: brew install poppler${NC}"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# Backend Setup
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}🐍 Setting up Python backend...${NC}"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt -q

echo -e "${GREEN}✓ Backend dependencies installed${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Frontend Setup
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}⚛️  Setting up React frontend...${NC}"

cd frontend

# Install dependencies
echo "Installing frontend dependencies..."
bun install

echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
echo ""

cd "$PROJECT_ROOT"

# ═══════════════════════════════════════════════════════════════════
# Environment Setup
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}🔧 Setting up environment...${NC}"

if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please configure your API keys in .env${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Create frontend .env if needed
if [ ! -f "frontend/.env" ]; then
    echo "VITE_API_URL=http://localhost:8000" > frontend/.env
    echo -e "${GREEN}✓ Frontend .env created${NC}"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════

echo -e "${GREEN}
╔═══════════════════════════════════════════════════════════════════╗
║                    SETUP COMPLETE! ✅                             ║
╚═══════════════════════════════════════════════════════════════════╝
${NC}"

echo "Next steps:"
echo ""
echo "  1. Configure API keys in .env:"
echo "     - GOOGLE_CLOUD_PROJECT (for Vertex AI)"
echo "     - or OPENAI_API_KEY (for OpenAI)"
echo ""
echo "  2. Run the application:"
echo "     ./start.sh"
echo ""
echo "  3. Or run manually:"
echo "     Terminal 1: source venv/bin/activate && uvicorn app.main:app --reload --port 8000"
echo "     Terminal 2: cd frontend && bun run dev"
echo ""
