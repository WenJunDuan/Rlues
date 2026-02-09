---
name: experience
description: |
  Experience management for pattern retrieval and deposit. Searches past
  solutions before development, deposits new patterns after completion.
  Works with continuous-learning skill for auto-extraction.
---

# Experience Skill

## Functions

### experience-index
Search experience library before development:
```yaml
Trigger: 开发任务开始前
Action: 搜索相关经验
Output: 匹配的模式和解决方案
```

### experience-deposit
Save new experience after completion:
```yaml
Trigger: 任务完成后
Action: 沉淀经验到库
Format: EXP-xxx.md
```

### experience-match
Rule-based best practice matching:
```yaml
Input: 当前任务描述
Process: 关键词匹配 + 语义相似
Output: 排序的相关经验列表
```

## Storage Structure

```
.ai_state/experience/
├── index.md          # 经验索引
├── learned/          # 自动提取的模式
│   └── pattern-xxx.md
└── EXP-xxx.md        # 手动沉淀的经验
```

## Experience Format

```markdown
# EXP-001: [标题]
Created: 2025-01-23
Tags: [auth, jwt, nextjs]

## 问题背景
[遇到的问题]

## 解决方案
[如何解决]

## 代码示例
[关键代码]

## 注意事项
[经验教训]
```

## Commands

```bash
/vibe-exp search <keyword>  # 搜索经验
/vibe-exp add               # 添加经验
/vibe-exp list              # 列出经验
```
