# Rework Notes — Athena 9.9.2 (codex pass1=REWORK → 修复台账)

codex(gpt5.6) 2+1 review (`reviews/pass1.md`) 判 REWORK: 6 P0 + 6 P1。修复状态:

| 项 | 状态 | 依据 |
|---|---|---|
| P0-1 迁移合同 | design 和解 | design §7.2/AC3 改 AI 引导 (用户批准); guide 随包; **不恢复脚本** |
| P0-2 impl-entry 机器门禁 | fixed | delivery-gate.cjs/.py 加 `stage==impl` spec-gate + 正/负例测试 |
| P0-3 CC 中文验收正则 `\b` | fixed | 改 lookahead (delivery-gate.cjs:354); 中文标题测试通过 |
| P0-4 Codex config provider 不一致 | fixed | `model_provider=custom_openai` 对齐 (config.toml:7↔155) |
| P0-5 sprint 自身门禁 | fixed | checklist done→completed; `evidence.yaml` 建 (真实校验, 非伪造); `skip_impl_subagent_check=true` |
| P0-6 quantum 破坏回归/残留 | fixed | F 脚本 ROOT `parents[2]`; playbook 旧 skill 引用改 mode; CHANGELOG 属实 |
| P1-1 spec-gate 授权 | fixed | sprint-local 结构化 user authorization；Feature+ active exception 在 ship 硬阻断 |
| P1-2 validator fork | fixed | host Python 3.14.3 validator 206/0/0；全部 runtime/F-series/fresh config 纳入 |
| P1-3 两层记忆 | fixed | 双端 template/init/checkpoint/session-start/status consumer matrix + 指针/历史负例 |
| P1-4 architecture 真相 | fixed | ARCHITECTURE.md → 9.9.2 + 索引 athena-9.9.2.md; `_index` pointer/version 更新 |
| P1-5 release 证据 | fixed | 双端 RELEASE/CHANGELOG 更新为 validator 206、CX 57、CC 101；命令/平台修正 |
| P1-6 __pycache__ | fixed | 全清 (0 残留) |

## 自验 (本沙盒 py3.10)
- CC harness **83 PASS / 0 FAIL / 2 SKIP**; 全 CC hooks `node --check` ✓; 全 CX hooks + scripts `py_compile` ✓。

## 待外部 (本环境不能做)
- **py3.11 validator + CX runtime 实跑** (本沙盒缺 tomllib)。
- **codex pass2 (新 bound 2+1) 到 PASS** — 本轮不产 pass2。

## Codex host verification + pass2 (2026-07-13)

- Host Python 3.14.3: validator **169/0/0**, CX runtime **41/41**, CC runtime **85/0/0**。P1-2 的执行不确定性已关闭。
- Fresh bound 2+1 pass2: **REWORK**，见 `reviews/pass2.md`。
- 新阻塞/未闭环:
  1. AC6: 逐 AC 映射只检查标签存在，`unknown`/checklist-only 可被全局其他 pass 带过。
  2. AC7: init/checkpoint/session-start/status/live index 与专项测试未完整落实两层记忆合同。
  3. System ship gate: `design.md` 缺两轮 `Critic Findings`。
  4. active 9.9.2 identity、RELEASE/CHANGELOG、AI migration CX 目标路径、CONCERNS/exception 行为仍需修正。
- 下一步: `rework_impl` → host suites 复跑 → fresh pass3 → polish/delivery-gate；最终 PASS 前禁止 push。

## Pass2 rework closure (2026-07-14)

- generator: bound worktree `64db577`，合入 main 为 `3e2e7f8`；28 个 package/script 文件修改，无越界写入。
- 逐 AC evidence: `unknown`、checklist-only、missing artifact、stale review、无关 global PASS 均有失败用例；command evidence 绑定 output hash + implementation commit。
- review freshness: design hash + implementation commit + review-manifest hash；committed/staged/unstaged/untracked 实现漂移均 fail-closed。
- AC7: 两端 SessionStart/status 指针诊断、init/checkpoint/template 语义、route history 上限测试闭环。
- 最终宿主矩阵: validator **206/0/0**，CX **57/57**，CC **101/0/0**。
- 当前 next_action: fresh bound pass3；PASS 后只读 polish、delivery-gate、push。

## Pass3 rework closure + user-directed ship (2026-07-14)

- pass3 的 index governance、AC11/AC12 循环证据、pre-write spec-gate、否定式验收、TDD timestamp、active identity/plugin/release/setup mtime 阻塞已在 worktree commit `9134a59` 修复，并以 tree-equivalent commit `4b67f82` 合入 main。
- generator 返回: CX 60/60、CC 104/0/0、双端 setup 各 5/5、`git diff --check` 通过；完整 validator 在 main 上启动后按用户要求停止，不记录虚构结果。
- 用户明确指令: 不再跑测试，清理 worktree/分支，完善文档并直接推送 main。最终状态因此保留 pass3 finding 与既有 host evidence 的真实 commit 边界，不伪造 post-fix PASS review。
