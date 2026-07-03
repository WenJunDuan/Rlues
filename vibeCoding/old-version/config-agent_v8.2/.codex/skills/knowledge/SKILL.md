---
name: knowledge
description: "Experience extraction and knowledge base management with instinct scoring"
---

# 知识与经验管理

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| sou | MCP | 语义搜索 .knowledge/ | `sou.search("关键词")` |
| deepwiki | MCP | 补充外部技术知识 | `deepwiki.query("主题")` |
| SP requesting-code-review | Superpowers | Rev 阶段触发经验提取 | 自动 |

## .knowledge/ 结构

```
.knowledge/
├── index.md
├── project/         # PRD, 架构图, 技术栈
├── standards/       # 编码规范 (项目特有)
├── experience/
│   ├── patterns.md  # 成功模式
│   ├── mistakes.md  # 错误记录 (root cause + fix)
│   └── instincts.md # 直觉 (置信度评分)
└── tech/
```

## 触发时机

| 时机 | 动作 | 工具 |
|:---|:---|:---|
| vibe-init --scan | 扫描项目 → project/overview.md | sou, deepwiki, find/grep |
| RIPER R 阶段 | 读取相关知识 | sou.search(.knowledge/) |
| RIPER Rev 阶段 | 提取经验 → experience/ | SP review |
| 用户纠正 | 记录规则 | → conventions.md + mistakes.md |
| vibe-debug 完成 | 记录 root cause | → mistakes.md |

## Instinct 演化

首次观察 → 0.3 → 重复 +0.1/次 → >0.8 且 >5 次 → 写入 conventions.md
