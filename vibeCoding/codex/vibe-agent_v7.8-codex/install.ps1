# VibeCoding Kernel v7.8 for Codex CLI - Installation Script (Windows PowerShell)

$ErrorActionPreference = "Stop"

$VERSION = "7.8.0-codex"
$INSTALL_DIR = "$env:USERPROFILE\.codex"
$BACKUP_DIR = "$env:USERPROFILE\.codex-backup-$(Get-Date -Format 'yyyyMMddHHmmss')"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      VibeCoding Kernel v7.8 for Codex CLI                    ║" -ForegroundColor Cyan
Write-Host "║      AI Programming Collaboration System                     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Backup existing
if (Test-Path $INSTALL_DIR) {
    Write-Host "Backing up existing config to $BACKUP_DIR..." -ForegroundColor Yellow
    Copy-Item -Path $INSTALL_DIR -Destination $BACKUP_DIR -Recurse -Force
    Write-Host "✓ Backup created" -ForegroundColor Green
}

# Create directory
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null

# Copy files
Write-Host "Installing files..." -ForegroundColor Yellow
$SOURCE_DIR = Join-Path $SCRIPT_DIR ".codex"

if (Test-Path $SOURCE_DIR) {
    Copy-Item -Path "$SOURCE_DIR\*" -Destination $INSTALL_DIR -Recurse -Force
    Write-Host "✓ Files installed from local package" -ForegroundColor Green
} else {
    Write-Host "✗ .codex directory not found. Run from package root." -ForegroundColor Red
    exit 1
}

# Success message
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          Installation Complete! 🎉                           ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Quick Start:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Initialize project:  " -NoNewline
Write-Host "cd your-project; vibe-init" -ForegroundColor Yellow
Write-Host "  2. Start development:   " -NoNewline
Write-Host 'vibe-dev "task description"' -ForegroundColor Yellow
Write-Host ""
Write-Host "Key Commands:" -ForegroundColor Cyan
Write-Host "  vibe-dev     - Smart development entry"
Write-Host "  vibe-plan    - Task planning"
Write-Host "  vibe-review  - Code review"
Write-Host "  learn        - Extract patterns"
Write-Host "  checkpoint   - Save state"
Write-Host "  verify       - Run verification"
Write-Host ""
Write-Host "Backup: $BACKUP_DIR" -ForegroundColor Yellow
Write-Host ""
