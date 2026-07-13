# Athena 9.9.2 — AI 引导安装 / 升级 / 数据迁移指南

> 9.9.2 起, Athena **不再维护逐版本 migrate/setup 脚本**。安装、升级、`.ai_state` 数据迁移一律**推荐由 AI 执行**:
> AI 读 CHANGELOG + 新旧包 `diff`, 智能应用变更并逐一保留用户配置。脚本化迁移脆、易漏字段, 已弃用。

## 为什么用 AI 而非脚本
逐版本 migrate 脚本把"某字段是否仍等于旧默认"硬编码, 版本一多就漂移、漏项、静默改坏用户配置。AI 能读语义 (CHANGELOG 说明了每项改动的意图) + 逐文件 diff, 按意图迁移, 遇歧义停下问, 比死脚本稳。

## 通用红线 (三种场景都遵守)
- **先备份**: 任何不可逆操作前分别备份 CC `~/.claude`、CX `~/.codex` 与 `~/.agents/skills`, 写入带时间戳目录并记录路径。
- **preserve 用户所有权**: 用户 model/effort/env、私有 hook、自定义 provider/MCP/plugin、permissions、trust、未知字段、**任何密钥值** —— 一律保留, 只动仍等于旧默认的 release-owned 值。
- **绝不打印密钥**: 迁移日志不 echo/log 任何 secret value。
- **失败即 rollback / 回滚**: 出错恢复备份, 报告差异, 不留半迁移状态。

## 场景一 · 全新安装 9.9.2
1. 定位包: `vibeCoding/claude/9.9.2/.claude` (CC) 与 `vibeCoding/codex/9.9.2/.codex` (CX)。
2. 精确目标: **CC runtime assets/config → `~/.claude`**；**CX config/hooks/agents → `~/.codex`**；**CX skills → `~/.agents/skills`**。不得把整个 CX `.codex` 包复制到 `~/.agents`。
3. 安装后的 guide: CC `~/.claude/skills/athena-migrate/references/AI-MIGRATION-GUIDE.md`; CX `~/.agents/skills/athena-migrate/references/AI-MIGRATION-GUIDE.md`。若目标已存在同版, 只读校验不覆盖。
4. 校验: 身份行/env 版本 = 9.9.2; skill 数 = 26; 跑 `python3 vibeCoding/scripts/validate-athena-9.9.2.py` (Python 3.11+)。

## 场景二 · 升级旧版 → 9.9.2 (AI 迁移)
读 `CHANGELOG.md` 9.9.2 段, 逐项应用 (仅当用户未自定义):
- 版本标识 → 9.9.2。
- 插件默认: `feature-dev` off · `superpowers` off · `ECC-AgentShield` on。
- release-owned 资产更新: 四原语 (加 MCP)、**spec-gate** 门禁 (delivery-gate)、`references/mcp.md`、两层记忆 `_index` 框架、pace 路由去重。
- **skill 合并 (7→2)**: 删旧 7 目录 (scaffold-page-gen / scaffold-module-gen / db-schema-gen / unit-test-gen / security-test / playwright-e2e / project-data-reader), 装新 2 (**quantum-codegen** / **quantum-data**); CX 同步改 `config.toml` skill 注册。
- 保留: 上面「通用红线」列出的全部用户所有权项。

## 场景三 · 数据 / 状态迁移 (`.ai_state`)
- `.ai_state` schema 9.9.2 **向后兼容**, 无破坏性变更。
- 仅按需把 `_index.md` 补齐两层记忆注释与新字段 (参 `skills/pace/templates/_index.md`)。
- **不删**用户 `sprints/` `compound/` `architecture/` `requirements/` 数据。
- 数据处理迁移 (如批量重构 .ai_state 记录) 同样走 AI: 先备份该目录, diff 预览, 再应用。

## 校验
`node vibeCoding/scripts/test-athena-claude-9.9.2-runtime.cjs` + `python3 vibeCoding/scripts/test-athena-9.9.2-runtime.py` + `python3 vibeCoding/scripts/validate-athena-9.9.2.py` (后两者需 Python 3.11+)。
