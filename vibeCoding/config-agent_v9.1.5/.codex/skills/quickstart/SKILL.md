---
name: quickstart
description: 新手引导
context: main
---
## 触发: 无 .ai_state/ 时

## 步骤
1. 欢迎: "VibeCoding Kernel v9.1.5 — AI 编程协作框架"
2. 检测项目类型 (package.json/Cargo.toml/go.mod/pyproject.toml)
3. 初始化 .ai_state/ (从 templates 复制)
4. 说明:
   - 描述需求即可 (自动路由到合适的工作流)
   - `/review` 审查, `/plan` 规划
   - `codex --profile dev|ci|review` 切换预设
5. 核心: 每个阶段执行前会先走思维协议 (定义→发散→追问→收敛)
