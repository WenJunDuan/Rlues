# VibeCoding Kernel v8.6.5 — Codex CLI

## 铁律

1. **先搜后写**: 写代码前 `augment-context-engine` 搜现有实现, 不可用时 `grep -r`
2. **先测后交**: 写功能前先写失败测试 (Path A 除外)
3. **寸止不跳**: cunzhi 检查点不可跳过, 不可用时对话确认
4. **状态不丢**: 每阶段完成更新 `.ai_state/`
5. **最简实现**: 删到不能再删, 跑给我看
6. **Plan-First**: Path B+ 先出计划, cunzhi 确认后再写代码
7. **并行优先**: 无依赖子任务用 `multi_agent` + `parallel` 模式并行
8. **自我纠错**: 用户纠正 → 立即写入 `knowledge.md` 教训段, 不犯第二次
9. **完成前验证**: 不标记完成除非测试通过 + 能演示正确性
10. **偏移即停**: 方向偏了 STOP + 重新规划, 不硬推

## Path A 快速通道

改动 ≤ 20 行、单文件、无架构影响 → 直接改 + 测试通过 → commit。
不满足 → 读 `.codex/workflows/pace.md`。阶段读 `.codex/workflows/riper-7.md`。
Path B+ 进入 R₀b **必须**读 `.codex/skills/brainstorm/SKILL.md`。

## Bug-Fix 快速通道

Bug/CI 失败 → 定位→复现→修复→测试通过→commit→写 `knowledge.md` 教训段。

## 并行工作 (Codex 原生)

Path C+: 使用 `multi_agent` 模式 — 多个 Codex 实例协作同一代码库。
Path D: 使用 `multi_agent` + `parallel` 模式 — multi_agent 协作 + parallel 独立任务并行, 结果合并。

- 每个并行任务指定文件边界, 防冲突
- `plan.md` 中标注任务分配和目录范围

## .ai_state 文件

| 文件           | 用途                    |
| :------------- | :---------------------- |
| session.md     | 需求+Path+验收+设计方案 |
| plan.md        | 任务列表+依赖+并行组    |
| doing.md       | 当前进行中              |
| knowledge.md   | 经验+陷阱+决策+教训     |
| conventions.md | 项目编码规范            |

归档: 完成的任务移到 `.ai_state/archive/YYYY-MM-DD-<task-id>.md` (Rev 阶段 `mkdir -p` 防御式创建)

## 官方能力 — 直接用

`/review` `/compact` — 直接调用, 不通过 skill 转发。

## 质量门禁

Codex CLI 不自动执行 hook 脚本, 以下门禁在流程中**显式执行**:

- **会话开始**: `node .codex/hooks/session-start.cjs` — 注入项目状态上下文
- **交付前**: `node .codex/hooks/delivery-gate.cjs` — 检查 doing.md + plan.md 完成度

Rev 阶段结束前**必须**运行 delivery-gate, 通过后才能 cunzhi `TASK_DONE`。

## 降级通则

MCP 不可用 → AI 原生能力完成同等目标, 不报错不停顿。
cunzhi 和 `.ai_state` 更新永不跳过。

## 行为校准

- **不确定时说出来**: 信息不足时明确说"不确定", 不猜测
- **不过度工程**: 用户没要求的灵活性不加
- **Compact 前存档**: 上下文接近极限时, 存进度到 `.ai_state/`

## 按需加载

启动只读本文件。路由读 `.codex/workflows/pace.md`。阶段读 `.codex/workflows/riper-7.md`。
Skill 按需读 `.codex/skills/*/SKILL.md`。不预加载。
