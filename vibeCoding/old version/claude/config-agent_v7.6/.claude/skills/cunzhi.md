# 寸止协议 (Stop & Confirm)

> 核心机制：让 AI 真正暂停等待用户确认

---

## 工具优先级

```
优先使用: cunzhi MCP
降级使用: mcp-feedback-enhanced

IF cunzhi 可用:
  使用 cunzhi
ELSE IF mcp-feedback 可用:
  使用 mcp-feedback
ELSE:
  输出文字等待（最后手段）
```

---

## 寸止点定义

| Token | 触发时机 | 选项 |
|:---|:---|:---|
| `[PLAN_READY]` | TODO 生成完 | 确认/修改/取消 |
| `[DESIGN_FREEZE]` | 架构设计完 | A/B/讨论 |
| `[PHASE_DONE]` | 阶段完成 | 继续/暂停/问题 |
| `[TASK_DONE]` | 全部完成 | 通过/问题/优化 |
| `[VERIFICATION_FAILED]` | 验证失败3次 | 重试/跳过/中止 |
| `[CLARIFY]` | 需求有歧义 | 等待澄清 |

---

## cunzhi MCP 调用

```javascript
// 使用 cunzhi MCP
await cunzhi.pause({
  token: "[TASK_DONE]",
  summary: "工作流完成",
  content: `
    ## TODO 核对
    - [x] T-001 ✅
    - [x] T-002 ✅
    
    ## 统计
    总用时: 2h
    
    ## 变更
    +100/-20 行
  `,
  options: ["通过", "问题", "优化"]
})

// 等待用户响应
const response = await cunzhi.waitForResponse()

// 根据响应处理
switch (response) {
  case "通过": archive(); break;
  case "问题": createFixTodo(); break;
  case "优化": createOptimizeTodo(); break;
}
```

---

## mcp-feedback 调用（降级）

```javascript
// 使用 mcp-feedback-enhanced
await feedback.request({
  type: "confirmation",
  message: `
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📋 [TASK_DONE] 工作流完成
    
    [核对内容]
    
    请选择: 通过 / 问题 / 优化
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  `
})

const response = await feedback.getResponse()
```

---

## 输出格式

```markdown
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 [TOKEN] 标题

## 主要内容
[核对清单/设计方案/统计等]

## 选项
1. 选项A - 说明
2. 选项B - 说明
3. 选项C - 说明

请选择：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 禁止行为

- ❌ 只输出文字不调用工具
- ❌ 不等待用户响应就继续
- ❌ 跳过寸止点
- ❌ 猜测用户会选什么

---

## 检查清单

- [ ] 调用了 cunzhi 或 mcp-feedback
- [ ] 输出了完整的状态摘要
- [ ] 提供了明确的选项
- [ ] 等待并获取了用户响应
- [ ] 根据响应执行了后续操作
