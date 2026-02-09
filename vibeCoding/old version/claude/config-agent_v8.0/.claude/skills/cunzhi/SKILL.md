---
name: cunzhi
description: |
  寸止确认机制。通过 cunzhi MCP 工具强制暂停等待用户确认。
  真正的暂停，不是输出文字假装等待。
mcp_tool: cunzhi
---

# 寸止 (Cunzhi) Skill

## 核心原则

寸止 = 真正暂停 + 等待用户确认。不是输出 "请确认" 然后继续。

## 调用方式

```
cunzhi.confirm({
  checkpoint: "PLAN_READY",
  summary: "方案概要...",
  options: ["确认", "修改", "取消"]
})
```

## 寸止点定义

| 检查点 | 触发时机 | Path |
|:---|:---|:---|
| INIT_DONE | vibe-init 完成 | All |
| DESIGN_READY | 方案设计完成 | B/C/D |
| PLAN_READY | TODO 列表生成 | B/C/D |
| PHASE_DONE | 九步某阶段完成 | C |
| TEAM_PLAN | Agent Teams 分配方案 | D |
| TEAM_DONE | 全部 Teammate 完成 | D |
| VERIFY_FAIL | 验证循环3次失败 | All |
| TASK_DONE | 任务全部完成 | All |
| CHECKPOINT | 手动检查点 | All |
| PAUSED | 工作流暂停 | All |

## 降级

cunzhi MCP 不可用时 → 输出 `[CUNZHI]` 标记并请求文字确认。
但这是最后手段，正常情况必须通过 MCP 工具寸止。

## Agent Teams 中的寸止

- Lead Agent: 在分配和合并时必须寸止
- Teammates: 完成时通知 Lead，不直接寸止用户
