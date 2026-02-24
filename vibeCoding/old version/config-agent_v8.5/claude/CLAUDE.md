# VibeCoding Kernel v8.5

> 编排层。不替代 Superpowers、不重复 Plugin 能力、只做 WHEN + WHERE + HOW MUCH。

## 铁律

1. **先搜后写**: 写代码前 `augment-context-engine` 搜现有实现, 不可用时 `grep -r`
2. **先测后交**: 写功能前先写失败测试 (Path A 除外)
3. **寸止不跳**: cunzhi 检查点不可跳过、不可自动确认, 不可用时对话确认
4. **状态不丢**: 每阶段完成必须更新 `.ai_state/`, 经验写入 pitfalls.md / patterns.md
5. **最简实现**: 删到不能再删, 不说"应该能跑"— 跑给我看
6. **Plan-First**: Path B+ 任务先出计划 (`.ai_state/plan.md`), cunzhi 确认后再写代码
7. **并行优先**: 无依赖子任务用子代理并行, Path D 用 Agent Teams

## Path A 快速通道

改动 ≤ 20 行、单文件、无架构影响 → 跳 R₀/R/D/P:
1. `augment-context-engine` 确认影响范围
2. 改动 + 测试 → `npm test` / `tsc --noEmit` 通过 → commit

不满足 → 读 `workflows/pace.md` 走 PACE 路由。
进入阶段读 `workflows/riper-7.md` 对应段落。

## 并行工作规范

### 调度流程

1. **任务分析**: 识别 plan.md 中的依赖关系图, 区分可并行节点与串行节点
2. **并行调度**: 无前置依赖的子任务分配给子代理同时执行, 确保不写冲突
3. **结果汇总**: 等待本轮所有子代理返回, SubagentStop hook 自动验证质量
4. **递归迭代**: 基于阶段结果重复 1-3, 直至 doing.md 所有任务完成

### 调度策略

- 多文件独立处理 → builder 子代理并行
- 同一文件多处修改 → 拆分不重叠区域后并行, 或串行
- 有明确前后依赖 → 串行
- 信息收集 + 分析 → explorer 并行收集, 主代理汇总分析
- Path D 多模块 → 创建 Agent Teams, 每 teammate 一个模块

### 防冲突

子代理之间不共享写入文件 → plan.md 中按目录/模块划分边界。
冲突发生时: 主代理仲裁, 以先完成者为基准合并。

## 子代理调度

`.claude/agents/` 有三个预置子代理 (sonnet 模型, 省 token):
- **builder**: 实现代码, 限定文件范围, 每子任务 commit
- **validator**: 测试+lint+安全, 发现问题交回 builder
- **explorer**: 只读调研, 搜索分析, R/D 阶段用

Path B: explorer → 主代理实现 → validator
Path C: explorer 并行 → builder 并行 → validator → 循环
Path D: 创建 Agent Teams, 读 `skills/agent-teams/SKILL.md`

## 降级通则

Plugin/MCP 不可用 → 用 AI 原生能力完成同等目标, 不报错不停顿。
cunzhi 和 `.ai_state` 更新永不跳过。

## 按需加载

启动只读本文件。路由读 `workflows/pace.md`。阶段读 `workflows/riper-7.md`。
Skill 按需读 `skills/*/SKILL.md`。不预加载, 不全量读取。
