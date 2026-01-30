# VibeCoding Kernel v7.9.1 for Codex CLI (Windows)

$VERSION = "7.9.1-codex"
$INSTALL_DIR = "$env:USERPROFILE\.codex"
$BACKUP_DIR = "$env:USERPROFILE\.codex-backup-$(Get-Date -Format 'yyyyMMddHHmmss')"

Write-Host "VibeCoding Kernel v7.9.1 for Codex CLI" -ForegroundColor Cyan

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

if (Test-Path $INSTALL_DIR) {
    Copy-Item -Path $INSTALL_DIR -Destination $BACKUP_DIR -Recurse -Force
}

New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null

$SOURCE = Join-Path $SCRIPT_DIR ".codex"
if (Test-Path $SOURCE) {
    Copy-Item -Path "$SOURCE\*" -Destination $INSTALL_DIR -Recurse -Force
}

$SCRIPTS = Join-Path $SCRIPT_DIR "scripts"
if (Test-Path $SCRIPTS) {
    Copy-Item -Path $SCRIPTS -Destination $INSTALL_DIR -Recurse -Force
}

Write-Host "Installation Complete!" -ForegroundColor Green
