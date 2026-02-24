# RIPER-7 — 阶段编排

> 每阶段三件事: 做什么(步骤)、写什么(.ai_state)、何时停(cunzhi)。
> 方法论模型已有, 工具自动发现, 这里只编排 WHEN + WHERE + HOW MUCH。

## 统一工具矩阵

| 阶段 | MCP/工具 | Skill | .ai_state | cunzhi |
|:---|:---|:---|:---|:---|
| **R₀** 需求接受+讨论 | — | — | → session.md | ● REQ_CONFIRMED |
| **R** Research | augment + deepwiki | brainstorm | ✎ session.md | ○ C+ |
| **D** Design | augment + deepwiki | brainstorm | → design.md + decisions.md | ● DESIGN_READY |
| **P** Plan+分解 | augment | plan-first + agent-teams | → plan.md + doing.md | ● PLAN_APPROVED |
| **E** Execute | augment + context7 | tdd | ✎ doing.md | ○ BIG_CHANGE |
| **T** Test | — | tdd + verification | → verified.md | ○ FAIL_3X |
| **Rev** Review | — | code-quality + knowledge | → review.md | ● REVIEW_DONE |
| **A** 验收归档 | — | — | → archive/ | — |

图例: ● 必须检查点 ○ 条件检查点 — 无
MCP: augment = `augment-context-engine`, deepwiki = `mcp-deepwiki`, context7 = `npx ctx7 resolve`

---

## R₀ (需求接受 + 需求讨论)

> 所有 Path B+ 的第一步。确认在解决正确的问题, 不跳过。
> 包含两个子阶段: **接受** (理解需求) → **讨论** (对齐认知) → cunzhi 确认。

### R₀a — 需求接受

1. 接收用户需求 → 用自己的话复述需求理解
2. 检查 `.ai_state/requirements/` 内是否有相关 PRD / 需求文档
3. 检查 `.ai_state/assets/` 内是否有 UI 设计图 / 原型
4. 明确三要素: **输入**是什么 → **输出**是什么 → **验收标准**是什么
5. 列出 **不做的事** (边界排除), 防止范围蔓延

### R₀b — 需求讨论

6. 整理 **待澄清项** (不确定的、有歧义的、缺失的) → 一次性向用户提问, 不猜测
7. 用户回复后 → 更新需求理解, 如有新疑问 → 继续追问 (讨论循环)
8. 讨论过程中需求变更 → 记录变更原因, 更新 session.md, 不静默改需求
9. 重大需求变更 (影响架构 / 新增模块) → 重新走 PACE 路由判定 Path

```
讨论循环:
  提问 → 用户回复 → 更新理解 → 仍有疑问? → 继续提问
                                 │
                                 └─ 无疑问 → cunzhi REQ_CONFIRMED
```

**写入:** `.ai_state/session.md` — 需求理解、验收标准、边界排除、讨论记录、变更记录
**检查点:** ● cunzhi `REQ_CONFIRMED` — 用户确认需求理解正确后才进入 R 阶段
**Path 裁剪:** Path A 跳过 (需求足够简单)

---

## R (Research)

**步骤:**
1. `augment-context-engine` 搜现有代码 → 找相关实现和模式
2. `mcp-deepwiki` 查官方文档 → 确认 API / 框架约束
3. 读 `.ai_state/pitfalls.md` + `patterns.md` → 复用历史经验
4. 读 `.ai_state/conventions.md` → 对齐编码规范
5. Path C+: 通过 `collab` 并行搜索多个方向
6. 研究发现与需求理解冲突 → 回到 R₀ 重新讨论

**写入:** `.ai_state/session.md` (追加) — 现有实现、技术约束、关键发现
**检查点:** Path C+ → cunzhi 确认研究充分
**Path 裁剪:** Path A 跳过, Path B 限时 15min

---

## D (Design)

**步骤:**
1. 基于 R 阶段发现提出 2-3 方案
2. `augment-context-engine` 搜索类似实现验证可行性
3. 选定方案, 写 ADR (Architecture Decision Record)
4. 标注影响范围: 哪些文件改、哪些接口变
5. 需求不明确 → 提出具体问题向用户确认, 不假设

**写入:** `.ai_state/design.md` — ADR 格式 (背景/决策/后果); 重大决策 → `decisions.md`
**检查点:** ● cunzhi `DESIGN_READY` — 所有 Path B+ 必须
**Path 裁剪:** Path A 跳过, Path B 合并到 R 一起 15min

---

## P (Plan + 分解)

> Plan-First: 拆解为可执行的任务列表, 标注依赖和并行机会。

**步骤:**
1. 读 `skills/plan-first/SKILL.md` → 执行 Plan-First 协议
2. 从 design.md 拆解为有序任务列表
3. 每个任务: 目标 + 涉及文件 + 验收标准 + 预估时间
4. 标注任务依赖关系图:
   - 无依赖 → 标记 `[并行]`
   - 有前置 → 标记 `[串行: 依赖 T{N}]`
