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
| P1-1 spec-gate 授权 | fixed | exception 需 reason+authorized_by+expiry; 占位符语义拒绝 |
| P1-2 validator fork | 部分 | 基线/天花板/62→52/guide 路径/config/F 系纳入 已修; **待 py3.11 复跑确认 0 FAIL** |
| P1-3 两层记忆 | 部分 | 模板 + 部分 init/status; 深化待续 |
| P1-4 architecture 真相 | fixed | ARCHITECTURE.md → 9.9.2 + 索引 athena-9.9.2.md; `_index` pointer/version 更新 |
| P1-5 release 证据 | fixed | 数字 71→83/0/2; CX RELEASE 平台修正 |
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
