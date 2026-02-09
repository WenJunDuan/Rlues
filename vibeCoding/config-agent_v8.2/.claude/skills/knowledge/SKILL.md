---
name: knowledge
---

# 知识与经验管理

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| sou | MCP | 语义搜索 .knowledge/ | `sou.search("关键词")` |
| deepwiki | MCP | 补充外部技术知识 | `deepwiki.query("主题")` |
| Superpowers requesting-code-review | Plugin Skill | Rev 阶段触发经验提取 | 自动 |

## .knowledge/ 结构

```
.knowledge/
├── index.md            # 知识索引
├── project/            # PRD, 架构图, 技术栈
├── standards/          # 编码规范 (项目特有的)
├── experience/
│   ├── patterns.md     # 成功模式
│   ├── mistakes.md     # 错误记录 (root cause + fix)
│   └── instincts.md    # 直觉 (置信度评分)
└── tech/               # 技术栈参考
```

## 触发时机

| 时机 | 动作 | 工具 |
|:---|:---|:---|
| vibe-init --scan | 扫描项目 → project/overview.md | sou, deepwiki, find/grep |
| RIPER R 阶段 | 读取相关知识 | sou.search(.knowledge/) |
| RIPER Rev 阶段 | 提取经验 → experience/ | Superpowers review |
| 用户纠正 | 记录规则 | → conventions.md + mistakes.md |
| vibe-debug 完成 | 记录 root cause | → mistakes.md |

## 经验格式

```markdown
### EXP-{{id}}: {{标题}}
- 模式: {{描述}}
- 置信度: {{0.0-1.0}}
- 来源: {{观察次数}}
- 日期: {{date}}
```

## Instinct 演化

```
首次观察 → 置信度 0.3
重复出现 → +0.1/次
置信度 >0.8 且 >5 次 → 建议写入 conventions.md
```
