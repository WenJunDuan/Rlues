# VibeCoding Kernel v8.3.5

> 编排层。不替代 Superpowers 方法论、不重复 Plugin 能力、只做 WHEN + WHERE + HOW MUCH。

## 铁律

1. **先搜后写**: 写代码前必须 `augment-context-engine` 搜现有实现
2. **先测后交**: 写功能前必须写失败测试
3. **寸止不跳**: cunzhi 检查点不可跳过、不可自动确认
4. **状态不丢**: 每阶段完成必须更新 `.ai_state/`
5. **经验不废**: 犯过的错必须写入 `.knowledge/`
6. **最简实现**: 删到不能再删, YAGNI
7. **证据说话**: 不说"应该能跑", 跑给我看
8. **渐进交付**: 每步可回退, 每步可验证

## Path A 快速通道

改动 ≤ 20 行、单文件、无架构影响 → 跳过 R/D/P, 直接 E → V:
1. `augment-context-engine` 确认影响范围
2. 写改动 + 写测试
3. `npm test` / `npx tsc --noEmit` 通过
4. commit + 更新 `.ai_state/session.md`

不满足条件 → 走 PACE 路由, 读 `workflows/pace.md`。

## Superpowers 协作

已安装 `superpowers@superpowers-marketplace`。
SP 自动提供: brainstorming, writing-plans, tdd, subagent-driven-dev, verification, code-review, debugging, worktree workflows。

VibeCoding 不重复 SP 方法论。VibeCoding 增值:
- PACE 按复杂度选路径 (SP 没有路径分级)
- RIPER-7 按阶段编排工具组合 + cunzhi 检查点 (SP 没有人工确认门控)
- Path 分级参数调节 TDD/验证/提交严格度 (SP 是统一严格度)
- `.ai_state` 文件驱动状态追踪 (SP 依赖 context window)
- `.knowledge` 跨会话经验复用 (SP 单会话)

## 工具注册表

### MCP 工具 (编排层引用)

| MCP | 用途 | 引用阶段 | 降级 |
|:---|:---|:---|:---|
| `augment-context-engine` | 语义代码搜索 | R/D/E | `grep -r` → `Read` |
| `cunzhi` | 人工确认检查点 | 全阶段 | ⛔ 不可降级 |
| `mcp-deepwiki` | 开源库文档查询 | R/D | Web search |

### 官方 Plugins (开机自装, 按阶段触发)

| Plugin | 触发阶段 | Path 门槛 |
|:---|:---|:---|
| `feature-dev` | P (Plan) | Path C/D |
| `commit-commands` | E (每次 commit) | 全路径 |
| `frontend-design` | E (UI 任务) | 按需 |
| `code-review` | Rev (Review) | Path B+ |
| `security-guidance` | Rev (Review) | Path C+ |
| `pr-review-toolkit` | Rev (PR 场景) | Path C/D |
| `learning-output-style` | 全局 | 全路径 |
| `hookify` | 全局 | 全路径 |

### VibeCoding Skills (编排参数, 按需加载)

| Skill | 内容 | 加载时机 |
|:---|:---|:---|
| `cunzhi` | 检查点交互协议 | Path B+ 全程 |
| `agent-teams` | 并行分工模板 | Path D |
| `knowledge` | 跨会话经验管理 | Rev 阶段 |
| `brainstorm` | augment + ADR 编排 | R/D 阶段 |
| `tdd` | Path 分级 + 提交策略 | E 阶段 |
| `verification` | Path 分级验证清单 | V 阶段 |
| `code-quality` | Plugin 编排顺序 | Rev 阶段 |
| `context7` | 库文档按需拉取 | E 阶段 |

## 降级通则

Plugin/MCP 不可用时, 用 AI 原生能力完成同等目标, 不报错不停顿。
SP 不可用时, 按 `workflows/riper-7.md` 阶段步骤手动执行。
cunzhi 检查点和 `.ai_state` 更新永不跳过。

## 可选增强: planning-with-files

如已安装 `OthmanAdi/planning-with-files`:
- 其 PreToolUse hook 自动读 plan → 与 VibeCoding `.ai_state/plan.md` 互补
- 其 Stop hook 阻止未完成交付 → 与 delivery-gate.cjs 互补
- 其 `session-catchup.py` → 与 /vibe-resume 互补 (compaction 后恢复)
- 不冲突: planning-with-files 管文件层, VibeCoding 管编排层

## 按需加载

启动只读本文件 (~110 行)。需要路由读 `workflows/pace.md`。
进入阶段读 `workflows/riper-7.md` 对应段落。
触发 Skill 读对应 `skills/*/SKILL.md`。
不预加载, 不全量读取。
