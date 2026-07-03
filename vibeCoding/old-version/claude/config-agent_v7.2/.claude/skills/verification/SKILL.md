---
name: verification
description: 验证回路，质量保障核心
---

# Verification Skill

> **这是质量提升2-3倍的核心原则** — Boris Cherny
> **如果AI不能验证自己的工作，质量就不稳定。**

## 核心理念

验证回路是确保代码质量的关键。不是"写完代码就结束"，而是"验证通过才算完成"。

## 验证流程

```
┌─────────────────────────────────────────┐
│           Verification Loop             │
├─────────────────────────────────────────┤
│                                         │
│  Execute ──→ Verify ──→ Pass? ──→ Done  │
│                 │                       │
│                 ↓ No                    │
│            Analyze                      │
│                 │                       │
│                 ↓                       │
│              Fix                        │
│                 │                       │
│                 ↓                       │
│         Retry (max 3)                   │
│                 │                       │
│                 ↓ Fail                  │
│         寸止: 人工介入                   │
│                                         │
└─────────────────────────────────────────┘
```

## 验证类型

### 1. 功能验证
```markdown
- [ ] 代码修改是否生效？
- [ ] 功能是否按预期工作？
- [ ] 边界情况是否处理？
```

### 2. 测试验证
```markdown
- [ ] 单元测试通过？
- [ ] 集成测试通过？
- [ ] 相关测试没有回归？
```

### 3. 构建验证
```markdown
- [ ] 编译/构建成功？
- [ ] 无类型错误？
- [ ] 无Lint警告？
```

### 4. 运行时验证
```markdown
- [ ] 应用能正常启动？
- [ ] 关键流程可用？
- [ ] 无控制台错误？
```

## 自我修复循环

```javascript
async function executeWithVerification(task) {
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      // 执行任务
      const result = await execute(task);
      
      // 验证结果
      if (await verify(result)) {
        return result; // 成功
      }
      
      // 分析失败原因
      const analysis = await analyze(result);
      
      // 修复
      task = await fix(task, analysis);
      
    } catch (error) {
      if (attempt === 3) {
        // 请求人工介入
        await 寸止.escalate({
          issue: "验证失败，已重试3次",
          attempts: attempts,
          request: "请人工介入"
        });
      }
    }
  }
}
```

## 验证清单

### 修改代码后
```markdown
1. 读取修改后的代码，确认变更正确
2. 运行相关测试
3. 检查没有破坏其他功能
4. 更新任务状态
```

### 提交前
```markdown
1. 所有测试通过
2. 无类型错误
3. 无Lint警告
4. 功能验证通过
5. 更新 .ai_state/active_context.md
```

## 验证日志

记录到 `.ai_state/active_context.md`:

```markdown
## 📝 验证日志

### [日期] T-001: 用户登录
- **状态**: ✅ 通过
- **测试**: 5/5 通过
- **验证方式**: 单元测试 + 手动验证
- **证据**: [截图/日志]
```

## 与Stop Hooks集成

```markdown
验证失败3次 → 触发 [VERIFICATION_FAILED]
             → 寸止请求人工介入
             → 等待用户决策
```

## 使用方式

```javascript
// 加载验证技能
skill.load("verification");

// 执行带验证的任务
verification.execute(task);

// 验证修改
verification.verify(changes);

// 记录验证结果
verification.log(result);
```
