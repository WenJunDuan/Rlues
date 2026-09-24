---
name: pace
description: >
  工作流路由器。收到开发任务时触发。按任务复杂度路由到 6 条路径，编排 Codex 内置工具 + spawn_agent。
---

# PACE — 6 路径路由器 (v9.5 Codex)

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

## Codex 平台优势 (v9.5 新认识)

Codex 在以下场景比 CC 更好用:
- **Terminal-Bench 77.3% vs CC 65.4%** (12pp 优势)
- **token 消耗 0.25-0.33×** 同任务
- **插件市场 90+ 插件** (3/27/2026 上线)

如果任务以终端命令为主, 或需要大量重复改写, 优先 Codex 端处理。
反向: 设计/架构判断, CC Opus 4.7 略强, 主跑 CC + 让 Codex /review。

---

## 路径升级机制 (impl 阶段持续监测)

写代码过程中发现实际复杂度超出当前路径 → 暂停, 询问用户升级:

| 升级触发信号 | 当前 → 建议 |
|------------|-----------|
| 需要改数据库 schema | * → System |
| 跨 3+ 模块的接口变更 | Feature → System |
| 实际改文件数 > 当前路径上限的 50% | Quick → Feature, Feature → Refactor/System |
| Refactor 中发现需要新增模块/重新设计接口 | Refactor → System |

**不自动升级**, 避免 Codex 借机扩 scope。

---

## PACE 节点插件推荐表 (v9.5 新增)

Codex 3/27/2026 上线插件市场, 可以 `@plugin-creator` scaffold 自定义插件:

| 节点 | 推荐 |
|------|-----|
| Quick / Feature | superpowers (跨 session 记忆) / context7 (查文档) |
| 集成类 | Slack / Linear / Notion / Figma / GitHub / Sentry plugins |
| 跨项目记忆 | superpowers (`/using-superpowers` 命令) |
| 自建技能 | `@plugin-creator` 内置 scaffold |

`/plugins list` 看已装的; vibe-setup 检测后只显示已装的——不诱导。

---

## 共享协议

### 审查协议 (Quick/Feature/Refactor/System 的 review 阶段共用)

```
1. 主力自审: 走一遍 diff, 测试全跑, 自己先挑毛病
2. [Feature+] /review 内置 → Codex 启动独立 reviewer 看 diff (一个视角)
3. [Feature+] spawn_agent reviewer (~/.codex/agents/reviewer/) → 第二个视角
   → 必须真实 tool_use (铁律 6 完成度证据), 不允许伪造
   → 调用失败 → 失败处理协议三轮 → 真失败则降级到主线 + 写明 review-report.md
4. [System] 追加 ECC + E2E (有 UI)
5. /simplify
6. spawn_agent evaluator (~/.codex/agents/evaluator/) → VERDICT
   PASS → 触发 $compound 提炼 .ai_state/lessons.md → 停一轮让用户确认 → stage=ship
   CONCERNS → 修复 → 重新评分
   REWORK → stage=impl (Feature/Refactor) 或 stage=design (System)
   FAIL → stage=plan
```

### 发布协议 (Quick/Feature/Refactor/System 的 ship 阶段共用)

```
1. [Quick] git commit → 跳过, 直接提交
2. [Feature+] 主线发布 (同步 main, 跑测试, 开 PR)
3. [System] 工程回顾 (写 retro.md)
4. .ai_state/lessons.md ($compound 已追加) + progress.md 最终更新
5. project.json: stage="", sprint+1
6. 主动写 .ai_state 保存状态 (Codex 无 compact 机制)
```

---

## 失败处理协议 (落地铁律 6 完成度证据)

**工具调用失败 (任意 Bash/spawn_agent/Skill)**:

```
Round 1: 读 stderr 和 exit code, 分类:
  - permission denied → 报具体阻断原因, 但**继续尝试**:
    a) 调整 sandbox / approval 配置
    b) 换等价命令 (如 node 改 npx)
    c) 拆到主线而非 spawn_agent
  - command not found → 装包或换工具
  - spawn_agent 报"无能力" → 实测一次 (echo 探测), 真不可用则主线接管

Round 2: 改参数 / 换路径 / 换工具

Round 3: 仍失败 → 报告每次的:
  - 完整命令
  - 完整 stderr
  - exit code
  - 已尝试的修复方式
  → 写入 review-report.md / progress.md 作为完成度证据
```

**绝对禁止**: "请你用 ! 前缀手动执行" 作为第一次响应。

**spawn_agent 边界约束 (v9.5)**: spawn_agent 输出预算 ≤ 2000 tokens。深入探索可以，只回传关键发现。

---

## Hotfix — 无仪式

```
直接定位 → Edit → test_cmd (有就跑) → git commit → 完
```

## Bugfix — 定位根因 + TDD (无 stage)

