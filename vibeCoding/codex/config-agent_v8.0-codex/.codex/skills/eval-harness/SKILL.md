---
name: eval-harness
description: |
  Evaluation framework for measuring code agent effectiveness.
  v8.0: Added Agent Teams collaboration quality metrics.
---

# Eval Harness Skill

## 评估维度

| 维度 | 指标 | 目标 |
|:---|:---|:---|
| 任务完成率 | done/todo 比例 | >95% |
| 验证通过率 | 首次验证通过比例 | >80% |
| 方案偏离度 | plan vs 实际实现差异 | <10% |
| 返工率 | 需要修复的任务比例 | <15% |
| 寸止响应质量 | 用户一次确认通过比例 | >90% |

## Agent Teams 评估 (v8.0 新增)

| 维度 | 指标 |
|:---|:---|
| 并行效率 | 实际加速比 vs 理论加速比 |
| 协调开销 | 协调 token / 总 token |
| 冲突率 | 文件冲突次数 |
| 合并质量 | 合并后测试通过率 |
