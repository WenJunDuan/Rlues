---
name: athena-migrate
description: 把已装旧版 Athena 升级到 9.9.8 或迁移 .ai_state。用户显式调用时触发；先备份、失败回滚。
---

# athena-migrate — AI 引导迁移 (v9.9.8)

> 不再维护逐版本 migrate 脚本。迁移由 AI 读文档 + diff 智能执行。
> 完整流程见本 skill `references/AI-MIGRATION-GUIDE.md`（与包根 `vibeCoding/{claude,codex}/9.9.8/AI-MIGRATION-GUIDE.md` 同一份）。

## 何时用
用户说"升级到 9.9.8 / 迁移我的 Athena / 迁移 .ai_state 数据"。

## 五步 (升级 9.9.6 → 9.9.8)
1. **备份** `~/.claude` 与 `~/.codex` 到带时间戳目录, 记录回滚路径。
2. **读变更**: 目标包 `RELEASE.md` / `CHANGELOG.md` 9.9.8 段 + `AI-MIGRATION-GUIDE.md`; diff 旧安装 vs `vibeCoding/{claude,codex}/9.9.8`。
3. **应用** (仅动仍等于 9.9.6 默认的 release-owned 值): 版本→9.9.8 · hooks/`REVIEW.md`/templates · 三 stub 角色。不覆盖用户 model/effort/output-style。不做 26-skill 合并。
4. **数据**: `.ai_state` 保留; `reviews/passN.md` 不改写历史; 新 sprint 用 `implementation-review.md`。telemetry 出 Git (`git rm --cached`), 运行时文件进 `.ai_state/.runtime/`。
5. **校验 → 失败回滚**: `python3 vibeCoding/scripts/validate-athena-9.9.8.py`; 出错恢复步骤 1 备份。

## 红线
- 不可逆操作前必须已备份; 绝不 echo/log 密钥; 用户自定义项一律保留。
