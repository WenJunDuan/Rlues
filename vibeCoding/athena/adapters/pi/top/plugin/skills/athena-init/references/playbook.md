# athena-init · playbook（Pi）

建 `.ai_state`。默认不探测 CC/CX。重复执行保留已有状态。

## 顺序

1. 已有 `.ai_state/` → 停，提示 `/athena-status`。
2. `git rev-parse --git-dir` 失败 → 停，先 `git init`。
3. 建目录：

```bash
mkdir -p .ai_state/sprints .ai_state/roadmap .ai_state/architecture \
  .ai_state/requirements .ai_state/compound .ai_state/.snapshots
```

4. 复制模板（不覆盖已有 `_index.md`）。模板在本包 `skills/pace/templates/_index.md`（相对 athena-init skill 为 `../pace/templates/_index.md`）：

```bash
# 从已安装的 athena-pace 包内拷；路径随 pi install 落点变化，用 skill 相对路径
cp ../pace/templates/_index.md .ai_state/_index.md
```

5. 探测并写入 `_index` 已有字段（不新造字段）：`rg` / `jq` → `tools_available`；`command -v pi` 有则记下，不当成 `cc_version`。`platforms_enabled` 保持模板，不填假的 CC/CX。
6. 告诉用户：`.ai_state` 已建；下一句任务走 PACE（athena-dev 分诊）。

脚本 `../scripts/init-platforms.py` 只在用户明确要探测 CC/CX 时用。Pi 默认路径不跑它。
