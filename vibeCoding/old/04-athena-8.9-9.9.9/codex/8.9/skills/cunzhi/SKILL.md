---
name: cunzhi
description: 寸止检查点协议
---
## 检查点
| 检查点 | 阶段 | Path |
|:---|:---|:---|
| [DESIGN_DIRECTION] | R₀b | B+ |
| [DESIGN_READY] | D | B+ |
| [PLAN_CONFIRMED] | P | B+ |
| [MILESTONE_CHECK] | E | C+ |
| [DELIVERY_CONFIRMED] | V | ALL |

优先 cunzhi MCP, 降级对话确认。不可跳过确认本身。

Path A: 只需 [DELIVERY_CONFIRMED]。
Path B: [DESIGN_DIRECTION] + [DESIGN_READY] + [PLAN_CONFIRMED] + [DELIVERY_CONFIRMED]。
Path C+: 全部检查点。
