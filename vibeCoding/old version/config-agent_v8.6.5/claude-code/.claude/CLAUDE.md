# VibeCoding Kernel v8.6.5

## 铁律

1. **先搜后写**: 写代码前 `augment-context-engine` 搜现有实现, 不可用时 `grep -r`
2. **先测后交**: 写功能前先写失败测试 (Path A 除外)
3. **寸止不跳**: cunzhi 检查点不可跳过、不可自动确认, 不可用时对话确认
4. **状态不丢**: 每阶段完成更新 `.ai_state/`
5. **最简实现**: 删到不能再删, 跑给我看
6. **Plan-First**: Path B+ 先出计划, cunzhi 确认后再写代码
7. **并行优先**: 无依赖子任务用 Task() 子代理并行, Path D 用 Agent Teams
8. **自我纠错**: 用户纠正 → 立即写入 `knowledge.md` 教训段, 不犯第二次
9. **完成前验证**: 不标记完成除非测试通过 + 日志干净 + 能演示正确性
10. **偏移即停**: 方向偏了 STOP + 重新规划, 不硬推

## Path A 快速通道

改动 ≤ 20 行、单文件、无架构影响 → 跳 R₀/R/D/P:
1. `augment-context-engine` 确认影响范围
2. 改 + 测试通过 → commit

不满足 → 读 `workflows/pace.md` 走 PACE 路由。
阶段读 `workflows/riper-7.md` 对应段落。
Path B+ 进入 R₀b 时**必须**读 `skills/brainstorm/SKILL.md`。

## Bug-Fix 快速通道

Bug/CI 失败 → 不走完整 PACE:
1. 定位根因 → 写失败测试复现 → 修复 → 测试通过 → commit
2. 更新 `knowledge.md` 教训段
3. 改动 > 20 行或涉及架构 → 升级 Path B

## 子代理 (.claude/agents/)

5 个预置 (sonnet 模型): builder, validator, explorer, e2e-runner, security-auditor
- Path C+ builder 用 `isolation: worktree` 避免文件冲突
- 每子代理一个任务, plan.md 中按目录划分写入边界
- builder 提交时只 `git add` 任务指定的文件, 不用 `-A`

## .ai_state 文件 (精简版 + knowledge 分段扩展)

| 文件 | 用途 | 更新时机 |
|:---|:---|:---|
| session.md | 需求+Path+验收+设计方案 | R₀ |
| plan.md | 任务列表+依赖+并行组 | P |
| doing.md | 当前进行中 | E (逐项勾选) |
| knowledge.md | 4 段: 经验模式/已知陷阱/架构决策/教训 | R₀(回顾) / Rev(写入) / 纠正时(即时) |
| conventions.md | 项目编码规范 | 首次+有新规范时 |
| archive/ | 已完成任务归档 | Rev (`mkdir -p` 防御式创建) |

**Schema 规则:** 只有这 5 个文件 + 1 个目录。所有经验类数据统一写入 knowledge.md 对应段落, 不另建文件。

## 官方能力 — 直接用, 不重复包装

`/review` `/compact` `/plan` — 直接调用, 不通过 skill 转发。
Superpowers 等已安装插件保持全部启用。

## 降级通则

MCP 不可用 → AI 原生能力完成同等目标, 不报错不停顿。
cunzhi 和 `.ai_state` 更新永不跳过。

## 行为校准 (来自官方最佳实践)

- **不确定时说出来**: 信息不足以得出结论时, 明确说"不确定", 不猜测。减少幻觉。
- **不过度工程**: Opus 4.6 倾向过度抽象。坚守铁律 #5 — 用户没要求的灵活性不加。
- **Compact 前存档**: 上下文接近极限时, 主动存进度到 `.ai_state/`, 不因 token 不够而中途停工。

## 按需加载

启动只读本文件。路由读 `workflows/pace.md`。阶段读 `workflows/riper-7.md`。
Skill 按需读 `skills/*/SKILL.md`。不预加载。
