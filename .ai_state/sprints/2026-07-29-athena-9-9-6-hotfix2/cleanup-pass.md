---
sprint_slug: "2026-07-29-athena-9-9-6-hotfix2"
created: "2026-07-29T14:49:00Z"
path: "System"
polish_worker: "主 agent（用户授权 main checkout；只读 polish audit）"
---

# Cleanup Pass — 2026-07-29-athena-9-9-6-hotfix2

## 5 检查项

### 1. 临时代码 / 调试痕迹

- 已检查 hooks、metrics、文档和同步目录；无新增 `console.log`、`debugger`、TODO/FIXME 调试残留。
- 生成的 `.DS_Store`、`.pyc`、`__pycache__` 已从仓库与两端 release-owned 树清理。

### 2. 注释完整性

- evidence collector 的脱敏边界、git re-route 单源、worktree 只读角色和 `verdict_ac2` 代理范围均有注释/文档说明。
- 模板不再复制 gate 正则或内部字段，改由实现与参考文档持有规则。

### 3. 冗余 / 重复代码

- 删除无消费者的 `_hf2_sync` 29 文件镜像；canonical package 是唯一安装源。
- 未新增 adapter、第二状态树或逐动作账本。

### 4. 低效模式

- 普通 prompt/Bash/Edit/MCP 不再产生 raw tool/token/subagent 账本；re-route 改用 git diff/cached/untracked 三探针。
- 本轮 validator、ledger、metrics、边界、脱敏、SQLite 检查均复跑通过。

### 5. 过度设计与过度防御

- 保留的防御仅位于外部输入、凭据、跨进程与 worktree 权限边界；未加新配置开关或扩展点。
- `review-manifest.yaml` 为全路径显式 opt-in；AC9 A/B 不在本 sprint 伪造完成。

## Finishing-a-development-branch

- [x] 运行 validator：`66 PASS / 0 FAIL / 0 SKIP`
- [x] 运行真实 sprint metrics：`verdict_ac2=PASS`（git-scale instrument proxy）
- [x] 运行 W35-W40 source/installed ledger、syntax/config、redaction、worktree boundary、SQLite quick-check
- [x] 用户已指定推送到 `main`；当前 checkout 即 `main`，无 worktree 待清理
- [x] 由于 Fable 实现已存在于 `77b64bb` 且本 sprint 没有 generator 握手记录，`skip_impl_subagent_check=true` 已按用户授权直做路径显式记录，不伪造生命周期
- [x] `_to_delete*` 原路径为空；内容保留在事务备份 `deleted-to-delete/`

## review 意见合并

- 首轮 F1：脱敏模式扩展到 Bearer/AWS/CLI/URL userinfo，并在 canonical/installed 两端复测 → ✅
- 首轮 F2/F3：明确 `verdict_ac2` 是度量代理，设计 AC2 以行为夹具为准，AC9 deferred → ✅
- Spec 首轮：删除 `_hf2_sync`、统一 manifest opt-in、模板收回 gate 内部细节 → ✅；第二轮 MISSING/EXTRA/DEVIATED 均为 0

## 归档到 compound/

- 已沿用现有决策档 `compound/2026-07-28-decision-close-prompt-engineering-direction.md`：不再追加纠结、啰嗦的控制面方向。
- 本 sprint 的新事实已进入 architecture、deployment、runtime-verify 与 session-log；不新增重复 compound 散文。

## VERDICT

**PASS** — 5 项清理完成；System sprint 可进入 ship。AC9 保留为下一 sprint 的独立 A/B gate。
