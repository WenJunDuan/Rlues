---
name: athena-review
description: PACE review stage 执行 skill (Claude Code). reviewer 与 spec-compliance 并行只读返回, 主 agent 合并 passN.md 后再运行 evaluator, 最终由主 agent 落盘 VERDICT 与 next_action.
---

# /athena-review — Review stage (v9.9.2)

## 触发

impl 完成、checklist 全绿、测试通过; Refactor/System 还须先完成 runtime-verify.

## 工作流 (2 + 1)

1. 主 agent 用 CC 当前 subagent 机制并行运行 reviewer 与 spec-compliance.
2. 两个 read-only agent 只返回完整 markdown 段, 不创建或修改文件.
3. 主 agent 收齐结果, 串行写入 `sprints/{current_sprint_slug}/reviews/passN.md`.
4. 主 agent 再运行 evaluator; evaluator 读取已合并的 passN.md、design、checklist 与 evidence, 返回 Evidence Cross-Check + VERDICT.
5. 主 agent 追加 evaluator 结果并更新 `_index.next_action`.

## VERDICT

| VERDICT | 下一步 |
|---|---|
| PASS | polish (Refactor/System) 或 ship |
| CONCERNS | 修复或明确 defer 后生成 passN+1; 不得直接 ship |
| REWORK / FAIL | 回 impl, 修复后生成 passN+1 |

## 门禁

ship 时 delivery-gate 选择数字最大的 passN.md, 只接受最终 PASS，并检查 Spec Compliance、Evidence Cross-Check (Refactor/System) 与 reviewer/evaluator 结果. agent 启动记录不能代替返回结果或落盘产物.

## 禁止

- reviewer/spec-compliance/evaluator 并发写同一文件
- evaluator 早于前两份结果合并
- read-only agent 更新 `_index.md`
- 主 agent 伪造 agent findings; 主 agent 只负责合并、去重与落盘

## 例外

- Hotfix: 可跳过 review
- Bugfix / Quick: 仅 reviewer
- Feature / Refactor / System: 完整 2+1 流程
