---
name: vibe-kb
description: |
  知识库操作命令。管理项目文档、技术规范、公司要求等外部知识。
  支持按需加载到开发流程中。
---

# vibe-kb Command

管理外部知识库。

## 使用方式

```bash
# 列出知识库内容
vibe-kb list

# 搜索知识
vibe-kb search "API 规范"

# 查看特定文档
vibe-kb show tech/api-standards.md

# 添加知识
vibe-kb add project/architecture.md

# 刷新知识库索引
vibe-kb refresh
```

## 知识库结构

```
knowledge-base/
├── project/              # 项目文档
│   ├── README.md         # 项目概述
│   ├── architecture.md   # 架构设计
│   └── decisions/        # 技术决策记录
│       └── adr-001.md
│
├── tech/                 # 技术规范
│   ├── api-standards.md  # API 规范
│   ├── database.md       # 数据库规范
│   └── security.md       # 安全规范
│
├── standards/            # 开发标准
│   ├── code-style.md     # 代码风格
│   ├── git-workflow.md   # Git 工作流
│   ├── review-checklist.md # 审查清单
│   └── testing.md        # 测试规范
│
└── company/              # 公司要求
    ├── compliance.md     # 合规要求
    ├── security-policy.md # 安全政策
    └── naming.md         # 命名规范
```

## 自动加载时机

```yaml
知识库自动加载:
  需求创建阶段:
    - project/*.md (项目背景)
    
  方案设计阶段:
    - tech/*.md (技术约束)
    - project/architecture.md
    
  开发实施阶段:
    - standards/code-style.md
    - standards/testing.md
    - company/*.md (合规要求)
    
  代码审查阶段:
    - standards/review-checklist.md
    - tech/security.md
```

## 命令详情

### list - 列出内容

```bash
# 列出全部
vibe-kb list

# 按分类列出
vibe-kb list project/
vibe-kb list tech/
```

输出：
```markdown
📖 Knowledge Base

## project/ (3 files)
- README.md - 项目概述
- architecture.md - 架构设计
- decisions/ (2 ADRs)

## tech/ (3 files)
- api-standards.md - API 规范
- database.md - 数据库规范
- security.md - 安全规范

## standards/ (4 files)
- code-style.md - 代码风格
- git-workflow.md - Git 工作流
- review-checklist.md - 审查清单
- testing.md - 测试规范

## company/ (3 files)
- compliance.md - 合规要求
- security-policy.md - 安全政策
- naming.md - 命名规范

Total: 15 documents
```

### search - 搜索知识

```bash
# 关键词搜索
vibe-kb search "API"

# 限定分类搜索
vibe-kb search "规范" --in=standards/
```

### show - 查看文档

```bash
# 查看完整内容
vibe-kb show tech/api-standards.md

# 查看摘要
vibe-kb show tech/api-standards.md --summary
```

### add - 添加知识

```bash
# 添加新文档
vibe-kb add project/new-feature.md

# 从 URL 添加
vibe-kb add --url=https://docs.example.com/api
```

### refresh - 刷新索引

```bash
# 重建索引
vibe-kb refresh

# 验证完整性
vibe-kb refresh --verify
```

## 知识文档模板

```markdown
---
title: API 设计规范
category: tech
last_updated: 2025-01-23
tags: [api, rest, standards]
applies_to: [backend, api]
---

# API 设计规范

## 概述
本文档定义项目 API 设计标准...

## 规范内容

### URL 命名
- 使用小写字母
- 使用连字符分隔
- 使用名词复数

### 响应格式
```json
{
  "data": {},
  "meta": {},
  "errors": []
}
```

## 示例
...

## 参考
- [REST API 最佳实践](link)
```

## 与其他命令协作

```yaml
vibe-plan:
  - 检索项目背景
  - 加载技术约束

vibe-dev:
  - 加载开发规范
  - 应用代码标准

vibe-review:
  - 加载审查清单
  - 应用安全策略

context7:
  - 外部库文档
  - 框架最佳实践
```
