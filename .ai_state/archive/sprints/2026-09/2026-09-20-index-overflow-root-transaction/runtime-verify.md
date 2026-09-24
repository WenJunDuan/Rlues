---
sprint_slug: "2026-09-20-index-overflow-root-transaction"
verified_at: "2026-09-20T01:52:54Z"
runner: "local"
verdict: "PASS"
---

# Runtime Verify — 根级 index overflow

## 完成条件与停止条件

- required：受控工作树 bundle 在本机 runner 中实际执行 CC/CX bounds 行为。
- PASS：四分支 pointer、混合端并发、崩溃恢复、原文保留和二次 no-op 全部成功，cleanup 成功。
- FAIL/停止：输入、transport、command 或 cleanup 任一 required 层失败即不进入 polish。

## 测试场景

| 场景 | AC | 结果 | 证据 |
|---|---|---|---|
| route/current-state/history/body 根 pointer 与无 sprint overflow | AC1、AC2 | PASS | run `517a8e9d272847f7b73abfe112022018` |
| CC+CX 同锁并发保存两份原文并生成唯一 heading | AC3 | PASS | 同 run，`test_mixed_platform_concurrent_bounds_preserve_both_payloads` |
| overflow-before-index 崩溃恢复、no-op、不可读原文保护 | AC3 | PASS | 同 run，其余 3 个定向场景 |
| 模板和 Git ignore 静态合同 | AC4 | PASS（源码工作区） | impl 单测 33/33；bundle 无 `.git`，不伪装成 runtime 检查 |

## 输入与环境绑定

- base commit：`7b3f1b49e9bc81f96a44ad81d0c5ce7ede395be3`
- current input manifest：`ea9505330652737f8b2f9805ab9fad501afcbc39b08e4b5b647c15da15774ec5`
- contract：`a5fa8c5905386787cfb2999c597fb02afa105f09f62416df16d74aa3042486e5`
- scenario：`38048b9eaaa3335618d27e66bb553206f570d6c434f83d0f66035902e154b981`
- environment：Darwin 27.0.0 arm64 / Python 3.14.3，sha256 `3026948d3d47bc5f147263810e94d15c26a16328b868da5336038a651d733fbf`
- current PASS artifact：`.ai_state/.runtime/q12-index-overflow-reviewed-fix-result.json`，run `96ee729e97ca44c6afebadad48b97878`，sha256 `c7c41c86a5355d58e9b44879d240668a71cadf965f9c3701e4c68b32dabb25da`

## 自测自改记录

首次 run `2f981ffa24f44d5ea28dc27e27e4e709` 为 `command_failed`：完整单测中的 `git check-ignore` 在按协议不含 `.git` 的受控 bundle 中返回 128。失败 artifact 保留为 `.ai_state/.runtime/q12-index-overflow-result.json`，sha256 `3dfdabf4f84c1ac0c21b008cd69ee772d82e574a6e88cf1066f857ca45942edc`。

该失败属于场景环境边界，不是 bounds 行为失败。第二次只收窄 runtime 场景到实际可运行的五个 hook 行为；未修改实现，也未把 Git ignore 检查宣称为 runtime PASS。源码工作区完整 33 项测试继续覆盖 AC4。

polish 调整了并发测试的确定性后重新 snapshot；current run `647c13b7eae847ddbdf2e98ad61d4fa2` 在新 manifest 上 5/5 PASS，旧 PASS `517a8e9d272847f7b73abfe112022018` 不再作为当前输入证据。

implementation review 的两项 P2 只修改测试证明：使用真实 contender 锁文件和 `check-ignore --no-index` + tracked 断言。修订后 current run `96ee729e97ca44c6afebadad48b97878` 5/5 PASS；它取代先前 polish run 作为当前证据。

## Reflect

真实 bundle 证明 CC/CX 实现与并发锁在脱离原工作树后仍运行。未覆盖安装态 hook；设计已将安装同步留给 roadmap 最终发行切片。历史 sprint overflow 明确不迁移。

## VERDICT

PASS。polish 后的 required local scenario、transport 与 cleanup 均通过，可进入独立 review。
