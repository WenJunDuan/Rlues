---
name: riper-pace
effort: high
description: >
  任务分析和工作流调度。收到开发任务、需求分析、或不确定从哪开始时触发。
---

# RIPER-PACE 工作流引擎

收到任务后: **PACE 选路径, RIPER 按路径执行。**

## 当前项目状态
!`cat .ai_state/project.json 2>/dev/null || echo '{"path":"","stage":"","sprint":0,"conventions":[],"gotchas":[]}'`

## 待办任务
!`cat .ai_state/tasks.md 2>/dev/null || echo '(无 tasks.md — 需要初始化)'`

---

## 前置检查

.ai_state/ 不存在? → 创建目录, 从本 skill 的 templates/ 复制模板文件:
```
mkdir -p .ai_state/reviews
cp ${CLAUDE_SKILL_DIR}/templates/project.json .ai_state/
cp ${CLAUDE_SKILL_DIR}/templates/tasks.md .ai_state/
cp ${CLAUDE_SKILL_DIR}/templates/design.md .ai_state/
cp ${CLAUDE_SKILL_DIR}/templates/lessons.md .ai_state/
```

有进行中的 stage? → 从当前 stage 继续, 不要重新路由。

---

## PACE 路由

评估任务的 5 维度, 取最高匹配:

| 维度 | A (快速) | B (标准) | C (复杂) | D (系统) |
|------|---------|---------|---------|---------|
| 文件 | 1-3 | 4-10 | 10+ | 跨服务 |
| 时间 | <30min | 30min-4h | 4h-2d | >2d |
| 架构 | 无影响 | 局部 | 跨模块 | 系统级 |
| 测试 | 单元 | 单元+集成 | 含 E2E | 全链路 |
| 风险 | 低 | 中 | 高 | 极高 |

路径 → 阶段映射:
```
A: ───────── E → T
B: R₀→R→D→P→E→T→V
C: 同 B + /batch 并行 + 对抗审查
D: 同 C + 设计评审
```

路由完成 → 更新 .ai_state/project.json → 告知用户 → 进入首阶段。

---

## RIPER 阶段

### 每阶段通用
1. 读 .ai_state/project.json 的 gotchas → 避开
2. 读 .ai_state/lessons.md → 参考历史教训
3. 完成后更新 project.json 的 stage 字段

---

### R₀ 需求精炼 (Path B+)

**目标:** 模糊需求 → 可验收 Spec
**工具:** superpowers brainstorming (自动激活) · `npx ctx7 resolve` (查库文档) · augment-context-engine (跨文件关联)
**产出:** .ai_state/design.md (MUST/SHOULD/COULD + 验收标准)
**门控:** cunzhi DESIGN_READY 检查点 (如可用) 或直接问用户确认 → stage="R"
**详细指引:** → plan/SKILL.md 阶段 R₀

---

### R 技术调研 (Path B+)

**目标:** 验证技术方案可行, 排除风险
**工具:** Grep (搜项目代码) · `npx ctx7 resolve` (查库 API) · augment-context-engine (语义搜索) · Read (conventions/lessons)
**产出:** design.md 追加技术方案段 (接口/依赖/风险)
**门控:** 技术方案非空 → stage="D"
**详细指引:** → plan/SKILL.md 阶段 R

---

### D 方案定稿 (Path B+)

**目标:** 锁定方案, 生成 Sprint Contract
**工具:** @evaluator (方案评审) · `/review` (快速审查)
**约束:** `/codex:adversarial-review` 只审查代码, D 阶段无代码, 不要用
**产出:**
1. design.md 最终版
2. .ai_state/tasks.md 填充 Task 清单
**门控:** cunzhi SPRINT_CONTRACT 检查点 (如可用) 或直接问用户确认 → stage="P"
**详细指引:** → plan/SKILL.md 阶段 D

---

### P 计划排期 (Path B+)

**目标:** 确定 Task 执行顺序和依赖
**工具:** 主 Agent 分析
**产出:** tasks.md 补充依赖和执行顺序
**约束:** 用 VibeCoding 的 tasks.md 格式 (- [ ] F001/T001: 描述)。如果 superpowers writing-plans 自动激活, 以 VibeCoding 格式为准。
**门控:** tasks.md 非空 → stage="E"
**详细指引:** → plan/SKILL.md 阶段 P

---

### E 执行 (所有 Path)

**目标:** 逐个完成 Task, 产出通过测试的代码
**详细指引:** → execute/SKILL.md
**门控:** tasks.md 所有 Task 完成 (Sisyphus) → stage="T"

---

### T 审查 (所有 Path)

**目标:** 独立验证质量, 产出审查报告和评分
**详细指引:** → review/SKILL.md
**门控:**
- PASS (≥4.0) → stage="V"
- CONCERNS (3.0-3.9) → 修复后重新评分
- REWORK (2.0-2.9) → 回 E
- FAIL (<2.0) → 回 D

---

### V 归档 (Path B+)

**目标:** 更新知识库, 为下次迭代积累
**产出:**
1. project.json: conventions + gotchas 更新
2. lessons.md: 追加本 Sprint 教训
3. project.json: stage="", sprint+1

---

## 阶段转换规则

1. 前进: 满足门控 → 更新 stage → 进入下一阶段
2. 后退: T-REWORK→E; T-FAIL→D
3. 跳过: Path A 只做 E→T
4. 中断恢复: 下次触发 skill 时 `!command` 注入状态, 从当前 stage 继续

## Gotchas

- ❌ 收到任务直接写代码 → ✅ 先 PACE 路由
- ❌ D 阶段用 /codex:adversarial-review → ✅ 该命令审查代码, D 阶段无代码
- ❌ E 完成一半就进 T → ✅ Sisyphus: 全部 Task 完成才能进 T
- ❌ T-CONCERNS 就交付 → ✅ 修复后重新评分
