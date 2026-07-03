# RIPER-7 — 阶段编排

> 每阶段三件事: 做什么(步骤)、写什么(.ai_state)、何时停(cunzhi)。
> 方法论 SP 教, 工具 Plugin 给, 这里只编排 WHEN + WHERE + HOW MUCH。

## 统一工具矩阵

| 阶段 | MCP/工具 | Plugin (CC) | Skill | .ai_state | cunzhi |
|:---|:---|:---|:---|:---|:---|
| **R** Research | augment + deepwiki | — | brainstorm | → session.md | ○ C+ |
| **D** Design | augment + deepwiki | — | brainstorm | → design.md | ● DESIGN_READY |
| **P** Plan | augment | feature-dev | — | → plan.md + doing.md | ● PLAN_APPROVED |
| **E** Execute | augment + context7 | commit-commands | tdd | ✎ doing.md | ○ 大改动 |
| **V** Verify | — | — | verification | → verified.md | ○ 3次失败 |
| **Rev** Review | — | code-review + security + pr-review | code-quality + knowledge | → review.md | ● REVIEW_DONE |
| **A** Archive | — | — | — | → archive/ | — |

图例: ● 必须检查点 ○ 条件检查点 — 无

MCP 全称: augment = `augment-context-engine`, deepwiki = `mcp-deepwiki`, context7 = `context7 CLI (npx ctx7 resolve)`

---

## R (Research)

**步骤:**
1. `augment-context-engine` 搜现有代码 → 理解当前实现和模式
2. `mcp-deepwiki` 查官方文档 → 确认 API/框架约束
3. 读 `.knowledge/` 相关条目 → 复用历史经验
4. 读 `.ai_state/conventions.md` → 对齐项目规范

**写入:** `.ai_state/session.md` — 需求理解、现有实现、关键发现
**检查点:** Path C+ → cunzhi 确认研究充分
**Path 裁剪:** Path A 跳过, Path B 限时 15min

---

## D (Design)

**步骤:**
1. 基于 R 阶段发现提出 2-3 方案
2. `augment-context-engine` 搜索类似实现验证可行性
3. 选定方案, 写 ADR (Architecture Decision Record)
4. 标注影响范围: 哪些文件改、哪些接口变

**写入:** `.ai_state/design.md` — ADR 格式 (背景/决策/后果)
**检查点:** ● cunzhi `DESIGN_READY` — 所有 Path B+ 必须
**Path 裁剪:** Path A 跳过, Path B 合并到 R 一起 15min

---

## P (Plan)

**步骤:**
1. 从 design.md 拆解为有序任务列表
2. 每个任务: 目标 + 涉及文件 + 验收标准 + 预计时间
3. 标注任务依赖关系和可并行项
4. Path C+: 触发 `feature-dev` plugin 辅助拆解
5. Path D: 标注哪些任务可分给 subagent

**写入:**
- `.ai_state/plan.md` — 完整任务列表
- `.ai_state/doing.md` — 当前执行任务 (初始化为第一个)

**检查点:** ● cunzhi `PLAN_APPROVED` — 所有 Path B+ 必须
**Path 裁剪:** Path A 跳过

---

## E (Execute)

**步骤:**
1. 读 `doing.md` 获取当前任务
2. 需要库文档时: `npx ctx7 resolve <library>` 拉取
3. 按 tdd Skill 分级策略:
   - Path B: 核心逻辑写测试, 其余可选
   - Path C: 全部写测试, RED→GREEN 交替 commit
   - Path D: + 集成测试, 原子 commit + PR
4. 每完成一个任务 → 更新 doing.md 进度
5. 每次 commit → `commit-commands` plugin 规范格式

**写入:** `.ai_state/doing.md` — 实时更新进度 (☐/☑)
**检查点:** ○ 大规模修改 (>100行或>3文件) → cunzhi 确认方向
**Path D:** 按 `agent-teams` Skill 分配 subagent 并行

---

## V (Verify)

**步骤:**
按 verification Skill Path 分级清单执行:

| Path | 检查项 |
|:---|:---|
| A | `npm test` 通过 |
| B | + `npx eslint .` clean + `npx tsc --noEmit` |
| C | + 覆盖率 ≥ 80% + 无 TODO/FIXME |
| D | + 集成测试 + 性能基线 + 安全扫描 |

**失败处理:**
```
失败 → 自动修复重试 (max 3)
  → 仍失败 → SP debugging 自动触发
    → 仍失败 → cunzhi: 请求人工介入
```

**写入:** `.ai_state/verified.md` — 通过项 + 失败项 + 修复记录
**检查点:** ○ 累计失败 ≥ 3 次 → cunzhi

---

## Rev (Review)

**步骤:**
1. **CC Plugin 编排** (按顺序):
   - `code-review` plugin → 自动化审查 (6 个 sub-agent)
   - `security-guidance` plugin → 安全扫描 (Path C+)
   - `pr-review-toolkit` plugin → PR 格式 (如有 PR)
2. **Linus 四问** (所有 Path):
   - 逻辑正确? (不只是能跑)
   - 边界处理? (空值、并发、溢出)
   - 命名清晰? (不需要注释解释)
   - 最简实现? (删到不能再删)
3. **经验沉淀**: 发现的问题 → `.knowledge/` 记录

**Codex 替代:** 无 Plugin, 手动执行审查 + `npm audit`

**写入:** `.ai_state/review.md` — 审查发现 + 修复记录
**检查点:** ● cunzhi `REVIEW_DONE` — 所有 Path B+ 必须

---

## A (Archive)

**步骤:**
1. 将 `.ai_state/` 当前文件移入 `.ai_state/archive/{日期}/`
2. 更新 `.knowledge/` — 沉淀本次经验 (知识点、坑、决策)
3. 清理 doing.md, session.md 为下一任务准备

**写入:** `.ai_state/archive/{日期}/` — 完整状态快照
**检查点:** 无
**Path 裁剪:** Path A/B 跳过 (session.md 追加即可)
