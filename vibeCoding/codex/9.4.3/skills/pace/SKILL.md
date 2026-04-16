---
name: pace
description: >
  工作流路由器。收到开发任务时触发。按任务复杂度路由到 6 条路径，编排 Codex 工具 + 增强。
---

# PACE — 6 路径路由器 (Codex CLI)

首先读 .ai_state/project.json。有 stage → 从当前阶段继续。
.ai_state/ 不存在 → 提示用户运行初始化。

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

| Path | 文件量 | Codex 主力 | 增强 | 写 project.json |
|------|--------|-----------|------|----------------|
| Hotfix | 1 | Edit | 无 | 否 |
| Bugfix | 1-5 | 调试+TDD | 无 | 否 |
| Quick | 1-10 | TDD | /review | 是 |
| Feature | 5-20 | subagent 并行 | brainstorming + /review | 是 |
| Refactor | 10-50 | subagent 并行 | /review | 是 |
| System | 20+ | subagent 全链 | 全增强 | 是 |

Quick+ 路由完成 → project.json {path, stage, sprint} → 告知用户。

---

## 共享协议

### 审查协议 (Quick/Feature/Refactor/System 的 review 阶段共用)

```
1. /review → 主审查
2. [Feature+] spawn reviewer agent → 独立审查
   → 对比两份 → 合并修复清单 → 一次性修
3. [System] 追加: 安全扫描 (augment-context 语义搜索敏感模式)
4. 评审: 按 4 维度评分 → VERDICT
   PASS → stage=ship
   CONCERNS → 修复 → 重新评分
   REWORK → stage=impl
   FAIL → stage=plan
```

### 发布协议 (ship 阶段共用)

```
1. [Quick] git commit → 直接提交
2. [Feature+] git merge + PR
3. lessons.md + progress.md 更新
4. project.json: stage="", sprint+1
```

---

## Hotfix — 无仪式

```
Edit → test_cmd (有就跑) → git commit → 完
```

## Bugfix — 调试 + TDD (无 stage)

```
定位根因 (grep + augment-context 语义搜索)
TDD: 写回归测试(复现) → 修复 → 测试通过
lint_cmd (有就跑) → /review → git commit
自愈: 修不好 3 轮 → 通知用户
```

## Quick

stages: impl → review → ship

```
stage=impl:
  Explore: 读要改的文件 + 调用方 (augment-context)
  TDD 实现 (superpowers 自动激活)
  lint_cmd + test_cmd → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## Feature — subagent 并行 + 增强

stages: plan → impl → review → ship

```
stage=plan:
  superpowers brainstorming → 发散 + 方向挑战
  → 合成 design.md
  用户确认 → tasks.md → stage=impl

stage=impl:
  按 Task 复杂度:
    简单 Task → 直接 TDD
    复杂 Task → spawn builder agent + handoff.md
    独立 Task → 多 builder 并行
  每完成一组 → /compact
  全部完成 → stage=review

stage=review: → 审查协议 (spawn reviewer agent 交叉审查)
stage=ship: → 发布协议
```

## Refactor — subagent 并行

stages: plan → impl → review → ship

```
stage=plan:
  分析重构范围 (augment-context 语义搜索)
  用户确认 → design.md + tasks.md → stage=impl

stage=impl:
  spawn 多个 builder agent 并行重构
  每个 agent 独立 worktree
  → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## System — 全链

stages: plan → design → impl → review → ship

```
stage=plan:
  superpowers brainstorming → 发散
  → 合成 design.md → 用户确认 → stage=design

stage=design:
  架构方案 + 接口定义
  → tasks.md → 用户确认 → stage=impl

stage=impl:
  按 Task 性质选工具:
    批量同模式 → 多 builder 并行
    复杂独立 → 单 builder + handoff.md
  handoff.md 必须含: 文件树 + 代码片段 + 验收标准
  每完成一组 → /compact
  全部完成 → stage=review

stage=review: → 审查协议 (reviewer agent + 安全扫描)
stage=ship: → 发布协议
```

---

## 状态管理

project.json: path, stage, sprint, tech_stack, test_cmd, build_cmd, lint_cmd, dev_cmd, conventions, gotchas

合法 path: Quick, Feature, Refactor, System (Hotfix/Bugfix 不写 project.json)
合法 stage: plan, design (System only), impl, review, ship, "" (完成)

stop-gate 在 stage="review" 时检查质量门 (Feature+ 要求 reviewer agent 审查, Quick 不要求)。
不间断工作: 不确定用什么库 → context7 skill 查文档。不确定现有代码 → augment-context 语义搜索。
只在以下情况停: 方案需用户确认 (plan 阶段), VERDICT 需判断 (review 阶段), 真正的阻塞。
