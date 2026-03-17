# RIPER-7 阶段编排 (v9.1.5)

> 每个阶段进入前, 执行 CLAUDE.md 的思维协议 (定义→发散→追问→收敛)。
> 工具随时可用, 不绑定阶段。需要时就用。

---

## R₀ 预研 (Path B+ 独有)

**目标**: 模糊需求 → 清晰 Spec + 可评估的候选方案。

**思考**:
- 需求的本质问题是什么? 用户真正要解决什么?
- **动手**: `augment-context-engine` 搜项目代码, 有没有类似功能已实现
- **动手**: 读 context7 skill → `mcp-deepwiki` 查候选库文档做对比
- **动手**: `cat .ai_state/knowledge.md | grep 关键词` 查历史经验
- **动手**: `cat .ai_state/lessons.md` 看上次踩过什么坑
- 从零开始最简单的实现方式是什么?

**执行**: 读 brainstorm skill → 发散-收敛流程 → Spec (SDD 模式: MUST/SHOULD/COULD) + 候选方案
**产出**: .ai_state/design.md
**检查点**: cunzhi [DESIGN_DIRECTION] — 用户选择方案
**技巧**: 可用 `/fork` 并行探索不同方向

---

## R 研究

**目标**: 验证选定方案的技术可行性, 补充细节。

**思考**:
- 方案依赖的核心技术版本兼容吗?
- **动手**: 读 context7 skill → `mcp-deepwiki` 查 API 具体签名和限制
- **动手**: `augment-context-engine` 搜项目里同类 API 的用法
- 性能瓶颈可能在哪? 数据量大了会怎样?
- 有没有忽略的边界条件?

**产出**: design.md 追加 (接口签名、数据结构、依赖版本、边界条件)

---

## D 设计 (Path B+ 独有)

**目标**: 锁定可执行的技术方案。

**思考**:
- 最可能出错的地方在哪?
- 半年后改这个功能, 现在的设计容易改吗?
- 模块接口是否最小化? 耦合是否可控?
- 错误处理策略清楚吗?
- **动手**: 不确定的 API → `mcp-deepwiki` 再查一次

**产出**: design.md 终稿 (模块划分 / 接口 / 数据结构 / 错误处理)
**检查点**: cunzhi [DESIGN_READY]

---

## P 规划 (Path B+ 独有)

**目标**: 设计 → 可独立执行、可独立验证的最小任务。

**思考**:
- 依赖关系清楚吗? 有隐藏耦合吗?
- 每个任务的验证标准是什么? 怎么知道 "做完了"?
- 粒度合适吗? 太大难验证, 太小浪费上下文
- Path C+: 哪些任务可以并行? 分给哪个子代理?

**执行**: 读 plan-first skill + `/plan {design.md 一句话摘要}`
**产出**: .ai_state/plan.md (checkbox 格式, 每 Task ≤30min)
**检查点**: cunzhi [PLAN_CONFIRMED]
**铁律**: plan 未确认, 不准写一行代码

---

## E 执行

**目标**: 按 plan 逐 Task 实现, 每个 Task 先测试后实现。

**思考** (每个 Task 开始前):
- **动手**: `augment-context-engine` 搜有没有现成代码可以复用
- **动手**: 读 context7 skill → `mcp-deepwiki` 查不确定的 API
- 测试覆盖哪些场景? 正常 + 边界 + 异常
- 最简单的实现是什么? 不要提前抽象
- 复杂 Task 可用 `/effort high` 提升推理深度

**执行**: 读 tdd skill → RED→GREEN→REFACTOR (obra/superpowers 强制模式)
- Path A: 直接开发, 关键路径有测试
- Path B: 严格 TDD L2, doing.md 看板跟踪
- Path C/D: 读 agent-teams skill → Agent(builder) × N 并行, worktree 隔离
**产出**: 代码 + 测试 + commit, plan.md 逐项勾选, doing.md 更新
**Hook**: PostToolUse TDD 检查 (写源码前是否有测试)

---

## T 验证

**目标**: 证明代码正确、安全、可维护。

**思考**:
- 测试真的覆盖关键路径了吗? 不只是 happy path?
- **动手**: `git diff --stat` 看改了什么, 有没有漏测的文件
- 如果我是 reviewer, 我会质疑哪里?
- 这些改动会不会影响其他模块?

**执行**:
1. 读 verification skill → 测试 + lint + 类型检查
2. 读 code-review skill → 逻辑/安全/性能审查
3. Path C/D: 读 e2e-testing skill → Agent(e2e-runner)
4. Path D: Agent(security-auditor) → cunzhi [SECURITY_PASSED]
**产出**: .ai_state/verified.md
**检查点**: cunzhi [TESTS_PASSED]

---

## V 交付

**目标**: 确认质量, 沉淀经验, 归档。

**思考**:
- 所有 plan 任务真的都完成了吗? 有 "差不多就行" 的妥协吗?
- 这次做得好的地方是什么? 下次怎么复用?
- 浪费时间的地方? 根因是什么?

**执行**:
1. delivery-gate hook 机械检查 (plan 完成 + 测试通过)
2. LLM-as-Judge prompt hook 语义检查 (NeoLabHQ 模式: 质量/测试/commit/密钥)
3. cunzhi [DELIVERY_CONFIRMED]
4. 读 kaizen skill → `git diff --stat` → knowledge.md + lessons.md
5. 归档 → archive.md
6. 可选: `/loop 10m npm test` 持续监控稳定性
**产出**: 交付 + 经验沉淀

---

## 可用工具 (任何阶段, 按需取用)

| 工具 | 用途 | 怎么用 |
|------|------|--------|
| augment-context-engine | 搜索项目代码 | MCP tool, 降级: grep -r |
| context7 / mcp-deepwiki | 查库文档 | 读 context7 skill |
| cunzhi | 人类确认检查点 | MCP tool, 降级: 对话确认 |
| WebSearch | 搜社区方案 | 内置 tool |
| knowledge.md + lessons.md | 项目经验 | 直接 cat/grep |
| codex-delegate | 委派给 Codex | 读 skill |
| /effort low/high | 调整推理深度 | E 阶段复杂 Task 前 |
| /plan {摘要} | 快速进入规划 | P 阶段 |
| /fork | 并行探索方案 | R₀ brainstorm |
| /loop {interval} {cmd} | 持续监控 | V 阶段后 |

## 状态文件 (.ai_state/)

| 文件 | 创建阶段 | 更新阶段 | 用途 |
|------|---------|---------|------|
| session.md | SessionStart | 每阶段 | 断点恢复: 项目/阶段/Path/需求/时间 |
| knowledge.md | /vibe-init | V | 跨会话经验: [日期] 领域: 可复用模式 |
| lessons.md | /vibe-init | V | 已知陷阱: [日期] 领域: 描述→正确做法 |
| conventions.md | /vibe-init | V | 编码规范: 语言/框架/测试/风格/Git |
| design.md | R₀ | R, D | Spec + 候选方案 → 技术方案终稿 |
| plan.md | P | E, V | 任务列表 (checkbox), delivery-gate 检查 |
| doing.md | E | E | 看板: TODO/DOING/DONE |
| verified.md | T | T | 验证报告: 测试/lint/review 结果 |
| review.md | T | T | 代码审查详情 |
| archive.md | V | V | 交付归档: 决策+变更+经验 |
