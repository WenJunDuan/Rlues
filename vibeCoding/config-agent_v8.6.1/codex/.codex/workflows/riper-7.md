# RIPER-7 九步工作流 v3.0

> 需求接受 → 研究 → 分解设计 → 需求讨论 → 生产计划
> → 开发 → 测试 → 验证审查 → 验收归档

## R₀ (需求接受 + 需求讨论/Brainstorm)

### R₀a — 需求接受
1. 接收用户需求 → 用自己的话复述理解
2. 检查 `.ai_state/requirements/` 是否有 PRD
3. 检查 `.ai_state/assets/` 是否有 UI 设计图
4. 明确三要素: 输入 → 输出 → 验收标准
5. 列出不做的事 (边界排除)

### R₀b — Brainstorm (苏格拉底式需求精炼)
6. **读 `.codex/skills/brainstorm/SKILL.md` 并严格执行**
7. 逐个提问澄清 → 一次一个, 优先选择题
8. context7 查询相关库文档 (`mcp-deepwiki` / `npx ctx7 resolve`) → 验证技术可行性
9. 提出 2-3 个方案 + 推荐理由
10. 分段呈现设计 → 用户确认 → 写入 `.ai_state/design.md`
11. 需求变更 → 记录原因, 更新 session.md
12. 重大变更 → 重新 PACE 路由

**写入:** `.ai_state/session.md` + `.ai_state/design.md`
**检查点:** ● cunzhi `REQ_CONFIRMED` → ● cunzhi `DESIGN_READY`
**技能:** brainstorm, context7
**Path 裁剪:** Path A 跳过 R₀b

## R (研究)

> 基于 R₀b brainstorm 的设计方案, 深入调研技术细节

1. **搜索**: `augment-context-engine` 搜现有实现 (不可用时 `grep -r`)
2. **调研**: 并行搜索相关代码
3. **文档**: context7 拉取依赖库文档 — `mcp-deepwiki` 查询 (不可用时 `npx ctx7 resolve`)
4. **经验**: 读 `.ai_state/pitfalls.md` + `patterns.md` + `decisions.md`
5. **验证**: 对照 brainstorm 设计方案, 确认技术可行性, 不可行则回 R₀b 调整

**写入:** `.ai_state/session.md` 追加研究结论
**技能:** context7, knowledge
**Path 裁剪:** Path A 跳过

## D (分解设计)

> 基于 R₀b brainstorm 的 design.md + R 的研究结论, 细化架构

1. **架构**: 细化 design.md 中的模块划分 + 数据流
2. **接口**: 定义模块间 API 契约
3. **技术选型**: context7 查最新库文档, 对比方案, 记录决策到 `decisions.md`
4. **ADR**: 重大决策写 Architecture Decision Record

**写入:** `.ai_state/design.md` (更新)
**检查点:** ● cunzhi `DESIGN_READY` (如 R₀b 已确认则跳过)
**技能:** brainstorm (如需补充), context7
**Path 裁剪:** Path A/B(简单) 跳过

## P (生产计划)

> 读 `.codex/skills/plan-first/SKILL.md` — 基于 design.md 生成可执行计划

1. **拆解**: 把 design.md 中的设计转为可执行任务列表
2. **依赖**: 标注任务间依赖关系
3. **并行**: 识别可并行的任务组
4. **估时**: 每个任务预估时间
5. **分配**: Path C+ 标注 collab 并行任务分配

**写入:** `.ai_state/plan.md` + 更新 `doing.md`
**检查点:** ● cunzhi `PLAN_CONFIRMED`
**技能:** plan-first
**命令:** 可用 `/plan` 辅助生成

## E (开发)

1. **TDD**: 读 `.codex/skills/tdd/SKILL.md` — 先写失败测试再实现
2. **实现**: Path C+ 使用 collab + parallel 并行开发
3. **Commit**: 每个子任务完成即 commit (conventional commits)
4. **更新**: 完成的任务从 doing.md 勾选

**技能:** plan-first, tdd
**Path A:** 直接改 + 测试
**Path C+:** collab 并行

## T (测试)

1. **单测**: `npm test` 全部通过
2. **类型**: `tsc --noEmit` 零错误
3. **E2E**: Path C+ 运行 Playwright E2E 测试
4. **手动**: 必要时提示用户手动验证

**技能:** verification, e2e-testing

## V (验证审查)

1. **Lint**: `npx eslint .`
2. **安全**: `npm audit` + 手动扫描 (Path C+)
3. **质量**: 读 `.codex/skills/code-quality/SKILL.md` 执行审查清单

**写入:** `.ai_state/verified.md` + `review.md`
**检查点:** ● cunzhi `VERIFIED`
**技能:** verification, code-quality, security-review

## Rev (验收归档)

1. **经验沉淀**: 好模式 → `patterns.md`, 踩坑 → `pitfalls.md`, 决策 → `decisions.md`
2. **归档**: 完成的任务从 `doing.md` 移到 archive/
3. **更新**: conventions.md 如有新规范
4. **上下文管理**: 上下文过大时读 `.codex/skills/smart-archive/SKILL.md`

**检查点:** ● cunzhi `TASK_DONE`
**技能:** knowledge, smart-archive
