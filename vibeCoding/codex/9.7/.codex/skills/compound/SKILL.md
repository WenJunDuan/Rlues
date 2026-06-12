---
name: compound
description: |
  Compound Learning Loop. 跨 sprint 积累的经验沉淀到 compound/, 按 doc_type 分文件存档.
  4 种 doc_type: learning / trick / decision / explore.
  v9.6.4 重写 (替代 v9.6.2 单文件 lessons.md). 铁律 13: 一事一档, ≤100 行.
effort: medium
---

# /compound — 复利知识沉淀 (v9.6.4 重写)

## 哲学 (借 CodeStable)

> 软件复杂度膨胀撑破上下文、隐知识丢失、需求漂移. compound/ 是复利工程的物理实现.
> "下一次 cs-arch / cs-feat-design / cs-issue-analyze 会回头读 compound/, 让经验在新工作里被复用".

## 四类 doc_type

| doc_type | 用途 | 触发时机 | 模板 |
|---|---|---|---|
| **learning** | 踩坑 → 教训 | polish 完成 / review P0 finding / 用户主动 `/compound add learning` | `templates/learning.md` |
| **trick** | 可复用模式 | impl 发现优雅写法 / 用户主动 `/compound add trick` | `templates/trick.md` |
| **decision** | 拍板技术选型 (类 ADR) | design 重大决策 / 用户主动 `/compound add decision` | `templates/decision.md` |
| **explore** | 代码调研结论 | docs_researcher 完成 / 用户主动 `/compound add explore` | `templates/explore.md` |

## 文件命名 (铁律 13)

```
compound/YYYY-MM-DD-{doc_type}-{slug}.md
```

例:
- `compound/2026-05-25-decision-jwt-rs256-vs-hs256.md`
- `compound/2026-05-25-learning-useeffect-deps-infinite-loop.md`
- `compound/2026-05-26-trick-redis-pipeline-batch-fetch.md`
- `compound/2026-05-26-explore-react-19-concurrent-rendering.md`

## 约束 (铁律 13)

- ✅ 每个 compound 文件 **≤ 100 行** (超出 → 拆分成多个 slug)
- ❌ 不允许"压缩 pass" (一事一档, 不合并)
- ✅ `decision` 改状态用 `superseded-by: {slug}` 引用, 不直接删
- ✅ doc_type 必 4 选 1, 不允许混合
- ✅ slug 必须 kebab-case, 不允许空格 / 下划线 / 中文
- ✅ frontmatter 必填 (date, sprint, status)
- ✅ index-updater hook 按 doc_type 自动分类计数

## 写入时机 (强制)

| 时机 | doc_type | 写入责任 |
|---|---|---|
| polish 完成 (cleanup-pass.md 写完) | learning | polish_worker / 主 agent |
| review_pass1 发现 P0 finding | learning | reviewer subagent |
| design.md 含重大决策 (e.g. "我们决定 X 不用 Y") | decision | 主 agent / architect |
| impl 时发现优雅 pattern | trick | generator / 主 agent |
| docs_researcher 调研完成 | explore | docs_researcher |
| 用户显式 `/compound add {type}` | 任意 | 主 agent |

## 读取时机 (强制)

| 时机 | 读什么 | 责任 |
|---|---|---|
| plan stage 开始 | `_index.pointers.latest_decisions` 列出的 5 个 `decision-*.md` | 主 agent (强制) |
| design stage | grep 关键词读相关 `learning-*.md` + `trick-*.md` | 主 agent / architect |
| review stage (critic) | 历史 decision 冲突检查 + 历史 learning 重复踩坑检查 | critic subagent |
| brainstorm stage | **不读 compound** (创意空间不污染) | (跳过) |

## 命令

| 命令 | 作用 |
|---|---|
| `/compound add learning {slug}` | 触发 learning 模板, 主 agent 填空 |
| `/compound add trick {slug}` | 触发 trick 模板 |
| `/compound add decision {slug}` | 触发 decision 模板 |
| `/compound add explore {slug}` | 触发 explore 模板 |
| `/compound list [type]` | 列出 compound 文件 (按 type 筛) |
| `/compound search {keyword}` | grep 全 compound 搜关键词 |

## archive 机制 (借 OpenSpec /opsx:archive)

跨季度时自动归档:
- 触发: 新 quarter 第一 sprint 启动时, athena-dev 检测
- 动作: 上 quarter 的 `compound/*.md` 移到 `.ai_state/archive-{quarter}/compound/`
- 主 `compound/` 只保留近 1 quarter + 所有 `decision-*.md` (永远保留 decision)

## 模板

见 `~/.agents/skills/_athena/compound/templates/{learning,trick,decision,explore}.md`

## 与其他 stage 联动 (vs v9.6.2 单文件)

```
v9.6.2 (lessons.md 单文件):                v9.6.4 (compound/ 颗粒化):
  - 追加一段                                  - 新建一个文件
  - grep 全文找                               - grep 文件名 + 内容
  - 3 个月后 500 行混合                       - 一事一档, ≤100 行
  - 跨 sprint 全部读                          - latest_decisions 仅近 5 个
```

## v9.6.2 → v9.6.4 迁移

`athena-migrate` 处理 lessons.md, 用户三选:
1. 整体保留 → 转成单个 `compound/{today}-learning-legacy-migration.md`
2. 手工拆分 → 主 agent 引导逐段分类
3. 全部丢弃 → 删除 lessons.md, compound/ 从空开始

详: `~/.agents/skills/_athena/athena-migrate/SKILL.md`
