# VibeCoding Kernel v8.5 — Codex CLI

> 编排层。不替代模型能力, 只做 WHEN + WHERE + HOW MUCH。并行优先, 串行兜底。

## 铁律

1. **先搜后写**: `augment-context-engine` 搜现有实现, 不可用时 `grep -r`
2. **先测后交**: 写功能前先写失败测试 (Path A 除外)
3. **寸止不跳**: cunzhi 检查点不可跳过, 不可用时对话确认
4. **状态不丢**: 每阶段更新 `.ai_state/`, 经验写 pitfalls.md / patterns.md
5. **最简实现**: 删到不能再删, 跑给我看
6. **Plan-First**: Path B+ 先出计划 (`/plan` 或 `.ai_state/plan.md`), 确认后再写代码
7. **并行优先**: 无依赖的子任务通过 `collab` 并行调度, 不串行等待

## Path A 快速通道

改动 ≤ 20 行、单文件、无架构影响 → 跳 R/D/P:
1. `augment-context-engine` 确认影响范围
2. 改动 + 测试 → 通过 → commit

不满足 → 读 `workflows/pace.md` 走 PACE 路由。

## 并行工作规范

### 调度流程

1. **任务分析**: 识别依赖关系图, 区分可并行节点与串行节点
2. **并行调度**: 无前置依赖的子任务通过 `collab` 同时下发, 确保不写冲突
3. **结果汇总**: 等待本轮所有并行任务返回, 校验一致性
4. **递归迭代**: 基于阶段结果重复 1-3, 直至完成

### 调度策略

- 多文件独立处理 → 并行
- 同一文件多处修改 → 拆分不重叠区域后并行, 或串行
- 有明确前后依赖 → 串行
- 信息收集 + 分析 → 收集并行, 分析汇总后执行
- Path D 多模块 → 每模块一个 collab 并行执行

### 防冲突

collab 子任务之间不共享写入文件 → 按目录/模块划分边界。
冲突发生时: 主代理仲裁, 以先完成者为基准合并。

## 降级通则

Plugin/MCP 不可用 → 用原生能力完成同等目标, 不报错不停顿。
`/plan` 不可用 → 手动输出计划到 `.ai_state/plan.md`。
cunzhi 和 `.ai_state` 更新永不跳过。

## 按需加载

启动只读本文件。路由读 `workflows/pace.md`。阶段读 `workflows/riper-7.md`。
Skill 按需读 `skills/*/SKILL.md`。不预加载, 不全量读取。
