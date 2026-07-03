#!/bin/bash
set -e
VERSION="8.0.0-codex"
INSTALL_DIR="${HOME}/.codex"
BACKUP_DIR="${HOME}/.codex-backup-$(date +%Y%m%d%H%M%S)"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║      VibeCoding Kernel v8.0 for Codex CLI                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -d "$INSTALL_DIR" ]; then
    echo "Backing up to $BACKUP_DIR..."
    cp -r "$INSTALL_DIR" "$BACKUP_DIR"
fi

mkdir -p "$INSTALL_DIR"

if [ -d "$SCRIPT_DIR/.codex" ]; then
    cp -r "$SCRIPT_DIR/.codex/"* "$INSTALL_DIR/"
    echo "✓ Config installed"
fi

if [ -d "$SCRIPT_DIR/scripts" ]; then
    cp -r "$SCRIPT_DIR/scripts" "$INSTALL_DIR/"
    echo "✓ Scripts installed"
fi

echo ""
echo "Installation Complete!"
echo ""
echo "MCP (Codex): augment-context-engine, chrome-devtools, cunzhi, desktop-commander, mcp-deepwiki"
echo ""
echo "Quick Start:"
echo "  cd your-project && vibe-init && vibe-dev 'task'"
