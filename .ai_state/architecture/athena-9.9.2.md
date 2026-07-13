# Athena 9.9.2 架构现状

## 双内核
- **pace** = 控制平面 (路由/stage/门禁/恢复)。
- **.ai_state** = 数据平面 (需求/设计/证据/评审/架构/复利; Tier2 持久, _index 检索路由)。

## 四原语 (执行机制)
Workflow 统领 (PACE) · SubAgent 执行 (红黄绿区) · Skill 赋能 (what/知识) · MCP 连接 (reach/外部)。

## 门禁 (fail-closed)
delivery-gate (双端): generator 生命周期 · checklist · evidence 分流 · passN PASS-only · runtime-verify · **spec-gate (impl-entry 提示 + ship 机器复核)** · cleanup · architecture · design-newer-than-review。

## skills 布局 (26)
Athena 核心 (athena-* / pace / brainstorm / roadmap / polish / compound / context7 / playwright / deps-check / biz-delivery-loop) + **quantum-codegen** (前后端生成 6 合 1, mode 分发) + **quantum-data** (运行期数据读取)。

## 安装/迁移
AI 引导 (AI-MIGRATION-GUIDE.md); 脚本化 migrate 弃用; setup 脚本为可选后备。

## 双端
CC (.claude, .cjs, settings.json) ↔ CX (.codex, .py, config.toml + AGENTS.md/standards)。语义对称, 工具不对称 (允许的不对称已记 CHANGELOG)。
