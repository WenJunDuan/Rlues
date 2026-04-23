---
name: pace
description: >
  工作流路由器。收到开发任务时触发。按任务复杂度路由到 6 条路径，编排 Codex 内置工具 + subagent。
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

| Path     | 文件量 | 主力方式                        | 增强                                    | 写 project.json |
| -------- | ------ | ------------------------------- | --------------------------------------- | --------------- |
| Hotfix   | 1      | 直接 Edit                       | 无                                      | 否              |
| Bugfix   | 1-5    | 定位根因 + TDD                  | 无                                      | 否              |
| Quick    | 1-10   | TDD                             | 可选 /review                            | 是              |
| Feature  | 5-20   | 顺序实现 (明确拆 Task)          | /review + ECC                           | 是              |
| Refactor | 10-50  | spawn_agent 并行 (同模式 Task)  | /review + [agents.reviewer] + ECC       | 是              |
| System   | 20+    | spawn_agent 并行 + 主线串联     | /review + [agents.reviewer] + ECC + E2E | 是              |

Quick+ 路由完成 → project.json {path, stage, sprint} → 告知用户。

---

## 共享协议

### 审查协议 (Quick/Feature/Refactor/System 的 review 阶段共用)

```
1. 主力自审: 走一遍 diff, 测试全跑, 自己先挑毛病
2. [Feature+] /review → Codex 内置独立 reviewer 看 diff
3. [Feature+] spawn_agent reviewer → [agents.reviewer] 第三视角
   → 合并: /review 和 reviewer 的输出做共识; 分歧逐条判
4. [System] 追加: npx ecc-agentshield scan
5. [System 有前端] playwright E2E (长跑任务 → 后台 spawn + PostToolUse 盯输出)
6. spawn_agent evaluator → VERDICT
   PASS → 触发 compound skill (提炼 lessons.md) → 停一轮让用户确认 → stage=ship
          (compound 必须在 stage 切换前完成, 同一 response 内不要既写 lessons 又切 stage, 让 delivery-gate 有机会在 review 阶段检查)
   CONCERNS → 修复 → 重新评分
   REWORK → stage=impl (Feature/Refactor) 或 stage=design (System)
   FAIL → stage=plan
```

/review 或 ECC 不可用不停等, 降级继续。

### 发布协议 (Quick/Feature/Refactor/System 的 ship 阶段共用)

```
1. [Quick] git commit → 直接提交
2. [Feature+] git commit + 开 PR (gh pr create 或 git push 后手动开)
3. lessons.md (compound 已追加) + progress.md 最终更新
4. project.json: stage="", sprint+1
5. /compact "Sprint N 完成"
```

---

## Hotfix — 无仪式

```
Edit → test_cmd (有就跑) → git commit → 完
```

## Bugfix — 定位 + TDD (无 stage)

```
复现: 先写一个能复现 bug 的测试 (红)
定位根因: 读相关代码 + 栈 + 日志; 不猜
修复 → 测试通过 (绿)
lint_cmd (有就跑) → /review → git commit
自愈: 根因不对 → 重新定位 (限 3 轮) → 3 轮后通知用户
```

## Quick

stages: impl → review → ship

```
stage=impl:
  Explore: 读要改的文件 + 调用方
  TDD 实现
  库文档不确定 → $context7 (或 "use context7")
  每完成 Task → tasks.md 勾选 + progress.md 追加一行
  lint_cmd + test_cmd → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## Feature — 顺序实现 + 增强

stages: plan → impl → review → ship

```
stage=plan:
  R₀: 读 lessons.md 最近 10 条 → 标记与本任务相关的 Pattern/Pitfall
  复杂度自评: ≥3 模块 / 架构决策 / 外部 API 契约变化 / schema 迁移 / 跨语言 / 需反复修订
    复杂 → 用户当面讨论方向 + 对多方案做 trade-off 分析 → design.md
    不复杂 → 直接按需求合成 design.md
  用户确认 → tasks.md (拆 Task, 每个 Task 有明确验收) → /compact "进入实现" → stage=impl

