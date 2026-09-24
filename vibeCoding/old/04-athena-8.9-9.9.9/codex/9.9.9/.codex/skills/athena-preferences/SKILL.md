---
name: athena-preferences
description: 项目级 Athena 偏好设置 (skip_polish / default_path / 优先工具 / LaaV)。用户显式调用时触发。
disable-model-invocation: true
---

# /athena-preferences — 项目级偏好

## 配置项 (写入 _index.md.frontmatter)

| 字段 | 值 | 说明 |
|---|---|---|
| `skip_polish` | true / false | Refactor/System 路径跳过 polish (不推荐) |
| `default_path` | Hotfix/Bugfix/.../System | 路由失败时的 fallback (default: 主 agent 询问) |
| `preferred_tools` | ["context7", "antigravity", ...] | 工具优先级覆盖 |
| `network_in_polish` | true / false | polish_worker 是否允许 network (default: true) |
| `laav_enabled` | true / false | 打开 `/llm-as-a-verifier` 排序；默认 false，不是 ship 门禁 |
| `skip_runtime_verify` | true / false | 跳过运行时验证 (纯库才设；System/Refactor 不建议) |

## 工作流

主 agent 读用户偏好 → 用 Edit 工具修改 `.ai_state/_index.md` 对应字段.

LaaV 用法见 `../llm-as-a-verifier/SKILL.md`。打开开关不等于已经校准；未配置 logprobs 后端时脚本会 skip。
