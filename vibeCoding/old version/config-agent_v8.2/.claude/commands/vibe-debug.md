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
  1. 复现: 确认 bug
  2. 定位: sou 搜索 + 二分缩小
  3. 修复: 写修复测试(RED) → 最小修复(GREEN)
  4. 验证: 全测试通过 → 记录 root cause
```

加载 skills: debugging。
