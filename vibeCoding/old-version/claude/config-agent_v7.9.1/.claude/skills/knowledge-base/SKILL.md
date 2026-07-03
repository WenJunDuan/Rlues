---
name: knowledge-base
description: |
  External knowledge base reader. Loads project docs, dev standards, company
  requirements from .knowledge/ directory. Auto-invoked during requirement
  analysis, design, and code review phases.
---

# Knowledge Base Skill

## Knowledge Sources

| Type | Path | Use Case |
|:---|:---|:---|
| Project | .knowledge/project/ | 项目背景, 业务领域 |
| Standards | .knowledge/standards/ | 代码规范, Git规范 |
| Company | .knowledge/company/ | 公司要求, 安全策略 |
| Tech | .knowledge/tech/ | 技术栈文档, API |

## Auto-Load Points

| Phase | Load Content |
|:---|:---|
| 需求创建 | project/*.md |
| 方案设计 | tech/*.md |
| 开发实施 | standards/*.md |
| 代码审查 | standards/review-checklist.md |

## Commands

```bash
/vibe-kb list              # 列出知识库
/vibe-kb load <category>   # 加载特定类别
/vibe-kb search <keyword>  # 搜索知识
/vibe-kb add <file>        # 添加到知识库
```

## Integration

- Called by `phase-router` at workflow transitions
- Complements `context7` skill for external library docs
- Feeds into `experience` skill for pattern matching
