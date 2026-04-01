# RIPER-7 工程编排 v9.3.1

## 统一工具调度表

| 阶段 | VibeCoding Skill | Plugin | MCP | 状态文件 |
|------|-----------------|--------|-----|---------|
| R₀ 头脑风暴 | — | superpowers:brainstorm | augment-context | design.md |
| R 研究 | context7 | — | augment-context | design.md (更新) |
| D 设计 | context7 | — | — | design.md (终稿) |
| P 规划 | — | superpowers:write-plan, gstack /codex (审查) | — | plan.md |
| E 开发 | reflexion | gstack /codex (委托), superpowers:execute-plan (次选), feature-dev, commit-commands | augment-context | doing.md |
| T 测试 | verification, code-review, security-review, e2e | code-review (官方), playwright-skill, ECC AgentShield | — | quality.md |
| V 验收 | kaizen | superpowers:finishing-branch, commit-commands | cunzhi | lessons.md |

## 阶段详情

---

### Path A (快速: bug/配置/<30min)
直接执行修复 → 运行测试验证 → delivery-gate 检查 → 完成。
不需要 design.md / plan.md / quality.md。

---

### R₀ — 头脑风暴 (Path B+)

**本阶段做什么**: 理解需求, 探索方案, 不写代码
**自动使用**: augment-context 扫描 → superpowers:brainstorm
**下一阶段**: R (研究)

```
步骤:
1. augment-context-engine 搜索现有代码, 理解项目结构
   (降级: grep + find)
2. 读 .ai_state/lessons.md + conventions.md — 避免重复犯错
3. /superpowers:brainstorm — 苏格拉底式逐个提问, 探索方案
   (降级: 手动一次一问, 覆盖目标/场景/边界/非功能需求)
4. 输出 2-3 方案到 .ai_state/design.md (MUST/SHOULD/COULD + 验收标准)
5. cunzhi [DESIGN_DIRECTION] — 用户选择方向
   (降级: 对话确认)
```

---

### R — 研究 (Path B+)

**本阶段做什么**: 深入调研已选方案, 确认技术可行性
**自动使用**: context7 拉取库文档 → 对照 design.md 验证

```
步骤:
1. context7 skill — 按需拉取相关库文档 (npx ctx7 resolve)
2. augment-context-engine 搜索项目中类似实现
3. 对照 design.md 验证方案可行性
4. 识别技术风险和依赖
5. 更新 design.md 中的技术细节
```

---

### D — 设计 (Path B+)

**本阶段做什么**: 确定技术方案, 输出架构决策
**自动使用**: context7 查 API 细节 → design.md 终稿

```
步骤:
1. context7 查 API 细节, 确认接口设计可行
2. 完成 design.md 终稿 (含验收标准)
3. cunzhi [DESIGN_READY] — 用户确认设计
   (降级: 对话确认)
```

---

### P — 规划 (Path B+)

**本阶段做什么**: 将设计拆解为可执行的任务列表
**自动使用**: superpowers:write-plan → gstack /codex 审查

```
步骤:
1. /superpowers:write-plan — 读 design.md, 生成 plan.md
   (降级: 手动分解为 T-001/T-002... 格式任务)
2. 对抗审查:
   a. gstack 已安装: /codex review plan.md — 获取 Codex second opinion
   b. gstack 未安装: validator agent 自审 ("找漏洞/模糊/不可执行")
3. 根据审查意见修改 plan.md
4. Path C+: 分配子代理 (builder/validator/explorer)
5. cunzhi [PLAN_CONFIRMED] — 用户确认计划
   (降级: 对话确认)
```

---

### E — 执行 (Path B+) — Sisyphus 循环

**本阶段做什么**: 按计划写代码
**自动使用**: 三级降级写代码 → reflexion 自审 → commit

```
对 plan.md 每个 Task:

1. 写代码 (三级降级):
   a. 首选 (gstack 已安装 + Codex 可用):
      /codex "实现 Task X: {Task描述 + 相关文件 + conventions.md}"
      → Codex (GPT-5.4) 写代码, CC 收到产出后审查
   b. 次选 (superpowers 已安装):
      /superpowers:execute-plan → CC subagent 写代码 (含 TDD + review)
   c. 兜底: 逐 Task TDD — 先测试→实现→重构

2. Reflexion (reflexion skill):
   自问 6 条: 走捷径? 忽略边界? 硬编码? 过度工程? 偏离spec? 可读?
   发现问题 → 立即修复
   值得记录 → lessons.md

3. 审查通过 → [x] Task + commit
   commit 用 /commit (commit-commands 如已安装)

Sisyphus: plan.md 有任何 [ ] 未完成, 不停止。
```

Path C+: agent-teams 并行 — builder 在 worktree 中实现, validator 在 worktree 中测试

---

### T — 测试/审查 (Path B+)

**本阶段做什么**: 验证代码质量, 跑测试, 安全检查, 交叉审查
**自动使用**: verification + code-review + delivery-gate

```
步骤:
1. superpowers verification-before-completion (如已安装, 功能完整性)
2. verification skill — 验收标准逐条确认:
   读 design.md "## 验收标准" → 逐条对标 → 未满足写入 quality.md
3. 技术验证: npm test + tsc --noEmit + eslint (按 Path 分级)
4. 前端 (如有 UI): playwright-skill 浏览器自动化验证
5. /code-review (官方 plugin, 如已安装): 4 agents 广度扫描
6. code-review skill — LLM-as-Judge: spec 合规 4 级判定
7. Codex 交叉审查 (gstack 已安装):
   /codex review 最近的代码变更 — 获取 second opinion
   (gstack 未安装: CC 单方审查)
8. 安全: npx ecc-agentshield scan (ECC 已安装时)
9. Path C+: security-review skill 深度审查
10. 综合 → quality.md
11. delivery-gate.cjs 自动检查:
    PASS(exit 0) / CONCERNS(exit 0+warn) / REWORK(exit 2) / FAIL(exit 2)
```

---

### V — 验收 (Path B+)

**本阶段做什么**: 最终确认, 提交, 归档经验
**自动使用**: kaizen → superpowers finish-branch → cunzhi

```
步骤:
1. kaizen skill — 回顾本次开发:
   好的保持 / 差的改进 / 模式性错误?
   更新 lessons.md + conventions.md "Agent 易犯错误"
2. 分支收尾:
   superpowers finishing-a-development-branch (如已安装)
   (降级: 手动选 merge/PR/keep/discard)
3. cunzhi [DELIVERY_COMPLETE] — 用户确认交付
   (降级: 对话确认)
```

## RIPER 阶段流转规则

- 只能前进, 不能跳过 (Path A 的"跳过"是路由决定, 不是运行时跳过)
- 每个阶段完成时更新 session.md 中的 current_phase
- 中断恢复: context-loader.cjs 读 session.md 自动恢复到中断阶段
