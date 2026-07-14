---
name: athena-migrate
description: >-
  AI 引导的 Athena 版本迁移 (9.9.2 起弃用脚本化 migrate). 当用户要把已装旧版 Athena 升级到 9.9.3,
  或迁移 .ai_state 数据时触发. AI 读 CHANGELOG + 新旧包 diff 智能应用, 逐一保留用户配置,
  先备份、绝不打印密钥、失败即回滚。
---

# athena-migrate — AI 引导迁移 (v9.9.3)

> 9.9.2 起**不再维护逐版本 migrate 脚本** (脆、易漏字段)。迁移由 AI 读文档 + diff 智能执行。
> 完整流程见本 skill `references/AI-MIGRATION-GUIDE.md` (随包安装; 与仓库包根 `vibeCoding/{claude,codex}/9.9.3/AI-MIGRATION-GUIDE.md` 为同一份, 内容含安装 / 升级 / 数据迁移三场景 + 红线)。

## 何时用
用户说"升级到 9.9.3 / 迁移我的 Athena / 迁移 .ai_state 数据"。

## 五步 (升级旧版 → 9.9.3)
1. **备份** `~/.claude` 与 `~/.agents`(CX `~/.codex`) 到带时间戳目录, 记录回滚路径。
2. **读变更**: 目标包 `CHANGELOG.md` 9.9.3 段 + `AI-MIGRATION-GUIDE.md`; diff 旧安装 vs `vibeCoding/{claude,codex}/9.9.3`。
3. **应用** (仅动仍等于旧默认的 release-owned 值): 版本→9.9.3 · 插件默认 (feature-dev off/superpowers off/ECC on) · 四原语/spec-gate/mcp.md/两层记忆 · **skill 7→2 合并** (删旧 7 装 quantum-codegen+quantum-data, CX 改 config.toml)。
4. **数据**: `.ai_state` schema 兼容, 无破坏性; 仅补 `_index` 两层记忆字段; 不删用户 sprint/compound/architecture。
5. **校验 → 失败回滚**: 跑 validate/runtime; 出错恢复步骤 1 备份。

## 红线
- 不可逆操作前必须已备份; 绝不 echo/log 密钥; 用户自定义项一律保留。
