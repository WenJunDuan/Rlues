---
name: quickstart
description: 新手引导 — 首次使用 VibeCoding 的引导流程
context: main
---
## 触发: 无 .ai_state/ 目录时

## 步骤
1. 欢迎: "VibeCoding Kernel v9.1.5 — AI 编程协作框架"
2. 检测项目类型 (package.json/Cargo.toml/go.mod/pyproject.toml)
3. 引导执行 /vibe-init 初始化
4. 说明:
   - `/vibe-dev {需求}` — 开始开发 (自动路由到合适的工作流)
   - `/vibe-status` — 查看进度
   - `/vibe-resume` — 中断恢复
5. 核心提示: 每个阶段执行前, agent 会先走思维协议 (定义→发散→追问→收敛), 确保想清楚再动手

## 原则: 不解释内部机制 (RIPER/PACE), 只告诉用户怎么用
