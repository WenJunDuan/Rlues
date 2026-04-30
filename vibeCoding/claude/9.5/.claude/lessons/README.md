# ~/.claude/lessons/ — 全局工具链经验库

## 这是什么

跨项目的工具链/基础设施经验沉淀。和项目级 `.ai_state/lessons.md` 互补：

| 范围 | 文件 | 内容 | 写入者 |
|------|------|------|--------|
| 全局 | `~/.claude/lessons/` | 工具链/Plugin/Hook/Permission 经验 | lesson-drafter hook 自动起草 + 用户手动 |
| 项目 | `.ai_state/lessons.md` | 业务代码 Pattern/Pitfall/Constraint | compound skill (Sprint Gate 通过后) |

## 文件类型

```
~/.claude/lessons/
├── INDEX.md                              # 主题索引 (curator 维护)
├── README.md                             # 本文件
├── 2026-04-28-codex-permission.md        # ✅ 已确认的 lesson
├── draft-2026-04-28-codex-rescue.md      # 📝 Claude 自动起草, 待用户审阅
└── archive/                              # 7 天未确认的 draft 自动归档
    └── draft-2026-04-21-old-issue.md
```

## 工作流

### Claude 自动起草 (lesson-drafter hook)

工具失败时 (permission denied / 子任务放弃 / hook schema 错 / codex 调用失败) 自动起草 `draft-*.md`，包含：
- 完整命令和报错
- 当前 PACE 状态
- 时间戳
- **空的根因/方案/workaround 段** — 等你补

### 你审阅 draft (`/lesson-curator`)

```
/lesson-curator
```

会列出所有 draft, 你逐个决定:
- **落档**: 改名为 `YYYY-MM-DD-{slug}.md`, 补完根因/方案/workaround
- **丢弃**: 移到 archive/
- **跳过**: 下次再看

### 7 天自动归档

`session-start` hook 每次启动顺手跑 `lesson-archiver`, 把 7 天未改名的 draft 移到 `archive/`。

## R₀ 怎么用

每次 `/vibe-dev` 或新 session, Claude 会:
1. 扫 `INDEX.md` 找命中本任务主题的 lesson 文件
2. 命中 → 读对应文件, 让经验生效

不命中 → 跳过, 不全文扫 (避免 token 爆炸)。

## 你能手动做的事

```bash
# 看待审 draft
ls ~/.claude/lessons/draft-*.md

# 直接读最近一个
cat $(ls -t ~/.claude/lessons/draft-*.md | head -1)

# 立即归档某个 draft (不等 7 天)
mv ~/.claude/lessons/draft-foo.md ~/.claude/lessons/archive/

# 落档一个 draft (改名 + 补内容, 然后跑 curator 重建索引)
mv ~/.claude/lessons/draft-2026-04-28-codex.md ~/.claude/lessons/2026-04-28-codex-permission.md
$EDITOR ~/.claude/lessons/2026-04-28-codex-permission.md
# 然后 /lesson-curator 重建 INDEX.md
```

## 设计哲学

- **append-only 历史**: 已落档的 lesson 不删不改, 历史可回溯
- **draft 不算数**: draft 是 Claude 起草, 用户审阅前不进 INDEX, 不影响 R₀
- **本地优先**: 全部存本地文件, 不上传, 不依赖云
