---
effort: low
---
# Scaffolder Agent — 项目初始化

## 流程
1. 检测项目类型 (Node/Python/全栈)
2. 创建 `.ai_state/` + JSON 模板 + md 模板
3. 生成 init.sh (启动 + 基线验证)
4. 检查并引导安装核心插件:
   ```
   /plugin install gsd@gsd-build
   /plugin install codex@openai-codex
   /codex:setup
   ```
5. 已有项目 → `/gsd:map-codebase`
6. 初始化 git (如未初始化)
