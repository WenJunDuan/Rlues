# Model Router Agent (v8.0 新增)

## 职责
根据任务类型自动选择最优模型 (Claude / Codex)。

## 加载 Skills
- model-router

## 决策依据
基于 Benchmark 数据：
- Terminal 密集 → Codex (77.3% > 65.4%)
- 复杂推理 → Claude (ARC AGI 68.8%)
- 知识工作 → Claude (GDPval 1606)
- 前端调试 → Codex (chrome-devtools)

## 降级
目标模型不可用 → 当前平台继续。
