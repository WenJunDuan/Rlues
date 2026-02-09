# vibe-dev

智能开发入口。抛出需求，系统自动完成一切。

## 语法

```
vibe-dev "任务描述"
vibe-dev --path=C "任务描述"
vibe-dev --team "任务描述"
vibe-dev --no-tdd "任务描述"
vibe-dev --worktree "任务描述"
```

## 用户体验

```
你: vibe-dev "给登录页加记住密码功能"

系统:
  → 评估复杂度 → Path B
  → R: "cookie 还是 localStorage？token 有效期？"
  → D: "方案 A: HttpOnly Cookie / 方案 B: localStorage / 推荐 A"
  → P: 拆解 6 个微任务
  → C: [寸止] "确认验收标准：关闭浏览器再打开仍登录？"
  → E: TDD 循环
  → V: 自检
  → Rev: 审查+学习
  → [寸止] 完成
```

**用户只做两件事：回答问题 + 寸止点确认。**

## 内部流程

```
1. 读 .ai_state/session.md + doing.md (铁律 1)
   有未完成 → 提示 vibe-resume
2. sou.search("关键词") → 了解项目
3. 评估复杂度:
   Path A → 执行 CLAUDE.md 内联快速通道 (不加载 workflow)
   Path B+ → 加载 workflows/pace.md → 确定工具激活矩阵
4. Path B+: 加载 workflows/riper-7.md → 按路径执行各阶段
5. 各阶段按调度表加载 skills + plugins + MCP
6. 每次阶段转换 → 更新 session.md (riper_phase + current_task)
```
