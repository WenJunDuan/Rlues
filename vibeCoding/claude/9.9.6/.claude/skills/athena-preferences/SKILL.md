---
name: athena-preferences
description: 项目级 Athena 偏好设置 (skip_polish / default_path / 优先工具)。用户显式调用时触发。
# v9.9.6: 副作用 skill — 只允许用户显式 /调用; 描述也不进常驻 catalog
disable-model-invocation: true
---

# /athena-preferences — 项目级偏好

## 配置项 (写入 _index.md.frontmatter)

| 字段 | 值 | 说明 |
|---|---|---|
| `skip_polish` | true / false | Refactor/System 路径跳过 polish (不推荐) |
| `default_path` | Hotfix/Bugfix/.../System | 路由失败时的 fallback (default: 主 agent 询问) |
| `preferred_tools` | ["context7", "antigravity", ...] | 工具优先级覆盖 |
| `network_in_polish` | true / false | polish_worker 是否允许 network (default: true 查最佳实践) |

## 工作流

主 agent 读用户偏好 → 用 Edit 工具修改 `.ai_state/_index.md` 对应字段.
