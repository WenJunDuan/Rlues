---
name: athena-status
description: >
  Athena 状态面板。显示当前 PACE 状态、Hook 触发计数、claude-mem 状态、plugin 健康。
effort: medium
disable-model-invocation: true
---

# /athena-status (v9.6.1)

实时聚合 Athena 运行状态。无副作用, 只读 (铁律 8 索引先行)。

## 收集顺序

### 1. PACE 状态 (从 _index.md frontmatter)
```bash
node -e '
const fs = require("fs");
const content = fs.readFileSync(".ai_state/_index.md","utf8");
const fm = content.match(/^---\n([\s\S]*?)\n---/);
if (!fm) { console.log("_index.md frontmatter 缺失"); process.exit(1); }
const get = (k) => { const m = fm[1].match(new RegExp("^  " + k + ": (.*)$","m")); return m ? m[1].replace(/^["\x27]|["\x27]$/g,"") : ""; };
console.log("Path:    ", get("path"));
console.log("Stage:   ", get("stage"));
console.log("Sprint:  ", get("sprint"));
console.log("Goal:    ", get("active_goal"));
'
```

### 2. Sprint 进度 (counts 段)
```bash
grep -E "^  (tasks_pending|tasks_done|tasks_blocked):" .ai_state/_index.md
```

### 3. Hook 触发记录 (最近 50 条)
```bash
tail -50 .ai_state/hook-trace.jsonl 2>/dev/null | \
  jq -r '.hook' 2>/dev/null | sort | uniq -c | sort -rn
```

### 4. Lessons 统计 (仅项目级)
```bash
grep "^  lessons_lines:" .ai_state/_index.md
grep "^## " .ai_state/details/lessons.md 2>/dev/null | tail -1
echo "[全局已删除, 跨项目记忆装 claude-mem]"
```

### 5. Platform 健康
```bash
grep "^  cc_version:" .ai_state/_index.md
grep "^  cx_version:" .ai_state/_index.md
grep -E "^  (goal|batch|background)_supported:" .ai_state/_index.md
grep "^  cross_session_memory:" .ai_state/_index.md
```

### 6. Plugin 状态
- codex: `which codex || codex --version 2>&1 | head -1`
- superpowers: `ls ~/.claude/plugins/cache/superpowers/ 2>/dev/null`
- claude-mem: `ls ~/.claude/plugins/ 2>/dev/null | grep -i claude-mem`
- context7: `npx ctx7 --version 2>&1 | head -1`

### 7. v9.6.1 标签使用率 (新)

```bash
# review-report.md 中 executed/inspected/assumed 标签出现频次
grep -hoE "executed|inspected|assumed" .ai_state/details/reviews/sprint-*.md 2>/dev/null | sort | uniq -c
```

判断:
- 3 个标签都 ≥ 5 次 → 校准报告 (铁律 10) 生效
- 仅 executed/inspected, 缺 assumed → 模型不愿承认 assumed
- 仅 assumed → 模型在偷懒不验证, 需要加强 review skill

## 输出格式

```
=== VibeCoding Athena v9.6.1 Status ===

[PACE]    Path: Feature  Stage: impl  Sprint: 3
          Goal: tasks all checked + npm test exits 0

[Tasks]   3 done · 2 pending · 0 blocked

[Hooks]   最近 50 次触发:
  session-start     ✓ 5 注入
  index-updater     ✓ 28 更新
  delivery-gate     ✓ 12 (阻断 2, soft 1)
  pre-bash-guard    ✓ 0 拦截
  pace-continuator  ✓ 5 (next: 5, proposals: 2)
  subagent-retry    ⚠ 3 注入

[Calibration v9.6.1]   (铁律 10)
  executed:   12
  inspected:  8
  assumed:    3

[Platform]
  CC version           ✓ 2.1.140
  CX version           ✓ 0.130
  /goal               ✓ supported (CC v2.1.139+, CX v0.128.0+)
  /batch              ✓ supported (CC only)
  /background         ✓ supported (CC only)
  Session memory      ✓ active
  Cross-session       ✓ claude-mem

[Commands]
  test_cmd: npm test
  build_cmd: npm run build
  lint_cmd: npm run lint
```

纯 Bash + node + jq. 失败的项显示 "✗ 不可用". 不写文件, 不改状态。
