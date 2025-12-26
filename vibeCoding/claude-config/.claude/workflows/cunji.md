# 寸止协议

## 铁律

1. **禁止直接询问**: 只能通过`寸止`与用户交互
2. **未批准禁止结束**: 必须获得明确确认才能结束

## 调用时机

| 场景 | 必须调用 |
|:---|:---|
| 需求不明确 | ✅ 提供预定义选项 |
| 存在多个方案 | ✅ 展示选项让用户选择 |
| 即将完成任务 | ✅ 请求验收反馈 |
| 遇到无法解决的问题 | ✅ 请求人工介入 |
| Path B/C 数据结构确定 | ✅ 等待批准 |
| 每个Phase完成 (Path C) | ✅ 阶段验收 |

## 调用方式

### 询问选择
```javascript
寸止.ask({
  question: "发现两个可行方案",
  options: [
    "方案A: JWT + Redis",
    "方案B: Session + DB"
  ]
})
```

### 请求确认
```javascript
寸止.confirm({
  summary: "即将修改用户表结构",
  changes: ["添加role字段", "创建索引"],
  action: "继续执行"
})
```

### 反馈结果
```javascript
寸止.feedback({
  summary: "完成用户认证模块",
  changes: ["src/auth.ts", "src/middleware.ts"],
  options: ["验收通过", "需要修改", "继续下一步"]
})
```

### 请求人工
```javascript
寸止.escalate({
  issue: "连续3次执行失败",
  attempts: [...],
  request: "请人工介入"
})
```

## 按Path分布

### Path A
```
R1 → E → R2
           ↑
         寸止验收
```

### Path B
```
R1 → I → P → E → R2
     ↑           ↑
   寸止确认   寸止验收
```

### Path C
```
R1 → I → P → E(Phase1) → E(Phase2) → ... → R2
     ↑   ↑       ↑           ↑              ↑
   寸止  寸止   寸止        寸止          寸止
```

## 禁止行为

```
❌ 直接在对话中询问用户
❌ 自行决定多方案中的选择
❌ 未经确认结束对话
❌ 假设用户意图
```
