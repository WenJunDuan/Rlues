---
sprint_slug: "2026-09-24-s6-install-doctor"
path: "Feature"
created: "2026-09-24"
roadmap: "athena-10-1"
item: "s6-install-doctor"
branch: "athena-10.1"
base_commit: "04df01e"
---

# Design — S6 · athena install / rollback / doctor

> 设计真相：`roadmap/athena-10-1/design.md` §11.1–11.2（D9：核心 ~/.athena/<ver> + current 软链）。

## 方案

- `gate/cli/{install,rollback,doctor}.cjs` + `cli/lib/{install-plan,install-apply,legacy-999}.cjs`。
- 来源：已构建 dist（`athena/<rel>` 核心、`claude|codex|pi/<rel>`），逐文件按 manifest sha 校验，缺/改即拒（AC4）；核心必需资产清单（hook/core/cli/shell-lex/…）。
- 落点：核心 → `~/.athena/<rel>/`、`current` → `<rel>`、`~/.athena/bin/athena` 垫片；CC `.claude/**` → `~/.claude/**`；CX `.codex/skills/**` → `~/.agents/skills/**`、其余 → `~/.codex/**`；Pi 包 → `~/.athena/<rel>/pi/`（`pi install` 由用户执行，待验证）；发行说明 → `~/.athena/<rel>/docs/`。
- 合并：settings.json（用户键保留、Athena/9.9.9 hook 条目替换、deny 并集、插件补缺、版本 env）；CX hooks.json 同 hook 合并；config.toml 只写 `[shell_environment_policy.set] VIBECODING_VERSION`（无文件时渲染模板）。
- 9.9.9 残留：`legacy-999.cjs`（由冻结 9.9.9 树生成的 300 个受管路径）中 10.1 不再安装的 → 移入 `~/.athena/backups/<ts>/`。
- 事务：每个被替换/移走/新建的文件先记入 `backup.json`；中途失败自动还原；`rollback` 用同一记录还原并恢复 current。
- 退役：删 `athena-setup/scripts/setup-athena.py`、其测试与 `athena-migrate` skill；`athena-setup` SKILL.md 改为 CLI 说明；RELEASE.md 顶部加 10.1 升级说明。

## 验收标准

- AC1: install / rollback / doctor 可用；配置合并保留用户键与用户 hook，Athena hook 全部指向 `~/.athena/current/hook.cjs`。
- AC2: 临时 HOME：9.9.9 → install 10.1 → doctor 零漂移 → 篡改一个受管文件 doctor 报 drift → rollback → HOME 与 9.9.9 逐字节一致；重装两次后回滚回到第一次安装的状态。
- AC3: setup-athena.py、athena-migrate skill 退役，RELEASE.md 有迁移说明；harness-patches.md 由 migrate 移入 archive/legacy（S4 已做）。
- AC4: dist 资产缺失或被改 → install 失败且 HOME 零写入。

## 不做

Pi 包自动注册（S7 已取消）；发布到 origin（S9 需授权）。
