# vibe-review

质量审查。触发 RIPER-7 Rev 阶段。

## 语法

```
vibe-review
vibe-review --strict
vibe-review --security
```

## 用户体验

```
你: vibe-review --strict

系统:
  ✓ 结构 — 函数<50行, 嵌套<3层
  ✗ 命名 — handleClick2 不够准确
  ✓ 类型 — 无 any
  ✗ 错误 — 缺少 network error 处理
  ✓ 安全 — 无硬编码密钥
  ✗ 品味 — 数据结构可更简
  → 问题写入 todo.md
  → 经验写入 knowledge
```

加载 skills: code-quality + knowledge。
