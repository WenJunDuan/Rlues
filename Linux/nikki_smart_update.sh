#!/bin/bash
# set -euo pipefail
#==========================================
# Nikki Smart 内核自动更新脚本 (统一目录 + 智能备份)
# Author: GPT-5 + WenJ
# Updated: 2025-10-05
#==========================================

#=== 全局代理设置（强制启用） ===#
export http_proxy="http://127.0.0.1:7890"
export https_proxy="http://127.0.0.1:7890"
export all_proxy="http://127.0.0.1:7890"
echo "[网络代理] 已启用 → http://127.0.0.1:7890"

#=== 日志函数 ===#
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

#=== 路径定义 ===#
BASE_DIR="/etc/nikki"
TMP_DIR="$BASE_DIR/tmp"
LOG_DIR="$BASE_DIR/log"
MODEL_DIR="$BASE_DIR/run"
BAK_DIR="$BASE_DIR/bak"
LOG_FILE="$LOG_DIR/update_$(date '+%Y-%m-%d_%H-%M-%S').log"

mkdir -p "$TMP_DIR" "$LOG_DIR" "$MODEL_DIR" "$BAK_DIR"

log "🚀 开始 Nikki Smart 内核更新流程"

#=== 获取最新版本号（GitHub Releases） ===#
log "获取 Mihomo Smart 内核版本号..."
VERSION_URL="https://github.com/vernesong/mihomo/releases/download/Prerelease-Alpha/version.txt"

version=$(curl -sL --connect-timeout 10 --max-time 20 "$VERSION_URL" 2>/dev/null)
if [ -z "$version" ]; then
    version=$(wget -qO - "$VERSION_URL" 2>/dev/null)
fi
version=$(echo "$version" | tr -d ' \n\r')

if [ -z "$version" ]; then
    log "❌ 无法获取版本号，请检查代理或 GitHub 连接"
    exit 1
fi

log "✅ 检测到版本号：$version"

#=== 下载内核 ===#
DOWNLOAD_URL="https://github.com/vernesong/mihomo/releases/download/Prerelease-Alpha/mihomo-linux-amd64-compatible-$version.gz"
TARGET_FILE="$TMP_DIR/mihomo-linux-amd64.gz"

log "下载内核中：$DOWNLOAD_URL"
if ! wget -qO "$TARGET_FILE" "$DOWNLOAD_URL"; then
    log "❌ 内核下载失败，请检查网络连接或代理设置"
    exit 1
fi

#=== 解压 ===#
log "解压内核文件..."
gzip -df "$TARGET_FILE"

#=== 备份旧版本 (内核 + 模型) ===#
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
log "备份旧文件到 $BAK_DIR ..."

if [ -f /usr/bin/mihomo ]; then
    cp /usr/bin/mihomo "$BAK_DIR/mihomo_$TIMESTAMP"
    log "✅ 已备份旧内核 /usr/bin/mihomo → $BAK_DIR/mihomo_$TIMESTAMP"
fi

if [ -f "$MODEL_DIR/Model-large.bin" ]; then
    cp "$MODEL_DIR/Model-large.bin" "$BAK_DIR/Model_$TIMESTAMP.bin"
    log "✅ 已备份旧模型 Model-large.bin → $BAK_DIR/Model_$TIMESTAMP.bin"
fi

#=== 保留最新备份，仅保留两份最新 ===#
log "清理旧备份，仅保留最新版本..."
cd "$BAK_DIR"
ls -1t | tail -n +3 | xargs -r rm -f

#=== 替换新内核 ===#
log "替换新内核..."
mv -f "$TMP_DIR/mihomo-linux-amd64" /usr/bin/mihomo
chmod +x /usr/bin/mihomo
log "✅ 内核替换完成"

#=== 下载 Smart 模型文件 ===#
MODEL_FILE="$MODEL_DIR/Model.bin"
MODEL_URL="https://github.com/vernesong/mihomo/releases/download/LightGBM-Model/Model-large.bin"

log "下载 Smart 模型文件..."
if wget -qO "$MODEL_FILE" "$MODEL_URL"; then
    log "✅ Model.bin 已成功下载至 $MODEL_FILE"
else
    log "⚠️ Model.bin 下载失败，请稍后重试"
fi

#=== 重启 Nikki 服务 ===#
log "重启 Nikki 服务..."
if command -v systemctl &>/dev/null; then
    systemctl restart nikki && log "✅ Nikki 服务已重启" || log "⚠️ Nikki 服务重启失败，请手动检查"
else
    service nikki restart && log "✅ Nikki 服务已重启" || log "⚠️ Nikki 服务重启失败，请手动检查"
fi

#=== 清理临时文件 ===#
log "清理临时文件..."
rm -rf "$TMP_DIR"/*

log "清理 15 天前的旧日志..."
find "$LOG_DIR" -type f -name "update_*.log" -mtime +15 -delete

log "🎉 Nikki Smart 内核更新流程完成！版本：$version"

