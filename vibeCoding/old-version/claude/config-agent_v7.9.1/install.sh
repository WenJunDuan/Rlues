#!/bin/bash

# VibeCoding Kernel v7.9 - Installation Script (Linux/macOS)

set -e

VERSION="7.9.1"
INSTALL_DIR="${HOME}/.claude"
BACKUP_DIR="${HOME}/.claude-backup-$(date +%Y%m%d%H%M%S)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << 'BANNER'
╔══════════════════════════════════════════════════════════════╗
║      VibeCoding Kernel v7.9.1                                ║
║      AI Programming Collaboration System                     ║
║                                                              ║
║      New in v7.9:                                            ║
║      • Instinct-based Learning                               ║
║      • Cunzhi MCP Integration                                ║
║      • Context7 CLI Support                                  ║
║      • Cross-platform Node.js Hooks                          ║
║      • Rules System                                          ║
╚══════════════════════════════════════════════════════════════╝
BANNER
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Backup existing
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Backing up existing config to ${BACKUP_DIR}...${NC}"
    cp -r "$INSTALL_DIR" "$BACKUP_DIR"
    echo -e "${GREEN}✓ Backup created${NC}"
fi

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/skills"
mkdir -p "$INSTALL_DIR/rules"

# Copy files
echo -e "${YELLOW}Installing files...${NC}"
if [ -d "$SCRIPT_DIR/.claude" ]; then
    cp -r "$SCRIPT_DIR/.claude/"* "$INSTALL_DIR/"
    echo -e "${GREEN}✓ Claude config installed${NC}"
else
    echo -e "${RED}✗ .claude directory not found${NC}"
    exit 1
fi

# Copy scripts
if [ -d "$SCRIPT_DIR/scripts" ]; then
    cp -r "$SCRIPT_DIR/scripts" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/scripts/hooks/"*.js 2>/dev/null || true
    echo -e "${GREEN}✓ Scripts installed${NC}"
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✓ Node.js found: ${NODE_VERSION}${NC}"
else
    echo -e "${YELLOW}⚠ Node.js not found. Hooks require Node.js 18+${NC}"
fi

# Check for cunzhi MCP
echo -e "${YELLOW}Checking MCP configuration...${NC}"
if [ -f "${HOME}/.claude.json" ]; then
    if grep -q "cunzhi" "${HOME}/.claude.json"; then
        echo -e "${GREEN}✓ Cunzhi MCP configured${NC}"
    else
        echo -e "${YELLOW}⚠ Cunzhi MCP not found in ~/.claude.json${NC}"
        echo -e "${YELLOW}  Add cunzhi MCP for best experience${NC}"
    fi
fi

# Success message
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Installation Complete! 🎉                           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Quick Start:${NC}"
echo ""
echo "  1. Initialize project:  ${YELLOW}cd your-project && vibe-init${NC}"
echo "  2. Start development:   ${YELLOW}vibe-dev \"task description\"${NC}"
echo ""
echo -e "${BLUE}New Commands:${NC}"
echo "  instinct-status   - View learned instincts"
echo "  instinct-export   - Export instincts for sharing"
echo "  instinct-import   - Import team instincts"
echo "  evolve            - Evolve instincts into skills"
echo ""
echo -e "${BLUE}Key Changes in v7.9:${NC}"
echo "  • Context7 via CLI (npx ctx7) instead of MCP"
echo "  • Cunzhi MCP for confirmations"
echo "  • Instinct-based learning with confidence scores"
echo "  • Cross-platform Node.js hooks"
echo "  • Rules system for consistent behavior"
echo ""
echo -e "${YELLOW}Backup location: ${BACKUP_DIR}${NC}"
echo ""
