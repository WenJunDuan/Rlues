---
name: athena-migrate
description: 用所选端基线将 Athena 升到 9.9.9，预览、逐文件备份、保留覆盖并支持回滚。
disable-model-invocation: true
---

# athena-migrate — AI 引导迁移 (v9.9.9)

> 不再维护逐版本 migrate 脚本。迁移由安装器 `--migrate` + 本 skill 文档执行。
> 完整流程见 `references/AI-MIGRATION-GUIDE.md`（与包根 `vibeCoding/{claude,codex}/9.9.9/AI-MIGRATION-GUIDE.md` 同一份）。

## 何时用

用户说"升级到 9.9.9 / 迁移我的 Athena / 迁移 .ai_state 数据"。全新安装走 `/athena-setup`。

## 五步 (升级 9.9.8 → 9.9.9)

1. **预览** 受管路径，不打印配置值。确认用户 model/effort/provider/权限/第三方 hooks/skills 会保留。
2. **读变更**: 目标包 `RELEASE.md` + `AI-MIGRATION-GUIDE.md`；diff 旧安装 vs `vibeCoding/{claude,codex}/9.9.9`。
3. **应用**:
   ```bash
   python3 vibeCoding/codex/9.9.9/.codex/skills/athena-setup/scripts/setup-athena.py \
     --repo-root "$PWD" --only cc --migrate --dry-run
   python3 vibeCoding/codex/9.9.9/.codex/skills/athena-setup/scripts/setup-athena.py \
     --repo-root "$PWD" --only cc --migrate
   ```
   事务逐文件备份到 `~/.athena/backups/<id>`。成功后安装器删除更早的安装器备份。`.ai_state` 历史不重写。
4. **数据**: `reviews/passN.md` 不改写历史；新 sprint 用 `implementation-review.md`。`REVIEW.md` 现位于 `skills/athena-review/REVIEW.md`，不再安装 `~/.claude/REVIEW.md`。旧 `["both"]` 可读，新写 `["cc"]` / `["cx"]` / `["cc","cx"]`。
5. **校验 → 失败回滚**: `python3 vibeCoding/scripts/validate-athena-9.9.9.py`（不安装进真实 HOME）；出错：
   ```bash
   python3 .../setup-athena.py --rollback ~/.athena/backups/<id>
   ```

## 红线

- 不可逆操作前必须已备份；绝不 echo/log 密钥；用户自定义项一律保留。
- 不删除 sessions / history / file-history / projects。
- 不把已装 9.9.8 当 9.9.9 包的来源。
