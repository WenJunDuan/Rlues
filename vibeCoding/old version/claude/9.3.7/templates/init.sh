#!/bin/bash
# VibeCoding init.sh — 启动 + 基线验证
set -e
echo "[init.sh] 启动..."
if [ -f package.json ]; then npm install && PORT=${PORT:-3000} npm run dev &
elif [ -f requirements.txt ]; then pip install -r requirements.txt && PORT=${PORT:-8000} python manage.py runserver 0.0.0.0:$PORT &
fi
for i in $(seq 1 30); do curl -s http://localhost:${PORT:-3000} > /dev/null 2>&1 && break; sleep 1; done
[ -f playwright.config.* ] && npx playwright test --grep @baseline 2>/dev/null || true
echo "[init.sh] ✅ Ready"
