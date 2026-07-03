---
name: knowledge-base
description: |
  Project knowledge management. Stores and retrieves project-specific
  documentation, standards, and technical references.
---

# Knowledge Base Skill

## 结构

```
.knowledge/
├── index.md          # 知识索引 (自动维护)
├── project/          # 项目文档 (PRD, 架构图)
├── standards/        # 开发规范 (编码规范, Git 规范)
├── company/          # 团队约定 (review 流程, 部署流程)
└── tech/             # 技术栈 (框架版本, API 参考)
```

## 操作

### 检索
```
vibe-kb search "关键词"
→ 搜索 .knowledge/ 目录下所有 .md 文件
→ 返回匹配内容和文件路径
```

### 添加
```
vibe-kb add --category=tech "Next.js 14 使用 App Router 作为默认路由"
→ 写入 .knowledge/tech/ 对应文件
→ 更新 index.md
```

## 自动触发

- vibe-plan 时自动检索相关知识
- vibe-review 时自动加载 standards/
- vibe-init 时自动扫描项目生成初始知识