5. Path C+: `/plan` 命令辅助拆解
6. Path D: 读 `skills/agent-teams/SKILL.md` → 标注每任务的 collab 分配
   - 按目录/模块划分, 子任务之间零文件重叠
7. 初始化 doing.md (todo list, 所有任务 `- [ ]`)

**写入:**
- `.ai_state/plan.md` — 任务列表 + 依赖图 + 并行标注 + collab 分配
- `.ai_state/doing.md` — 初始化待办列表

**检查点:** ● cunzhi `PLAN_APPROVED` — 所有 Path B+ 必须
**Path 裁剪:** Path A 跳过

---

## E (Execute)

**步骤:**
1. 读 `doing.md` 获取当前任务
2. 需要库文档时: `npx ctx7 resolve <library>` 拉取
3. 按 tdd Skill 分级策略:
   - Path B: 核心逻辑写测试
   - Path C: 全部写测试, RED→GREEN 交替 commit
   - Path D: + 集成测试, 原子 commit
4. 并行调度 (Path C/D):
   - 取 doing.md 中所有 `[并行]` 且无未完成前置的任务
   - 通过 `collab` 并行下发子任务
   - Path D: 每模块一个 collab 并行执行
5. 每完成一个任务 → 更新 doing.md 进度 (`- [x]`)

**写入:** `.ai_state/doing.md` — 实时更新进度
**检查点:** ○ 大规模修改 (>100行或>3文件) → cunzhi `BIG_CHANGE`

---

## T (Test)

> 独立测试阶段, 不混在 Execute 里。E 阶段写的是伴随测试, T 阶段做全量验证。

**步骤:**
按 verification Skill 的 Path 分级清单执行:

| 检查项 | A | B | C | D |
|:---|:---:|:---:|:---:|:---:|
| `npm test` 全部通过 | ✓ | ✓ | ✓ | ✓ |
| `npx eslint .` clean | — | ✓ | ✓ | ✓ |
| `npx tsc --noEmit` | — | ✓ | ✓ | ✓ |
| 覆盖率 ≥ 80% | — | — | ✓ | ✓ |
| 无 TODO / FIXME | — | — | ✓ | ✓ |
| `npm audit --audit-level=high` | — | — | ✓ | ✓ |
| 集成测试 / E2E | — | — | — | ✓ |
| 性能基线对比 | — | — | — | ✓ |

**失败处理:**
```
失败 → 自动修复重试 (max 3)
  → 仍失败 → 调试分析
    → 仍失败 → cunzhi FAIL_3X: 请求人工介入
```

**写入:** `.ai_state/verified.md` — 通过项 + 失败项 + 修复记录
**检查点:** ○ 累计失败 ≥ 3 次 → cunzhi `FAIL_3X`

---

## Rev (Review)

**步骤:**
1. **Linus 四问** (所有 Path):
   - 逻辑正确? (不只是能跑)
   - 边界处理? (空值、并发、溢出)
   - 命名清晰? (不需要注释解释)
   - 最简实现? (删到不能再删)
2. **需求回验**: 对照 R₀ 的验收标准逐条检查, 遗漏 → 返回 E
3. **经验沉淀**: 问题 → `pitfalls.md`; 好模式 → `patterns.md`; 工具心得 → `tools.md`

**写入:** `.ai_state/review.md` — 审查发现 + 修复记录
**检查点:** ● cunzhi `REVIEW_DONE` — 所有 Path B+ 必须

---

## A (验收归档)

**步骤:**
1. 对照 `.ai_state/session.md` 的验收标准 → 逐条确认通过
2. 将当前 `.ai_state/` 文件复制到 `.ai_state/archive/{日期}/`
3. 更新经验沉淀: `pitfalls.md` + `patterns.md` + `decisions.md`
4. 清理 doing.md, session.md 为下一任务准备
5. 向用户报告: 完成情况 + 验收标准对照 + 经验总结

**写入:** `.ai_state/archive/{日期}/` — 完整状态快照
**检查点:** 无
**Path 裁剪:** Path A/B 跳过归档 (session.md 追加即可)

---

## 完整流程图

```
需求 → [PACE路由] → Path判定
                       │
                    Path A ────────────────────────────→ E → T → done
                       │
                    Path B+ → R₀a(需求接受) → R₀b(需求讨论 ↺) ──cunzhi──→ R(研究) → D(设计) ──cunzhi──→
                                                                                                        │
  ←── A(验收归档) ←──cunzhi── Rev(审查) ← T(测试) ← E(开发, collab并行) ←──cunzhi── P(计划+分解+TODO)
```

中途任意阶段发现需求不清 → 回到 R₀b 重新讨论。
中途需求变更导致架构影响 → 重新走 PACE 路由。
中途复杂度升级 → cunzhi `PATH_UPGRADE`, 从当前阶段按新 Path 继续。
