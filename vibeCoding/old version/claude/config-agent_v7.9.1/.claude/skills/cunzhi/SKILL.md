---
name: cunzhi
description: |
  寸止协议 - Pause and wait mechanism using cunzhi MCP for human confirmation
  at critical decision points. Prevents AI from proceeding autonomously past
  important checkpoints.
hooks:
  PreToolUse:
    - matcher: "tool == 'Write' && phase in ['design', 'implement']"
      command: "echo 'Approaching cunzhi point'"
---

# 寸止 (Cunzhi) Protocol

## Concept

寸止 = "Stop at the inch" - Pause execution at critical points for human review.

Uses **cunzhi MCP** for interactive confirmation.

## Cunzhi Points

| Point | When | Purpose |
|:---|:---|:---|
| `[REQ_READY]` | 需求分析完成 | 确认理解正确 |
| `[DESIGN_READY]` | 方案设计完成 | 确认技术方案 |
| `[PLAN_READY]` | 计划制定完成 | 确认执行计划 |
| `[PHASE_DONE]` | 阶段执行完成 | 确认继续下一阶段 |
| `[RELEASE_READY]` | 准备发布 | 确认发布 |
| `[TASK_DONE]` | 任务完成 | 确认归档 |

## MCP 调用方式

### 确认请求
```javascript
mcp__cunzhi__confirm({
  point: "PLAN_READY",
  title: "计划确认",
  content: `
## 执行计划摘要

1. 创建 auth 模块
2. 实现 JWT 验证
3. 添加单元测试

预计时间: 2小时
  `,
  options: [
    { id: "continue", label: "继续执行", default: true },
    { id: "modify", label: "修改计划" },
    { id: "cancel", label: "取消任务" }
  ]
})
```

### 处理响应
```javascript
switch (response.choice) {
  case "continue":
    // 继续执行下一阶段
    break;
  case "modify":
    // 回到规划阶段
    break;
  case "cancel":
    // 终止任务，保存状态
    break;
}
```

## Fallback (无 MCP)

当 cunzhi MCP 不可用时，使用文本确认：

```markdown
---
🛑 **[PLAN_READY]** 寸止等待确认

## 计划摘要
[内容]

请输入选择:
- `继续` 或 `c` - 执行计划
- `修改` 或 `m` - 调整后重新规划  
- `取消` 或 `x` - 终止任务
---
```

## Rules

1. **必须等待** - 不可跳过寸止点
2. **明确输出** - 清晰展示等待内容
3. **选项明确** - 提供清晰的下一步选项
4. **状态保存** - 等待前保存当前状态

## 集成场景

### 需求审查
```javascript
await cunzhi.confirm({
  point: "REQ_READY",
  content: formatRequirement(req),
  options: ["确认理解正确", "需要澄清", "重新描述"]
});
```

### 方案审查
```javascript
await cunzhi.confirm({
  point: "DESIGN_READY", 
  content: formatDesign(design),
  options: ["批准方案", "调整设计", "换方向"]
});
```

### 发布确认
```javascript
await cunzhi.confirm({
  point: "RELEASE_READY",
  content: formatReleaseNotes(release),
  options: ["确认发布", "延迟发布", "取消"]
});
```

## 与 RIPER 集成

| RIPER Phase | Cunzhi Point | Trigger |
|:---|:---|:---|
| Research → Innovate | REQ_READY | 需求分析完成 |
| Plan → Execute | PLAN_READY | 计划制定完成 |
| Execute → Review | PHASE_DONE | 每阶段完成 |
| Review → Done | TASK_DONE | 任务完成 |
