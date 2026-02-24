# VibeCoding Kernel v8.6.1 (Codex CLI)

## 铁律

1. **先搜后写**: 写代码前 `augment-context-engine` 搜现有实现, 不可用时 `grep -r`
2. **先测后交**: 写功能前先写失败测试 (Path A 除外)
3. **寸止不跳**: cunzhi 检查点不可跳过, 不可用时对话确认
4. **状态不丢**: 每阶段完成必须更新 `.ai_state/`
5. **最简实现**: 删到不能再删
6. **Plan-First**: Path B+ 先出计划, cunzhi 确认后再写代码
7. **并行优先**: 无依赖子任务用 collab 并行

## Path A 快速通道

改动 ≤ 20 行、单文件 → 跳 R₀/R/D/P:
1. `augment-context-engine` 确认影响范围
2. 改动 + 测试通过 → commit

不满足 → 读 `.codex/workflows/pace.md` 走 PACE 路由。
Path B+ 进入 R₀b 时**必须**读 `.codex/skills/brainstorm/SKILL.md` 执行苏格拉底式需求精炼。

## Skills & Plugins

以下 skills 默认全部启用 (`.codex/skills/` 目录):
brainstorm, context7, plan-first, tdd, verification, code-quality, debugging,
knowledge, smart-archive, cunzhi, agent-teams, e2e-testing, security-review

Superpowers (如已安装) 与 VibeCoding 互补: VibeCoding 编排流程, Superpowers 提供执行能力。

## 并行工作规范

### 调度流程 (collab 模式)
1. **任务分析**: 识别 plan.md 中的依赖关系图
2. **并行调度**: 无前置依赖的子任务并行执行 (parallel + collab features)
3. **结果汇总**: 等待本轮所有任务完成
4. **递归迭代**: 基于结果重复, 直至 doing.md 全部完成

### 防冲突
子任务之间不共享写入文件。冲突时按先完成者为准。

## 降级通则

MCP 不可用 → 用原生能力完成, 不报错不停顿。
cunzhi 和 `.ai_state` 更新永不跳过。

## 按需加载

启动只读本文件。路由读 `.codex/workflows/pace.md`。
阶段读 `.codex/workflows/riper-7.md`。Skill 按需读。
