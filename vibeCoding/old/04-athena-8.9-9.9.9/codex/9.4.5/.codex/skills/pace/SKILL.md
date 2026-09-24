---
name: pace
description: >
  工作流路由器。收到开发任务时触发。按任务复杂度路由到 6 条路径，编排 Codex 内置工具 + spawn_agent。
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
| Feature  | 5-20   | 顺序实现 (明确拆 Task)          | /review + spawn_agent reviewer + ECC    | 是              |
| Refactor | 10-50  | spawn_agent 并行 (同模式 Task)  | /review + reviewer + ECC                | 是              |
| System   | 20+    | spawn_agent 并行 + 主线串联     | /review + reviewer + ECC + E2E          | 是              |

Quick+ 路由完成 → project.json {path, stage, sprint} → 告知用户。

---

## 路径升级机制 (impl 阶段持续监测)

写代码过程中发现实际复杂度超出当前路径 → 暂停, 询问用户升级:

| 升级触发信号 | 当前 → 建议 |
|------------|-----------|
| 需要改数据库 schema | * → System |
| 跨 3+ 模块的接口变更 | Feature → System |
| 实际改文件数 > 当前路径上限的 50% | Quick → Feature, Feature → Refactor/System |
| Refactor 中发现需要新增模块/重新设计接口 | Refactor → System |

升级流程: 用户确认 → project.json path 升级 + stage 回到 design (System) 或 plan (其他) → progress.md 追加升级记录 → 重新 plan。
**不自动升级**, 避免 Codex 借机扩 scope。

---

## 共享协议

### 审查协议 (Quick/Feature/Refactor/System 的 review 阶段共用)

```
1. 主力自审: 走一遍 diff, 测试全跑, 自己先挑毛病
2. [Feature+] /review 内置 → Codex 启动独立 reviewer 看 diff (一个视角)
3. [Feature+] spawn_agent reviewer → 第二个独立视角 (不同 prompt, 不同 cycle)
   → 必须看到 child agent thread 真实输出 (反伪装, 铁律 4)
   → 调用失败按铁律 8 重试 3 次, 最终失败则记录到 ~/.codex/lessons/draft-*.md
   → 对比 /review 和 reviewer 输出, 共识合并 → 一次性修分歧逐条判
4. [System] 追加: npx ecc-agentshield scan
5. [System 有前端] playwright E2E (长跑任务 → 后台 spawn + PostToolUse 盯输出)
6. spawn_agent evaluator → VERDICT
   PASS → 触发 compound skill (提炼 lessons.md) → 停一轮让用户确认 → stage=ship
          (compound 必须在 stage 切换前完成, 同一 response 内不要既写 lessons 又切 stage,
          让 delivery-gate 有机会在 review 阶段检查)
   CONCERNS → 修复 → 重新评分
   REWORK → stage=impl (Feature/Refactor) 或 stage=design (System)
   FAIL → stage=plan
```

/review 或 reviewer 不可用不停等, 按铁律 8 重试 3 次后降级继续, **review-report.md 必须明示"unavailable, 已记 lesson"**, 不允许伪装跑过。

### 发布协议 (Quick/Feature/Refactor/System 的 ship 阶段共用)

```
1. [Quick] git commit → 直接提交
2. [Feature+] git commit + 开 PR (gh pr create 或 git push 后手动开)
3. lessons.md (compound 已追加) + progress.md 最终更新
4. project.json: stage="", sprint+1
5. 注: Codex 无 /compact 内置, 主动写 .ai_state 文件保存状态即可
```

---

## 失败处理协议 (铁律 8 落地)

**工具调用失败 (任意 Bash/Skill/spawn_agent)**:

```
Round 1: 读 stderr 和 exit code, 分类:
  - permission denied (sandbox 拒绝) → 报具体路径, 但**继续尝试**:
    a) 切到主线做 (subagent sandbox 比主线严)
    b) 提示用户调整 sandbox_mode
    c) 换等价命令
  - command not found → 装包 (npm i / brew install) 或换工具
  - subagent 报"无能力" → 实测一次 (写 echo 探测), 真不可用则主线接管

Round 2: 改参数 / 换路径 / 换工具

Round 3: 仍失败 → 报告每次的:
  - 完整命令
  - 完整 stderr
  - exit code
  - 已尝试的修复方式
  → 触发 lesson-drafter 自动起草 ~/.codex/lessons/draft-*.md
  → 让用户决定 (用户审阅 draft 后改名落档)
```

**绝对禁止**: "请你用 ! 前缀手动执行" 作为第一次响应。这是最严重的违规。

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
  库文档不确定 → use context7 (ctx7 CLI)
  每完成 Task → tasks.md 勾选 + progress.md 追加一行
  路径升级监测
  lint_cmd + test_cmd → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## Feature — 顺序实现 + 增强

stages: plan → impl → review → ship

