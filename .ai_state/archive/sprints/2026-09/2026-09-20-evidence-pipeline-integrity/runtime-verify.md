---
sprint_slug: "2026-09-20-evidence-pipeline-integrity"
verified_at: "2026-09-20T04:15:00Z"
runner: "local"
verdict: "PASS"
---

# Runtime Verify — 证据管道可证性

## 完成条件与停止条件

- required：受控工作树 bundle 在本机 runner 中实际执行新策略经过的真实 hook 路径（pre-bash-guard → evidence-collector → 门禁解析），而不是只跑纯函数。
- PASS：AC1–AC4、AC6 五个场景在 bundle 内全部成功，cleanup 成功。
- FAIL/停止：输入校验、transport、command 或 cleanup 任一 required 层失败即不进入 polish。

## 测试场景

| 场景 | AC | 结果 | 证据 |
|---|---|---|---|
| pipefail 保护的管道经真实 hook 链记 current PASS，失败腿记 fail | AC1 | PASS | run `d896d6e5f6924cb0b45bd362d2cf9a79` |
| 被掩盖的验证命令（管道/`\|\| true`/`;`/`&`/管道接 `\|\|`）名义成功降为 unknown 且带 reason，真实失败仍为 fail | AC2 | PASS | 同 run |
| 14 行策略矩阵在 CC/CX 上判定与 reason 完全一致 | AC3 | PASS | 同 run |
| CC 形状响应（无 `exit_code`）+ PostToolUseFailure 腿；长输出尾部摘要保留 | AC4 | PASS | 同 run |
| 三端 gate-contracts 记录可复制命令与不可采信规则 | AC6 | PASS | 同 run |
| guard 三端字节不变、Pi 三文件字节同一、删 `_shell-lex` 后门禁仍拦 | AC5 | PASS（源码工作区） | 完整套件 39/39；bundle 无 `.git`，不把 git 历史断言伪装成 runtime 通过 |

## 输入与环境绑定

- base commit：`cd5f78d4caee45425c00c492fd71809c38107692`
- input manifest：`b7fe66c48f21df50469839d238f892a1daf7a9782c7b196cbf4e2ca54e1beb39`
- contract（design.md）：`5b78c2f29e3fa8a7fbd0a4739f55944fa01e0c6bdf5a8e344d72bd8d71dba4f4`
- scenario：`0d51e8ddc2cf00959988eb8ebb358e6c0f8fe7867a7ec289e9c07195a577cb33`
- environment：Darwin 27.0.0 arm64 / Python 3.14.3，sha256 `3026948d3d47bc5f147263810e94d15c26a16328b868da5336038a651d733fbf`
- current PASS artifact：`.ai_state/.runtime/q12-evidence-result.json`，run `d896d6e5f6924cb0b45bd362d2cf9a79`，sha256 `aca9b4db566c6be0d6d7af27da0b6d43b436957de48e7280aa773609ea3a304e`
- command 层 exit 0，耗时 3.931s，`blocks_delivery: false`，cleanup 成功。

## 自测自改记录

本轮 runtime 一次通过，无返工。

场景刻意不含 AC5 的 `git diff --exit-code 52ff57eb` 断言：受控 bundle 按协议不含 `.git`，该断言在其中必然报 128。这是场景环境边界而非行为缺口，所以由源码工作区的完整套件承担（39/39 全绿，含 AC5 的 guard 字节、Pi 字节同一与「删 `_shell-lex` 后门禁仍 exit 2」三项）。不把 git 历史断言宣称为 runtime PASS。

上一切片踩过同一个坑（`git check-ignore` 在无 `.git` bundle 中返回 128），本次直接按该经验收窄场景，未产生失败 run。

## Reflect

真实 bundle 证明策略与收集器脱离原工作树后仍按设计判定，且 CC/CX 两端一致。未覆盖安装态 hook —— 设计已把 `~/.claude` / `~/.codex` 同步列为 Non-goal，交给 roadmap 最终发行切片。

外部写者（grok）的施工产物已 ff 合入主仓后才做本次快照，所以 runtime 证据绑定的是主仓 HEAD，不是隔离 worktree 的中间态。

## VERDICT

PASS。required 本机场景、transport 与 cleanup 均通过，可进入 polish。
