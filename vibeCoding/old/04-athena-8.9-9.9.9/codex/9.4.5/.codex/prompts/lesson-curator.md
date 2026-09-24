# /lesson-curator — 整理 ~/.codex/lessons/

整理全局工具链经验。每周或感觉 draft 堆积时跑一次。

## 任务

### 1. 列出待审 drafts

```bash
ls -la ~/.codex/lessons/draft-*.md 2>/dev/null
```

按创建时间排序, 显示给用户。每个 draft 显示:
- 文件名
- 创建距今天数
- 首段问题简述

### 2. 审阅每个 draft

对每个 draft 与用户对话:

```
draft-2026-04-28-spawn-agent-fail.md (创建 0 天前)
问题简述: spawn_agent reviewer 调用失败

用户操作:
  a) 落档 → 改名为 2026-04-28-{slug}.md, 补全根因/workaround
  b) 丢弃 → 移到 archive/
  c) 跳过 → 下次再看
```

### 3. 7 天自动归档

```bash
find ~/.codex/lessons -maxdepth 1 -name 'draft-*.md' -mtime +7 -exec mv {} ~/.codex/lessons/archive/ \;
```

通知用户哪些被归档了。

### 4. 重建 INDEX.md

扫 `~/.codex/lessons/*.md` (排除 draft- 和 archive/), 按主题重建索引:

```markdown
# Global Lessons Index

## 主题: spawn_agent / 跨 worker 调度
- [2026-04-28] spawn_agent reviewer fail → ./2026-04-28-spawn-agent-fail.md

## 主题: Hooks / Hook 协议 (Codex)
- [2026-04-15] Stop hook continue/stopReason 协议 → ./2026-04-15-stop-hook.md
- [2026-04-10] PostToolUse decision:block 注入 stderr → ./2026-04-10-posttooluse.md

## 主题: Permission / Sandbox
- [2026-04-28] sandbox_mode workspace-write 边界 → ./2026-04-28-sandbox.md

## 文件清单 (按时间倒序)
- 2026-04-28-spawn-agent-fail.md
- ...
```

主题分类靠 lesson 文件 frontmatter 的 `context:` 字段。

### 5. 报告

完成后告知用户:
- 归档了 N 个超期 draft
- 落档了 M 个 draft (列出新文件名)
- INDEX.md 现在 K 条目

## 与 lesson-drafter hook 的关系

- lesson-drafter hook **自动起草** draft-*.md (基于工具失败检测)
- /lesson-curator **由用户触发**, 审阅 draft, 落档或归档
- INDEX.md 由 curator 重建 (drafter 不动 INDEX.md)
