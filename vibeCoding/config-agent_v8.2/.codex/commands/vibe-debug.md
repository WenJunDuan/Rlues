# vibe-debug

系统化调试。四阶段根因分析。

## 语法

```
vibe-debug "问题描述"
vibe-debug --file=src/auth.ts "登录后白屏"
```

## 用户体验

```
你: vibe-debug "登录后跳转白屏"

系统:
  1. 复现 (chrome-devtools 抓前端错误)
  2. 定位 (sou + 二分法)
  3. 修复 (RED → GREEN)
  4. 验证 → 记录 root cause
```

加载 skills: debugging。Codex 优势: chrome-devtools 实时前端调试。
