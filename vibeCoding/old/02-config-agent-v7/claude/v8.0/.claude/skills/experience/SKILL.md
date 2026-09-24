---
name: experience
description: |
  Experience management. Stores learned patterns, mistakes, and
  best practices from past development sessions.
---

# Experience Skill

## 存储

```
.knowledge/experience/
├── patterns.md       # 反复出现的成功模式
├── mistakes.md       # 错误和修复记录
├── instincts.md      # 自动学习的直觉 (v2)
└── evolved/          # 已演化为 skill 的模式
```

## 经验格式

```markdown
### EXP-{{id}}: {{标题}}
- **模式**: {{描述}}
- **置信度**: {{0.0-1.0}}
- **来源**: {{观察次数和场景}}
- **分类**: coding-pattern | error-pattern | architecture | workflow
```

## 触发时机

- R2 (Review) 阶段自动提取
- vibe-learn 手动触发
- 用户纠正时记录到 mistakes.md

## 演化路径

instinct (置信度 >0.8, 出现 >5 次) → 建议 evolve 为 skill
