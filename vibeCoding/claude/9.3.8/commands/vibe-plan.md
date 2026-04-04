# /vibe-plan — 需求分析与规划

只走规划流程, 不写代码。产出: design.md + feature_list.json + plan.md。

## 流程

1. 初始化检查: .ai_state/ 不存在 → @scaffolder 初始化
2. 触发 plan skill (R₀ + R + D + P)
3. 完成后告知用户: "规划完成。用 /vibe-work 开始执行, 或用 /vibe-dev 全流程。"

## 用法

```
/vibe-plan 用户管理模块: 注册、登录、个人资料、密码重置
/vibe-plan $ARGUMENTS
```
