# RIPER-7 工程编排 v9.3.1

## 统一工具调度表

| 阶段 | VibeCoding Skill | Plugin | MCP | 状态文件 |
|------|-----------------|--------|-----|---------|
| R₀ 头脑风暴 | — | superpowers brainstorming | augment-context | design.md |
| R 研究 | context7 | — | augment-context | design.md |
| D 设计 | context7 | — | — | design.md |
| P 规划 | — | superpowers write-plan | — | plan.md |
| E 开发 | reflexion | superpowers execute-plan | augment-context | doing.md |
| T 测试 | verification, code-review, security-review, e2e | ECC AgentShield | — | quality.md |
| V 验收 | kaizen | superpowers finishing-branch | cunzhi | lessons.md |

---

### Path A (快速: bug/配置/<30min)
直接执行修复 → 运行测试验证 → 完成。

---

### R₀ — 头脑风暴 (Path B+)

**做什么**: 理解需求, 探索方案, 不写代码
**使用**: augment-context 扫描 → superpowers brainstorming

```
1. augment-context-engine 搜索现有代码 (降级: grep)
2. 读 lessons.md + conventions.md
3. superpowers brainstorming (降级: 手动苏格拉底式访谈)
4. 输出 design.md → cunzhi 确认 (降级: 对话确认)
```

---

### R — 研究 / D — 设计 (Path B+)

```
1. context7 查库文档 (npx ctx7 resolve)
2. augment-context 搜索类似实现
3. 验证方案可行性 → 更新 design.md
4. cunzhi [DESIGN_READY] 确认
```

---

### P — 规划 (Path B+)

```
1. superpowers write-plan (降级: 手动 T-001/T-002)
2. /review 内置审查 或 validator agent 自审
3. cunzhi [PLAN_CONFIRMED] 确认
```

---

### E — 执行 (Path B+) — Sisyphus

```
对 plan.md 每个 Task:
1. superpowers execute-plan (降级: 手动 TDD)
2. Reflexion: 自问 6 条清单 → 发现问题立即修复
3. 审查通过 → [x] Task + commit

Sisyphus: plan 有 [ ] 未完成就不停。
```

---

### T — 测试/审查 (Path B+)

```
1. superpowers verification-before-completion (如已安装)
2. verification skill: 验收标准逐条确认
3. /review 内置审查
4. code-review skill: 4 级 LLM-as-Judge
5. npx ecc-agentshield scan (如已安装)
6. → quality.md
7. Quality Gate: PASS / CONCERNS / REWORK / FAIL
```

---

### V — 验收 (Path B+)

```
1. kaizen skill → lessons.md + conventions.md "Agent 易犯错误"
2. superpowers finishing-branch (降级: 手动 merge/PR/discard)
3. cunzhi [DELIVERY_COMPLETE]
```

## 流转规则
- 只能前进, 不能跳过
- session.md 记录 current_phase
- 中断恢复: 读 session.md 自动恢复