```
定位根因: 复现 → grep/find 找症状源头 → 看 stack trace
TDD: 写回归测试(复现) → 修复 → 测试通过
lint_cmd (有就跑) → /review 内置 → git commit
自愈: 修不好 → 重新定位 (限 3 轮) → 3 轮后通知用户
```

## Quick

stages: impl → review → ship

```
stage=impl:
  Explore: 读要改的文件 + 调用方
  TDD 实现 (主力)
  库文档不确定 → use context7
  每完成 Task → tasks.md 勾选 + progress.md 追加一行
  路径升级监测
  lint_cmd + test_cmd → /simplify → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## Feature — 顺序实现 + 增强

stages: plan → impl → review → ship

```
stage=plan:
  R₀: 命中主题再读 .ai_state/lessons.md (just-in-time)
  brainstorm + 多方案 trade-off
  → 合成 design.md (含 File Structure Plan 段)
  用户访谈对齐细节 (CLI/IDE/Web/价格)
  用户确认 → tasks.md (Boundary/Depends 标注) → stage=impl

stage=impl:
  顺序实现 (按 tasks.md 一条条做)
  Phase 4 (架构) 前 → 用户确认
  每完成 Task → tasks.md 勾选 + progress.md 追加一行
  设计偏离 → 先改 design.md 再继续 (铁律 5)
  库文档不确定 → use context7
  路径升级监测 → 触发即停
  /simplify → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## Refactor — spawn_agent 并行 + 增强

stages: plan → impl → review → ship

```
stage=plan:
  R₀: 按需 read .ai_state/lessons.md
  超声学验证: spawn_agent reviewer 独立审查重构方案
  用户确认 → design.md (含 before/after 边界) + tasks.md (Boundary/Depends) → stage=impl

stage=impl:
  按 Task 拆分 (同模式批量, 可并行):
    主线写 generator handoff → spawn_agent generator (~/.codex/agents/generator/)
    并行启动 N 个 generator 实例 (N ≤ 4)
    每 generator 完成 → 主线 review + 测试
    设计偏离 → 先改 design.md 再继续
  每完成一组 Task → tasks.md 勾选 + progress.md 追加
  路径升级: 发现需要新增模块 → 升 System
  /simplify → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## System — 全链

stages: plan → design → impl → review → ship

```
stage=plan:
  R₀: 按需 read .ai_state/lessons.md
  brainstorm 多方案 → 用户访谈 → trade-off
  spawn_agent reviewer 做架构交叉审查 (System 强制)
  → 合成 design.md → 用户确认 → stage=design

stage=design:
  锁定架构 (用户确认)
  design.md 必含 File Structure Plan (定义模块边界) → tasks 据此拆
  → 合成 tasks.md (每 Task 含 Boundary/Depends) → 用户确认 → stage=impl

stage=impl:
  按 Task 性质选工具:
    批量同模式 → spawn_agent generator 并行
    复杂独立 → 主线顺序
    跨模型委托 → 主线写 handoff.md → 显式调用工具
  每完成 Task → tasks.md 勾选 + progress.md 追加
  设计偏离 → 先改 design.md 再继续
  长任务点主动写 .ai_state (Codex 无 compact)
  全部完成 → /simplify → stage=review

stage=review: → 审查协议 (含 ECC + E2E)
stage=ship: → 发布协议 (含 retro)
```

---

## 状态管理

project.json: path, stage, sprint, tech_stack, test_cmd, build_cmd, lint_cmd, dev_cmd, conventions, gotchas

合法 path: Quick, Feature, Refactor, System (Hotfix/Bugfix 不写 project.json)
合法 stage: plan, design (System only), impl, review, ship, "" (完成)

**.ai_state/ 文档职责 (铁律 5, just-in-time)**:
- 写端: project.json (vibe-init + 路由) / tasks.md (plan + impl 勾选) / progress.md (impl 每 Task 追加) /
  design.md (plan + impl 偏离时更新) / handoff.md (跨模型/跨 worker 临时) / lessons.md (compound 写, append-only) /
  reviews/sprint-N.md (V 阶段写) / hook-trace.jsonl (hooks 自动)
- 读端 (just-in-time, 不预加载):
  - 必读: project.json
  - 阶段=impl/review → progress.md + tasks.md
  - 任务命中 lessons 主题 → lessons.md
  - plan 阶段 → 命中再读 lessons / impl 读 design 对照 / review 读 design + previous reviews

**跨项目记忆已删除**: Hermes 不做。需要的话装 superpowers (`/using-superpowers`)。

delivery-gate (Stop hook) 在 stage="review" 时检查质量门 (Feature+ 要求外部审查, Quick 不要求)。
长任务点主动写 .ai_state (Codex 无 compact 机制)。

不间断工作: 不确定用什么库 → use context7。不确定现有代码 → Read 看。
只在以下情况停: 方案需用户确认 (plan/design 阶段), VERDICT 需判断 (review 阶段), 真正的阻塞 (失败 3 次后)。
