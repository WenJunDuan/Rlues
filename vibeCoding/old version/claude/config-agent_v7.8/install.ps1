# VibeCoding Kernel v7.8 - Installation Script (Windows PowerShell)

$ErrorActionPreference = "Stop"

$VERSION = "7.8.0"
$INSTALL_DIR = "$env:USERPROFILE\.claude"
$BACKUP_DIR = "$env:USERPROFILE\.claude-backup-$(Get-Date -Format 'yyyyMMddHHmmss')"

# Colors
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) { Write-Output $args }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          VibeCoding Kernel v7.8 Installer                    ║" -ForegroundColor Cyan
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
$SOURCE_DIR = Join-Path $SCRIPT_DIR ".claude"

if (Test-Path $SOURCE_DIR) {
    Copy-Item -Path "$SOURCE_DIR\*" -Destination $INSTALL_DIR -Recurse -Force
    Write-Host "✓ Files installed from local package" -ForegroundColor Green
} else {
    Write-Host "✗ .claude directory not found. Run from package root." -ForegroundColor Red
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
Write-Host "  vibe-plan    - Enhanced planning"
Write-Host "  vibe-review  - Code review"
Write-Host "  /learn       - Extract patterns"
Write-Host "  /checkpoint  - Save state"
Write-Host "  /verify      - Run verification"
Write-Host ""
Write-Host "Backup: $BACKUP_DIR" -ForegroundColor Yellow
Write-Host ""
