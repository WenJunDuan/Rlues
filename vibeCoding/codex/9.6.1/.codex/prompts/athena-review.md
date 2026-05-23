# /athena-review (Codex) v9.6.1

有 `.ai_state/_index.md` → 按当前 Path 触发 pace skill 审查阶段。
无 → 快速审查 (Codex 内置 /review)。

焦点: $ARGUMENTS

Codex 端可用工具:
- `/review` (Codex 内置)
- `spawn_agent reviewer` (从 ~/.codex/agents/reviewer.toml 调度)
- `web_search` 查最佳实践
- 不可: /codex:review (那是 CC 侧反向调用)

## 标签规约 (铁律 10 校准报告 / 铁律 11 可逆性加权)

每个 finding 和评分证据必须附 **1 个** 标签:

- `executed` — 我跑了命令 / 读了代码 / 验证了输出 (附 shell 命令输出或 spawn_agent job ID)
- `inspected` — 我查阅了源码或文档但未执行 (附 file:line 或 URL)
- `assumed` — 基于经验/类比的判断, 未验证 (默认低权重)

### 跨边界判定 (铁律 11)

任何涉及以下边界的声明 → **仅接受 `executed` 标签**:

| 边界 | 例子 |
|------|------|
| 生产环境 | "部署到 prod 不会引入回归" |
| Schema 迁移 | "新字段对老数据兼容" |
| 公开 API | "改 endpoint 签名不破老客户端" |
| 数据迁移 | "脚本不丢数据" |
| 安全/权限 | "新路径无授权漏洞" |

附 `inspected` 或 `assumed` → REWORK.

### 在 review-report.md 中的写法 (跨平台格式)

```
## Step 6 评分

| 维度 | 分数 | 证据 | 标签 |
|------|------|------|------|
| Functionality | 4 | src/auth/jwt.ts:42-78 实测通过 | executed |
| Spec Compliance | 4 | design.md L18 vs src/auth.ts:30 | inspected |
| Boundary | 5 | git diff 仅触及 src/auth/, tests/auth/ | executed |
| Craft | 3 | 命名/SRP 检查 (未跑工具) | inspected |
| Robustness | 3 | 边界 case 经验判断, 未实测 | assumed |
```

## 矛盾不折中 (铁律 12)

`/review` (Codex 内置) 与 `spawn_agent reviewer` 给出**竞争方案**时:

- ❌ 不平均、不折中、不"两边都对一点"
- ✅ 二选一 → 在 `reviews/sprint-N.md` 加 **"## Step 7: 矛盾决议"** 段, 显式命名被弃方案 + 给技术理由

模板:

```markdown
## Step 7: 矛盾决议 (铁律 12)

**冲突点**: <一句话描述>

- 方案 A (/review 提出): <描述>
- 方案 B (spawn_agent reviewer 提出): <描述>

**采纳**: <A 或 B>
**弃用**: <B 或 A>
**技术理由**: <为什么, 不是"两边都有道理"; 引用代码行号或测试结果>
**标签**: executed | inspected | assumed
```
