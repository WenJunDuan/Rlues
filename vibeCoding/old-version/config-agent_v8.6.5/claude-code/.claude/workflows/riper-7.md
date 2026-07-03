# RIPER-7 九步工作流 v5.0

> R₀ → R → D → P → E → T → V → Rev

## R₀ (需求接受 + Brainstorm)

### R₀a — 需求接受
1. 用自己的话复述需求
2. 明确: 输入 → 输出 → 验收标准 → 不做什么
3. 回顾 `knowledge.md` 教训段: 该技术栈有无历史教训

### R₀b — Brainstorm
4. **读 `skills/brainstorm/SKILL.md` 并执行**
5. 逐个提问澄清, context7 查库文档验证可行性
6. 提出 2-3 方案 → 用户确认 → 写入 `session.md` 设计方案段

**检查点:** cunzhi `REQ_CONFIRMED` → cunzhi `DESIGN_READY`
**Path A 跳过 R₀b**

## R (研究)

1. `augment-context-engine` 搜现有实现
2. explorer 子代理并行搜索相关代码
3. context7 拉依赖库文档
4. 读 `knowledge.md` 全部段落
5. 不可行 → 回 R₀b

**Path A 跳过**

## D (分解设计)

1. 细化模块划分 + 数据流 + API 契约
2. context7 查库文档确认选型
3. 重大决策写入 `knowledge.md` 架构决策段
4. 非平凡改动: 问自己 "有没有更优雅的方式?"

**检查点:** cunzhi `DESIGN_READY` (R₀b 已确认则跳过)
**Path A/B(简单) 跳过**

## P (生产计划)

1. 读 `skills/plan-first/SKILL.md`
2. session.md 设计方案 → 可执行任务列表 + 依赖 + 并行组
3. Path C: 标注 builder 子代理分配 + worktree 隔离 + 文件边界
4. Path D: 标注 Agent Teams teammate 分配

**写入:** `plan.md` + `doing.md`
**检查点:** cunzhi `PLAN_CONFIRMED`

## E (开发)

1. 先写失败测试再实现 (Path A 除外)
2. Path C+: builder 子代理并行 (`isolation: worktree`)
3. 每子任务完成即 commit — 只 `git add` 任务指定的文件
4. 完成的任务从 doing.md 勾选
5. 改动量超预估 2x → STOP, 回 P 重新规划
6. 用户纠正 → 立即修复 + 写入 `knowledge.md` 教训段

## T (测试)

1. 按项目栈运行测试:
   - Node/TS: `npm test` + `tsc --noEmit`
   - Python: `pytest` (或 `conventions.md` 指定的命令)
   - Go: `go test ./...`
   - Rust: `cargo test`
   - 其他: 按 `conventions.md` 定义
2. Path C+: e2e-runner 子代理跑 Playwright E2E
3. 必要时提示用户手动验证

## V (验证审查)

1. `npx eslint .`
2. Path C+: security-auditor 子代理扫描
3. `/review` 官方代码审查
4. 问自己: "staff engineer 会批准这个吗?"
5. diff main, 确认只改了该改的

**检查点:** cunzhi `VERIFIED`

## Rev (验收归档)

1. 经验 → `knowledge.md` (对应段落: 模式/陷阱/决策)
2. 用户纠正过的 → 确认已写入教训段
3. 归档: `mkdir -p .ai_state/archive` → 完成的任务 → `.ai_state/archive/YYYY-MM-DD-<task-id>.md`
4. conventions.md 如有新规范
5. 上下文过大 → `/compact`

**检查点:** cunzhi `TASK_DONE`
