---
name: compound
description: 跨 sprint 经验沉淀到 compound/。learning / trick / decision / explore 时触发。
---

# /compound — 复利知识沉淀

一事一档, ≤100 行。电报体: 教训一句话。模板 `templates/{learning,trick,decision,explore}.md`。

## 四类

| doc_type | 用途 | 触发 |
|---|---|---|
| **learning** | 踩坑 → 教训 | polish 完成 / review P0 / `/compound add learning` |
| **trick** | 可复用模式 | impl 发现写法 / `/compound add trick` |
| **decision** | 技术选型 | design 重大决策 / `/compound add decision` |
| **explore** | 调研结论 | 调研完成 / `/compound add explore` |

命名: `compound/YYYY-MM-DD-{doc_type}-{slug}.md`。slug=kebab-case, 禁空格/下划线/中文。

## 约束

- ≤100 行; 超出拆 slug。禁「压缩 pass」合并多事。
- `decision` 改状态用 `superseded-by: {slug}`, 不删。
- doc_type 四选一。frontmatter 必填 date/sprint/status。
- index-updater 按 type 计数。

## 写 / 读

| 时机 | 动作 |
|---|---|
| polish 完成 | learning |
| 独立 review P0 | learning |
| design 重大决策 | decision |
| impl 优雅 pattern | trick |
| 调研完成 | explore |
| plan 开始 | 读 `_index.pointers.latest_decisions` 近 5 个 decision |
| design | grep 相关 learning/trick |
| review | 查 decision 冲突与重复踩坑 |
| brainstorm | **不读** compound |

命令: `/compound add {type} {slug}` · `list [type]` · `search {keyword}`。

## archive

新 quarter 第一 sprint: 上 quarter 非 decision 迁 `.ai_state/archive-{quarter}/compound/`。decision 永留。旧 `lessons.md` 迁移动作见 athena-migrate。