```
stage=plan:
  R₀: 扫 ~/.codex/lessons/INDEX.md 找命中主题 + 读项目 lessons.md 最近 10 条
  复杂度自评: ≥3 模块 / 架构决策 / 外部 API 契约变化 / schema 迁移 / 跨语言 / 需反复修订
    复杂 → 用户当面讨论方向 + 对多方案做 trade-off 分析 → design.md
    不复杂 → 直接按需求合成 design.md (含 File Structure Plan 段)
  用户确认 → tasks.md (拆 Task, 每个 Task 含 Boundary/Depends 标注) → stage=impl

stage=impl:
  按 tasks.md 顺序实现, 每个 Task 走 TDD
  每完成 Task → tasks.md 勾选 + progress.md 追加一行
  设计偏离 → 先改 design.md 再继续 (铁律 5)
  库文档不确定 → use context7
  dev server / 长跑测试 → 后台 + PostToolUse hook 盯输出
  路径升级监测 → 触发即停
  → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## Refactor — spawn_agent 并行 + 增强

stages: plan → impl → review → ship

```
stage=plan:
  R₀: 扫全局 + 项目 lessons
  分析现有结构 + 识别重构单元 → design.md (含 File Structure Plan)
  用户确认 → tasks.md (拆成可并行单元, Boundary/Depends 清晰) → stage=impl

stage=impl:
  Task 可并行 → spawn_agent generator 并行做 (同模式 Task 成组)
    每个 worker: 隔离 sandbox / TDD / 自己跑测试
    主线: wait_agent 收集 + 每组结束后合并
    Boundary 内任一 worker 越界 → 整组停, 主线决定
  Task 强耦合 → 串行做
  每完成 Task → tasks.md 勾选 + progress.md 追加
  路径升级: 发现需要新增模块 → 升 System
  → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## System — 全链

stages: plan → design → impl → review → ship

```
stage=plan:
  R₀: 扫全局 + 项目 lessons
  需求提取: 用户访谈式对话, 问边界条件 / 非功能需求 / 失败模式
  发散方向: 至少 3 个方案, 对比 trade-off → design.md (只到方案级)
  用户确认方向 → stage=design

stage=design:
  架构定稿: 组件边界 / 数据流 / 接口契约 / 失败处理 / File Structure Plan
  spawn_agent reviewer → 架构交叉审查 → 回到主线合并
  (可选) 前端有 UI → 单独 design review
  → 合成 tasks.md (Boundary/Depends) → 用户确认 → stage=impl

stage=impl:
  按 Task 性质选方式:
    批量同模式 → spawn_agent generator 并行
    复杂独立 → 主线串行
    不确定 → 主线试做一个, 定模式后 spawn_agent 复制
  每完成 Task → tasks.md 勾选 + progress.md 追加
  设计偏离 → 先改 design.md 再继续
  全部完成 → stage=review

stage=review: → 审查协议 (含 ECC + E2E, 长跑任务后台 + 盯输出)
stage=ship: → 发布协议
```

---

## 状态管理

project.json: path, stage, sprint, tech_stack, test_cmd, build_cmd, lint_cmd, dev_cmd, conventions, gotchas

合法 path: Quick, Feature, Refactor, System (Hotfix/Bugfix 不写 project.json)
合法 stage: plan, design (System only), impl, review, ship, "" (完成)

**.ai_state/ 文档职责 (铁律 5, 与 CC 端完全一致的 schema)**:
- 写端: project.json (vibe-init + 路由) / tasks.md (plan + impl 勾选) / progress.md (impl 每 Task 追加) /
  design.md (plan + impl 偏离时更新) / handoff.md (跨模型/跨 worker 临时) / lessons.md (compound 写) /
  reviews/sprint-N.md (V 阶段写) / hook-trace.jsonl (hooks 自动)
- 读端: R₀ 读 project/progress/tasks/项目 lessons 最近 10 + 全局 lessons INDEX /
  plan 读 lessons / impl 读 design 对照 / review 读 design + previous reviews /
  compound 读 reviews + diff 写 lessons

**~/.codex/lessons/ 全局工具链经验 (铁律 8 触发的失败自动起草)**:
- 写端: lesson-drafter hook (自动 draft) + 用户手动 (改 draft 名落档)
- 读端: R₀ 全局开头扫 INDEX.md, 主题命中再读对应文件

delivery-gate (Stop hook) 在 stage="review" 时检查质量门 (Feature+ 要求外部审查, Quick 不要求)。
长任务中 → 主动写 .ai_state 保存状态 (Codex 无 PreCompact hook 兜底)。

不间断工作: 不确定用什么库 → use context7。不确定现有代码 → 直接读。不确定测试怎么跑 → 读 project.json test_cmd。
只在以下情况停: 方案需用户确认 (plan 阶段), VERDICT 需判断 (review 阶段), 真正的阻塞 (失败 3 次后)。
