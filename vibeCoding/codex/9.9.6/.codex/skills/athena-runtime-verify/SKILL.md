---
name: athena-runtime-verify
description: impl 之后的运行时验证环。System/Refactor 强制；需要实跑接口而非只跑单测时触发。
---

# /athena-runtime-verify — 运行时验证环 (v9.9.6, Codex)

## 触发

| 路径 | 要求 |
|---|---|
| Hotfix / Bugfix / Quick | 默认跳过; fix-note 可含定点实跑 |
| Feature | 外部接口、有状态或多环境时启用 |
| Refactor / System | 强制 |

## 不做

- 不替代 impl 单测或 review
- 不对生产或共享环境做破坏性验证, 除非用户明确授权目标与范围
- 不从本地文件猜账号、密码、cookie 或 token
- 不用人工描述代替可复跑证据

## 详细 playbook

完整工作流、模板、schema 与联动细节见 `references/playbook.md` —— 按需 Read, 不进热路径。
