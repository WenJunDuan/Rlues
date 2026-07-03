---
name: knowledge
description: 跨会话经验管理 — Rev 阶段沉淀教训, 后续会话自动复用
context: main
---

# Knowledge — 跨会话经验管理

## 目录结构

```
.knowledge/
├── patterns.md        # 项目特有模式 (怎么做是对的)
├── pitfalls.md        # 踩过的坑 (什么做法会出错)
├── decisions.md       # 架构决策记录 (为什么这样做)
└── tools.md           # 工具使用心得 (哪个好用/不好用)
```

## 写入时机

1. **Rev 阶段**: code-review 发现问题 → 记录到 pitfalls.md
2. **V 阶段失败**: 调试后的 root cause → 记录到 pitfalls.md
3. **D 阶段**: 重大设计决策 → 记录到 decisions.md
4. **E 阶段**: 发现好的实现模式 → 记录到 patterns.md

## 写入格式

```markdown
## {日期} — {简短标题}

**场景**: {什么情况下遇到的}
**教训**: {核心结论, 一句话}
**详情**: {可选, 具体细节}
```

## 读取时机

1. **R 阶段**: 搜 `.knowledge/` 看有没有相关经验
2. **E 阶段**: 开始写代码前读 patterns.md 对齐风格
3. **D 阶段**: 做决策前读 decisions.md 查历史选择

## 降级

.knowledge/ 不存在 → 首次使用, 跳过读取, Rev 阶段创建。
文件损坏 → 从 `.ai_state/archive/` 恢复最近版本。
