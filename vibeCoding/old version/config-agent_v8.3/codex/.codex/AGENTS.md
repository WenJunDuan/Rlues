# VibeCoding Kernel v8.3.5 — Codex CLI

> 编排层。只做 WHEN + WHERE + HOW MUCH。

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

不满足条件 → 走 PACE 路由, 读 `.codex/workflows/pace.md`。

## MCP 工具

| MCP | 用途 | 引用阶段 | 降级 |
|:---|:---|:---|:---|
| `augment-context-engine` | 语义代码搜索 | R/D/E | `grep -r` → `cat` |
| `cunzhi` | 人工确认检查点 | 全阶段 | ⛔ 不可降级 |
| `mcp-deepwiki` | 开源库文档查询 | R/D | Web search |
| `chrome-devtools` | 浏览器调试 | E/V (前端) | 手动浏览器测试 |

## Skills (编排参数, 按需加载)

Skills 目录: `.codex/skills/` (与 codex Code 共享)

| Skill | 内容 | 加载时机 |
|:---|:---|:---|
| `cunzhi` | 检查点交互协议 | Path B+ 全程 |
| `agent-teams` | 并行分工模板 | Path D |
| `knowledge` | 跨会话经验管理 | Rev 阶段 |
| `brainstorm` | augment + ADR 编排 | R/D 阶段 |
| `tdd` | Path 分级 + 提交策略 | E 阶段 |
| `verification` | Path 分级验证清单 | V 阶段 |
| `code-quality` | 审查 + Linus 四问 | Rev 阶段 |
| `context7` | 库文档按需拉取 | E 阶段 |

## 降级通则

MCP 不可用时, 用原生命令行工具完成同等目标, 不报错不停顿。
cunzhi 检查点和 `.ai_state` 更新永不跳过。

## 质量门控 (替代 codex Code Stop Hook)

完成任务前必须执行 `node .codex/hooks/delivery-gate.cjs`, 此脚本自动检查:
1. `npm test` — 全部通过
2. `npx tsc --noEmit` — 类型检查通过 (如有 tsconfig)
3. `.ai_state/doing.md` — 无未完成任务 (☐)
任一失败 → 修复后重跑, 不允许带错交付。

## 上下文恢复

每次会话开始执行 `node .codex/hooks/context-loader.cjs` 自动恢复 .ai_state 上下文。

## 跨会话经验

每次开始新任务前, 读取 `.knowledge/pitfalls.md` 避免重复踩坑。
Review 完成后, 将本次教训写入 `.knowledge/` 对应文件。

## 按需加载

启动只读本文件。需要路由读 `.codex/workflows/pace.md`。
进入阶段读 `.codex/workflows/riper-7.md`。
触发 Skill 读 `.codex/skills/*/SKILL.md`。