stage=impl:
  按 tasks.md 顺序实现, 每个 Task 走 TDD
  每完成 Task → tasks.md 勾选 + progress.md 追加一行
  设计偏离 → 先改 design.md 再继续 (铁律 5)
  库文档不确定 → $context7
  dev server / 长跑测试 → 后台运行 + PostToolUse hook 盯输出 (避免前台阻塞)
  → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## Refactor — spawn_agent 并行 + 增强

stages: plan → impl → review → ship

```
stage=plan:
  R₀: 读 lessons.md 最近 10 条
  分析现有结构 + 识别重构单元 → design.md 写清 before/after 和边界
  用户确认 → tasks.md (拆成可并行单元) → stage=impl

stage=impl:
  Task 可并行 → spawn_agent worker 并行做 (同模式 Task 成组)
    每个 worker: 隔离目录 / TDD / 自己跑测试
    主线: wait_agent 收集 + 每组结束后合并
  Task 强耦合 → 串行做
  每完成 Task → tasks.md 勾选 + progress.md 追加
  → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## System — 全链

stages: plan → design → impl → review → ship

```
stage=plan:
  R₀: 读 lessons.md 最近 10 条
  需求提取: 用户访谈式对话, 问边界条件 / 非功能需求 / 失败模式
  发散方向: 至少 3 个方案, 对比 trade-off → design.md (只到方案级)
  用户确认方向 → stage=design

stage=design:
  架构定稿: 组件边界 / 数据流 / 接口契约 / 失败处理
  spawn_agent reviewer → 架构交叉审查 → 回到主线合并
  (可选) 前端有 UI → 单独 design review
  → 合成 tasks.md → 用户确认 → stage=impl

stage=impl:
  按 Task 性质选方式:
    批量同模式 → spawn_agent 并行
    复杂独立 → 主线串行
    不确定 → 主线试做一个, 定模式后 spawn_agent 复制
  每完成 Task → tasks.md 勾选 + progress.md 追加
  设计偏离 → 先改 design.md 再继续
  /compact (每完成一组)
  全部完成 → stage=review

stage=review: → 审查协议 (含 ECC + E2E, 长跑任务后台 + 盯输出)
stage=ship: → 发布协议
```

---

## 状态管理

project.json: path, stage, sprint, tech_stack, test_cmd, build_cmd, lint_cmd, dev_cmd, conventions, gotchas

合法 path: Quick, Feature, Refactor, System (Hotfix/Bugfix 不写 project.json)
合法 stage: plan, design (System only), impl, review, ship, "" (完成)

.ai_state/ 文档职责 (铁律 5, 与 CC 端完全一致的 schema):
  写端: project.json (vibe-init + 路由) / tasks.md (plan + impl 勾选) / progress.md (impl 每 Task 追加) /
        design.md (plan + impl 偏离时更新) / handoff.md (跨 Task 交接时临时) / lessons.md (compound 写) /
        reviews/sprint-N.md (V 阶段写)
  读端: R₀ 读 project/progress/tasks/lessons 最近 10 / plan 读 lessons / impl 读 design 对照 /
        review 读 design + previous reviews / compound 读 reviews + diff 写 lessons

delivery-gate (Stop hook) 在 stage="review" 时检查质量门 (Feature+ 要求 /review 或 reviewer 记录, Quick 不要求)。
阶段转换 + 长任务中 → 主动 `/compact`，不等 context 满。

不间断工作: 不确定用什么库 → $context7。不确定现有代码 → 直接读。不确定测试怎么跑 → 读 project.json test_cmd。
只在以下情况停: 方案需用户确认 (plan 阶段), VERDICT 需判断 (review 阶段), 真正的阻塞 (无权限/无依赖)。
