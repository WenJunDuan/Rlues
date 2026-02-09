# RIPER Flow

## 路径映射

| Path | 阶段 |
|:---|:---|
| A | R1 → E → R2 |
| B | R1 → I → P → E → R2 |
| C | R1 → I → P → E → R2 (每步寸止) |
| D | Lead: R1→I→P → Teams: E → Lead: R2 |

## 各阶段 .ai_state 联动

| RIPER | 读取 | 写入 |
|:---|:---|:---|
| R1 | conventions.md, .knowledge/ | - |
| I | R1 分析结果 | plan.md, decisions.md |
| P | plan.md | todo.md |
| E | todo.md | doing.md → done.md |
| R2 | todo.md, done.md | archive.md, experience |
