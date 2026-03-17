# RIPER-7 阶段编排 (v9.1.5)

> 每阶段进入前执行 AGENTS.md 思维协议 (定义→发散→追问→收敛)。
> 工具随时可用: augment-context / context7 / cunzhi / web search / knowledge.md

---

## R₀ 预研 (Path B+)

**目标**: 模糊需求 → 清晰 Spec + 候选方案。

**思考**:

- 需求的本质问题是什么?
- **动手**: `augment-context-engine` 搜有没有类似实现
- **动手**: `mcp-deepwiki` 查候选库, `web search` 看社区方案
- **动手**: `cat .ai_state/knowledge.md | grep 关键词`
- **动手**: `cat .ai_state/lessons.md` 上次踩坑?
- 最简单的实现是什么?

**执行**: 读 brainstorm skill → 发散-收敛 → Spec (SDD 模式) + 候选方案
**产出**: .ai_state/design.md
**检查点**: cunzhi [DESIGN_DIRECTION]

---

## R 研究

**目标**: 验证技术可行性。

**思考**:

- 核心技术版本兼容?
- **动手**: `mcp-deepwiki` 查 API 签名和限制
- **动手**: `augment-context-engine` 搜项目里同类 API 用法
- 性能瓶颈在哪? 边界条件?

**产出**: design.md 追加技术细节

---

## D 设计 (Path B+)

**目标**: 锁定可执行方案。

**思考**:

- 最可能出错的地方?
- 模块接口最小化? 错误处理清楚?
- **动手**: 不确定的 API → `mcp-deepwiki` 再查

**产出**: design.md 终稿
**检查点**: cunzhi [DESIGN_READY]

---

## P 规划 (Path B+)

**目标**: 设计 → 最小可执行任务。

**思考**:

- 依赖清楚? 粒度合适? 验证标准?
- Path C+: 哪些可并行? 分给哪个角色?

**执行**: 读 plan-first skill + `/plan {design 摘要}` 原生规划
**产出**: .ai_state/plan.md
**检查点**: cunzhi [PLAN_CONFIRMED]

---

## E 执行

**目标**: 按 plan 逐 Task, 先测试后实现。

**思考** (每个 Task 前):

- **动手**: `augment-context-engine` 搜可复用代码
- **动手**: `mcp-deepwiki` 查不确定的 API
- 测试场景: 正常 + 边界 + 异常
- 最简实现, 不提前抽象

**执行**: 读 tdd skill → RED→GREEN→REFACTOR (obra/superpowers 强制模式)

- Path C/D: 读 agent-teams skill → 多代理并行
  **产出**: 代码 + 测试 + commit, plan.md 勾选, doing.md 更新

---

## T 验证

**目标**: 证明正确、安全、可维护。

**思考**:

- 测试覆盖关键路径? 不只是 happy path?
- **动手**: `git diff --stat` 检查漏测文件
- 我是 reviewer 会质疑哪里?

**执行**:

1. 读 verification skill → 测试 + lint + 类型检查
2. 读 code-review skill + `/review` 原生审查
3. Path C/D: 读 e2e-testing skill
   **产出**: .ai_state/verified.md
   **检查点**: cunzhi [TESTS_PASSED]

---

## V 交付

**目标**: 确认质量, 沉淀经验。

**思考**:

- 所有 plan 任务真完成了吗? 有 "差不多就行" 的妥协?
- 做得好的地方? 下次怎么复用?
- 浪费时间的地方? 根因?

**执行**:

1. plan 全完成 + 测试通过
2. cunzhi [DELIVERY_CONFIRMED]
3. 读 kaizen skill → `git diff --stat` → knowledge.md + lessons.md (NeoLabHQ 模式)
4. 归档 → archive.md

---

## 可用工具 (任何阶段, 按需取用)

| 工具                      | 用途                      |
| ------------------------- | ------------------------- |
| augment-context-engine    | 搜项目代码 (降级: grep)   |
| context7 / mcp-deepwiki   | 查库文档                  |
| cunzhi                    | 人类确认 (降级: 对话确认) |
| web search                | 搜社区方案                |
| `/plan {摘要}`            | 原生规划 (P 阶段)         |
| `/review`                 | 原生审查 (T 阶段)         |
| claude-delegate           | 委派给 Claude (读 skill)  |
| knowledge.md + lessons.md | 项目历史经验              |

## 状态文件 (.ai_state/)

| 文件           | 创建阶段 | 更新阶段 | 用途                          |
| -------------- | -------- | -------- | ----------------------------- |
| session.md     | 首次运行 | 每阶段   | 断点恢复: 项目/阶段/Path/需求 |
| knowledge.md   | 初始化   | V        | 跨会话经验                    |
| lessons.md     | 初始化   | V        | 已知陷阱                      |
| conventions.md | 初始化   | V        | 编码规范                      |
| design.md      | R₀       | R, D     | Spec + 方案                   |
| plan.md        | P        | E, V     | 任务列表 (checkbox)           |
| doing.md       | E        | E        | 看板                          |
| verified.md    | T        | T        | 验证报告                      |
| review.md      | T        | T        | 审查详情                      |
| archive.md     | V        | V        | 交付归档                      |
