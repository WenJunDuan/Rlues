# /vibe-dev — 完整开发流程 (引导式)

这是 VibeCoding 的主入口命令。适合粗通 vibe coding 的用户。

## 流程

1. **理解需求**: 你说了什么? 需求清晰吗? 不清晰就追问。
2. **初始化检查**: .ai_state/ 存在吗? 不存在 → 先调 @scaffolder 初始化。
3. **RIPER-PACE 路由**: 触发 riper-pace skill, 评估复杂度, 选择 Path。
4. **按 Path 执行**:
   - Path A: 直接进 execute skill → review skill
   - Path B+: plan skill → execute skill → review skill
5. **交付**: review PASS 后归档, 告知用户完成。

## 用法

```
/vibe-dev 做一个用户登录功能，支持邮箱+密码注册和登录
/vibe-dev 修复 #42 bug: 搜索结果分页不正确
/vibe-dev 重构 src/auth/ 模块，从 JWT 迁移到 session-based
```

$ARGUMENTS 是用户的需求描述。如果为空, 问用户: "你想做什么?"

## 新手引导

如果用户看起来不熟悉 (如需求非常模糊), 在开始前简短说明:
"我会按以下流程帮你: 先理解需求 → 设计方案 → 你确认 → 写代码 → 审查 → 交付。过程中需要你确认几个关键节点。"
