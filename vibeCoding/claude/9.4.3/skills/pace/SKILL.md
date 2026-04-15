---
name: pace
effort: high
description: >
  工作流路由器。收到开发任务时触发。按任务复杂度路由到 6 条路径，编排 CC 工具 + 增强节点。
---

# PACE — 6 路径路由器

首先读 .ai_state/project.json。有 stage → 从当前阶段继续。
.ai_state/ 不存在 → 提示 `/vibe-init`。

## 路由

```
          ┌─ 1行/配置 ──────→ Hotfix
 修复 ────┤
          └─ 需要调试 ─────→ Bugfix

          ┌─ 需求清晰/小 ──→ Quick
 新建 ────┤ 需要设计 ─────→ Feature
          ├─ 改现有结构 ───→ Refactor
          └─ 跨模块/服务 ──→ System
```

| Path     | 文件量 | CC 主力               | 增强                     | 写 project.json |
| -------- | ------ | --------------------- | ------------------------ | --------------- |
| Hotfix   | 1      | Edit                  | 无                       | 否              |
| Bugfix   | 1-5    | /debug                | 无                       | 否              |
| Quick    | 1-10   | TDD                   | 可选交叉审查             | 是              |
| Feature  | 5-20   | /feature-dev          | brainstorming + 交叉审查 | 是              |
| Refactor | 10-50  | /batch                | Gstack eng + 交叉审查    | 是              |
| System   | 20+    | /feature-dev + /batch | 全增强                   | 是              |

Quick+ 路由完成 → project.json {path, stage, sprint} → 告知用户。

---

## 共享协议

### 审查协议 (Quick/Feature/Refactor/System 的 review 阶段共用)

```
1. /review → 第一份审查
2. [Feature+] codex:review → 第二份审查
   → 对比: 共识直接采纳 / 分歧逐条判 → 合并修复清单 → 一次性修
3. [System] 追加: codex:adversarial-review + npx ecc-agentshield scan
4. [System 有前端] Gstack /qa + playwright E2E
5. /simplify → 清理
6. @evaluator → VERDICT
   PASS → stage=ship
   CONCERNS → 修复 → 重新评分
   REWORK → stage=impl (Feature/Refactor) 或 stage=design (System)
   FAIL → stage=plan
```

codex 不可用 → 只用 CC /review。Gstack 不可用 → 跳过 /qa。superpowers 不可用 → 直接和用户对话探索需求。增强不可用不停等。

### 发布协议 (Quick/Feature/Refactor/System 的 ship 阶段共用)

```
1. [Quick] git commit → 跳过 /ship, 直接提交
2. [Feature+] Gstack /ship → 发布 (同步 main, 跑测试, 开 PR)
3. [System] Gstack /retro → 工程回顾
4. lessons.md + progress.md 更新
5. project.json: stage="", sprint+1
6. /compact "Sprint N 完成"
```

Gstack 不可用 → 手动 git merge + PR。

---

## Hotfix — 无仪式

```
Edit → test_cmd (有就跑) → git commit → 完
```

## Bugfix — /debug + TDD (无 stage)

```
/debug → 定位根因
TDD: 写回归测试(复现) → 修复 → 测试通过
lint_cmd (有就跑) → /review → git commit
自愈: 修不好 → /debug 再来一轮 (限 3 轮) → 3 轮后通知用户
```

## Quick

stages: impl → review → ship

```
stage=impl:
  Explore: 读要改的文件 + 调用方
  TDD 实现 (superpowers 自动激活)
  lint_cmd + test_cmd → /simplify → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## Feature — /feature-dev + 增强

stages: plan → impl → review → ship

```
stage=plan:
  superpowers brainstorming → 发散 + 方向挑战
  → 合成 design.md
  Gstack /plan-eng-review → 架构交叉验证
  Gstack 不可用 → /plan 替代
  用户确认 → tasks.md → /compact "进入实现" → stage=impl

stage=impl:
  /feature-dev "需求描述"
  Phase 4 (架构) 前 → 用户确认
  /simplify → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## Refactor — /batch + 增强

stages: plan → impl → review → ship

```
stage=plan:
  Gstack /plan-eng-review → 验证重构方案
  Gstack 不可用 → /plan 替代
  用户确认 → design.md + tasks.md → stage=impl

stage=impl:
  /batch "重构描述"
  CC 自动: Research → Plan → 用户确认 → 并行 worktree → 每 worker /simplify + 测试
  → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## System — 全链

stages: plan → design → impl → review → ship

```
stage=plan:
  Gstack /office-hours → 需求提取
  superpowers brainstorming → 发散 + 方向挑战
  → 合成 design.md → 用户确认 → stage=design

stage=design:
  Gstack /plan-eng-review → 架构锁定
  Gstack /plan-design-review → 设计审查 (有 UI 时)
  → 合成 tasks.md → 用户确认 → stage=impl

stage=impl:
  按 Task 性质选工具:
    批量同模式 → /batch 并行
    复杂独立 → /feature-dev
    跨模型委托 → codex:rescue + handoff.md:
      handoff.md 必须含: 实际文件树 (find 输出) + Task 相关代码片段 (Read 取关键函数) + 验收标准
      codex 结果取回后验证: 引用的文件 test -f → 不存在的结论作废
      幻觉>50% → 降级到 @generator
  每完成一组 → /compact
  全部完成 → /simplify → stage=review

stage=review: → 审查协议 (含 adversarial + ECC + /qa + E2E)
stage=ship: → 发布协议 (含 /retro)
```

---

## 状态管理

project.json: path, stage, sprint, tech_stack, test_cmd, build_cmd, lint_cmd, dev_cmd, conventions, gotchas

合法 path: Quick, Feature, Refactor, System (Hotfix/Bugfix 不写 project.json)
合法 stage: plan, design (System only), impl, review, ship, "" (完成)

delivery-gate 在 stage="review" 时检查质量门 (Feature+ 要求外部审查, Quick 不要求)。
阶段转换 + 长任务中 → 主动 `/compact`，不等 context 满。

不间断工作: 不确定用什么库 → ctx7 查。不确定现有代码 → Read 看。不确定测试怎么跑 → 读 project.json test_cmd。
只在以下情况停: 方案需用户确认 (plan 阶段), VERDICT 需判断 (review 阶段), 真正的阻塞 (无权限/无依赖)。
