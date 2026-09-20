---
sprint_slug: "2026-09-20-review-binding-preflight"
verified_at: "2026-09-20T05:40:00Z"
runner: "local"
verdict: "PASS"
---

# Runtime Verify — review binding preflight

## 完成条件与停止条件

- required：受控工作树 bundle 在本机 runner 中实际执行 review-binding CLI 的真实四步与新增子命令，而不是只跑纯函数。
- PASS：AC1–AC5 的 11 个目标场景在 bundle 内全部成功，cleanup 成功。
- FAIL/停止：输入校验、transport、command 或 cleanup 任一 required 层失败即不进入 polish。

## 测试场景

| 场景 | AC | 结果 | 证据 |
|---|---|---|---|
| prepare 把 CLI 自身会写的路径移出存储的 `input_paths` 并记 `excluded_inputs` | AC1 | PASS | run `d35b4c47408a411a87c546613a24cdc7` |
| 声明非空但排除后为空 → 失败；零输入 prepare 仍合法 | AC1 | PASS | 同 run |
| 声明路径漂移指名路径与前后哈希 | AC2 | PASS | 同 run |
| 聚合轴漂移只报轴名，不声称指出文件 | AC2 | PASS | 同 run |
| `evidence_docs` 指名具体文档、`evidence_ids` 指名缺失 id | AC2 | PASS | 同 run |
| 无 `input_hashes` 的旧 row 退回字段名消息并显式说明 | AC2 | PASS | 同 run |
| 过期 `implementation_commit` 在 prepare 即失败 | AC3 | PASS | 同 run |
| 该字段缺失或畸形时跳过预检，行为与今天一致 | AC3 | PASS | 同 run |
| `governance` 与门禁计算一致且两端输出相等 | AC4 | PASS | 同 run |
| `governance` 无 sprint 可用、缺 `_index.md` 时非零退出 | AC4 | PASS | 同 run |
| 既有绑定行去重回归未被破坏 | 范围守护 | PASS | 同 run |
| 门禁差异仅两个导出名、Pi 与 CC 字节同一 | AC5 | PASS（源码工作区） | 完整套件 52/52；bundle 无 `.git`，不把 git 历史断言伪装成 runtime 通过 |

## 输入与环境绑定

- base commit：`baf5d9cd5c7422aa1f63a72aade09dab07f0f1f1`
- input manifest：`cc1b860782cc02600c1c52ed82ced0c310aec639002f98146be42ee4c35a3cc5`
- contract（design.md）：`0d4c90f8fb0d0ac6cd863d30dc5ad0794b6761bbb6379d7e9c2b440bcb160fe8`
- scenario：`ec5a009ef5f02fee1a66758f9dfb21cef66eb0d3df001664207bbc6fc0aa55a5`
- environment：Darwin 27.0.0 arm64 / Python 3.14.3，sha256 `3026948d3d47bc5f147263810e94d15c26a16328b868da5336038a651d733fbf`
- current PASS artifact：`.ai_state/.runtime/q12-review-binding-result.json`，run `d35b4c47408a411a87c546613a24cdc7`，sha256 `3fe15db2b0762b9a848df75caee633a67600a8fd0d03b9944691b700a2e41b40`
- command 层 exit 0，耗时 5.659s，`blocks_delivery: false`，cleanup 成功。

## 自测自改记录

本轮 runtime 一次通过，无返工。

AC5 的 `git show 0ca066c:<gate>` 逐行断言按上两个切片的经验留在源码工作区：受控 bundle 按协议不含 `.git`，该断言在其中必然报 128。这是场景环境边界而非行为缺口，由完整套件承担（52/52，含门禁导出差异与 Pi 字节同一两项）。

## 主 agent 额外现场核实

runtime 之外另跑了一次真实调用，因为 AC4 的全部意义就在这里：

- 从 linked worktree 调用 `governance`，该 worktree 自带一份**内容不同**的 `.ai_state/_index.md`，输出哈希 `c092c488…` 与主仓调用一致，也与门禁 `indexGovernanceSha256` 的权威值一致。证明它读的是门禁会读的那份，不是脚下那份。
- CC 与 CX 两端输出逐字节相同。

## Reflect

真实 bundle 证明新的四步行为与子命令脱离原工作树后仍按设计判定。未覆盖安装态 hook —— 设计已把 `~/.claude` / `~/.codex` 同步列为 Non-goal；用户已单独授权本切片 ship 后执行同步。

外部写者（grok）的产物已 ff 合入主仓后才做快照，故 runtime 证据绑定主仓 HEAD 而非隔离 worktree 的中间态。

## VERDICT

PASS。required 本机场景、transport 与 cleanup 均通过，可进入 polish。
