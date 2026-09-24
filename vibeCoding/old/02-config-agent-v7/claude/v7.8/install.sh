#!/bin/bash

# VibeCoding Kernel v7.8 - Installation Script (Linux/macOS)

set -e

VERSION="7.8.0"
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
║          VibeCoding Kernel v7.8 Installer                    ║
║      AI Programming Collaboration System                     ║
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

# Copy files
echo -e "${YELLOW}Installing files...${NC}"
if [ -d "$SCRIPT_DIR/.claude" ]; then
    cp -r "$SCRIPT_DIR/.claude/"* "$INSTALL_DIR/"
    echo -e "${GREEN}✓ Files installed from local package${NC}"
else
    echo -e "${RED}✗ .claude directory not found. Run from package root.${NC}"
    exit 1
fi

# Make scripts executable
find "$INSTALL_DIR" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

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
echo -e "${BLUE}Key Commands:${NC}"
echo "  vibe-dev     - Smart development entry"
echo "  vibe-plan    - Enhanced planning"
echo "  vibe-review  - Code review"
echo "  /learn       - Extract patterns"
echo "  /checkpoint  - Save state"
echo "  /verify      - Run verification"
echo ""
echo -e "${YELLOW}Backup: ${BACKUP_DIR}${NC}"
echo ""
