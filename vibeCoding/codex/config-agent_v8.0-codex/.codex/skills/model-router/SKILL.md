---
name: model-router
description: |
  Intelligent task-to-model routing based on benchmark data.
  Routes tasks to Claude Code or Codex CLI based on task type
  and model strengths. New in v8.0.
---

# Model Router Skill

## 路由矩阵

基于 2026-02 Benchmark 数据驱动的路由决策：

| 任务类型 | 首选 | 理由 | 降级 |
|:---|:---|:---|:---|
| 终端密集型操作 | **Codex** | Terminal-Bench 77.3% > 65.4% | Claude |
| 复杂 Bug 诊断 | **Claude** | OpenRCA 34.9%, 推理更深 | Codex |
| 多语言代码修复 | **Codex** | SWE-Bench Pro 领先，token 更省 | Claude |
| 架构设计/评审 | **Claude** | ARC AGI 68.8%, 推理深度 | 不降级 |
| 前端 UI 实现 | **Codex** | 25%更快 + chrome-devtools | Claude |
| 文档/知识工作 | **Claude** | GDPval-AA 1606 Elo | 不降级 |
| 安全审查 | **双引擎** | 两者互补 | 单引擎 |
| 长上下文任务 | **Claude** | MRCR v2 76% vs 18.5% | 拆分任务 |

## 自动路由逻辑

```
任务输入 → 分类
  │
  ├─ 涉及终端/脚本/CLI?
  │   → Codex CLI
  │
  ├─ 涉及前端 UI + 需要实时调试?
  │   → Codex CLI (chrome-devtools)
  │
  ├─ 涉及架构决策/复杂推理?
  │   → Claude Code (effort=max)
  │
  ├─ 涉及文档/分析/知识工作?
  │   → Claude Code
  │
  ├─ 涉及安全审查?
  │   → 双引擎并行 (Agent Teams)
  │
  └─ 其他?
      → 当前平台默认
```

## 交叉验证模式

`vibe-verify --cross` 触发：

```
Claude 实现 → Codex 审查 → 差异报告
Codex 实现 → Claude 审查 → 差异报告
```

利用模型差异化能力提高缺陷发现率。

## 降级策略

| 条件 | 动作 |
|:---|:---|
| 目标模型不可用 | 使用当前平台继续 |
| 连续 2 次执行失败 | 切换到备选模型 |
| API 限流 | 队列等待或降级 |

所有降级决策记录到 `.ai_state/decisions.md`。
