# RIPER-7 九步工作流 v5.0 (Codex)

> R₀ → R → D → P → E → T → V → Rev

## R₀ (需求接受 + Brainstorm)

### R₀a — 需求接受
1. 运行 `node .codex/hooks/session-start.cjs` 注入项目状态
2. 用自己的话复述需求
3. 明确: 输入 → 输出 → 验收标准 → 不做什么
4. 回顾 `knowledge.md` 教训段

### R₀b — Brainstorm
5. **读 `skills/brainstorm/SKILL.md` 并执行**
6. 逐个提问澄清, context7 查库文档验证可行性
7. 提出 2-3 方案 → 用户确认 → 写入 `session.md` 设计方案段

**检查点:** cunzhi `REQ_CONFIRMED` → cunzhi `DESIGN_READY`
**Path A 跳过 R₀b**

## R (研究)

1. `augment-context-engine` 搜现有实现
2. context7 拉依赖库文档
3. 读 `knowledge.md` 全部段落
4. 不可行 → 回 R₀b

**Path A 跳过**

## D (分解设计)

1. 细化模块划分 + 数据流 + API 契约
2. context7 查库文档确认选型
3. 重大决策写入 `knowledge.md` 架构决策段
4. 非平凡改动: 问自己 "有没有更优雅的方式?"

**检查点:** cunzhi `DESIGN_READY` (R₀b 已确认则跳过)

## P (生产计划)

1. 读 `skills/plan-first/SKILL.md`
2. session.md 设计方案 → 可执行任务列表 + 依赖 + 并行组
3. Path C+: 标注 collab/parallel 分配和文件边界
4. 使用 `/plan` 进入规划模式, `plan.md` 作为落盘镜像

**写入:** `plan.md` + `doing.md`
**检查点:** cunzhi `PLAN_CONFIRMED`

## E (开发)

1. 先写失败测试再实现 (Path A 除外)
2. Path C+: `collab` 模式并行开发
3. 每子任务完成即 commit — 只 `git add` 任务指定的文件
4. doing.md 勾选
5. 改动量超预估 2x → STOP, 回 P
6. 用户纠正 → 修复 + 写入 `knowledge.md` 教训段

## T (测试)

1. 按项目栈运行测试:
   - Node/TS: `npm test` + `tsc --noEmit`
   - Python: `pytest` (或 `conventions.md` 指定的命令)
   - Go: `go test ./...`
   - Rust: `cargo test`
   - 其他: 按 `conventions.md` 定义
2. Path C+: chrome-devtools MCP 验证 UI + E2E 场景
3. 必要时提示用户手动验证

## V (验证审查)

1. `npx eslint .`
2. Path C+: `npm audit` 安全扫描
3. `/review` 官方代码审查
4. 问自己: "staff engineer 会批准这个吗?"
5. diff main, 确认只改了该改的

**检查点:** cunzhi `VERIFIED`

## Rev (验收归档)

1. 经验 → `knowledge.md` 对应段落
2. 用户纠正过的 → 确认已写入教训段
3. 归档: `mkdir -p .ai_state/archive` → 完成的任务 → `.ai_state/archive/YYYY-MM-DD-<task-id>.md`
4. conventions.md 如有新规范
5. **运行 `node .codex/hooks/delivery-gate.cjs`** — 检查完成度
6. 上下文过大 → `/compact`

**检查点:** cunzhi `TASK_DONE`
