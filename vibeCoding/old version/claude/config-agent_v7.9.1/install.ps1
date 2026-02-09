# VibeCoding Kernel v7.9 - Installation Script (Windows PowerShell)

$ErrorActionPreference = "Stop"

$VERSION = "7.9.1"
$INSTALL_DIR = "$env:USERPROFILE\.claude"
$BACKUP_DIR = "$env:USERPROFILE\.claude-backup-$(Get-Date -Format 'yyyyMMddHHmmss')"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      VibeCoding Kernel v7.9.1                                ║" -ForegroundColor Cyan
Write-Host "║      AI Programming Collaboration System                     ║" -ForegroundColor Cyan
Write-Host "║                                                              ║" -ForegroundColor Cyan
Write-Host "║      New in v7.9:                                            ║" -ForegroundColor Cyan
Write-Host "║      • Instinct-based Learning                               ║" -ForegroundColor Cyan
Write-Host "║      • Cunzhi MCP Integration                                ║" -ForegroundColor Cyan
Write-Host "║      • Context7 CLI Support                                  ║" -ForegroundColor Cyan
Write-Host "║      • Cross-platform Node.js Hooks                          ║" -ForegroundColor Cyan
Write-Host "║      • Rules System                                          ║" -ForegroundColor Cyan
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

# Create directories
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
New-Item -ItemType Directory -Path "$INSTALL_DIR\skills" -Force | Out-Null
New-Item -ItemType Directory -Path "$INSTALL_DIR\rules" -Force | Out-Null

# Copy files
Write-Host "Installing files..." -ForegroundColor Yellow
$SOURCE_DIR = Join-Path $SCRIPT_DIR ".claude"

if (Test-Path $SOURCE_DIR) {
    Copy-Item -Path "$SOURCE_DIR\*" -Destination $INSTALL_DIR -Recurse -Force
    Write-Host "✓ Claude config installed" -ForegroundColor Green
} else {
    Write-Host "✗ .claude directory not found" -ForegroundColor Red
    exit 1
}

# Copy scripts
$SCRIPTS_DIR = Join-Path $SCRIPT_DIR "scripts"
if (Test-Path $SCRIPTS_DIR) {
    Copy-Item -Path $SCRIPTS_DIR -Destination $INSTALL_DIR -Recurse -Force
    Write-Host "✓ Scripts installed" -ForegroundColor Green
}

# Check Node.js
try {
    $nodeVersion = node -v
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠ Node.js not found. Hooks require Node.js 18+" -ForegroundColor Yellow
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
Write-Host "New Commands:" -ForegroundColor Cyan
Write-Host "  instinct-status   - View learned instincts"
Write-Host "  instinct-export   - Export instincts for sharing"
Write-Host "  instinct-import   - Import team instincts"
Write-Host "  evolve            - Evolve instincts into skills"
Write-Host ""
Write-Host "Backup location: $BACKUP_DIR" -ForegroundColor Yellow
Write-Host ""
