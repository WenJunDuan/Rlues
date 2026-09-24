---
name: pace
effort: xhigh
description: >
  工作流路由器。收到开发任务时触发。按任务复杂度路由到 6 条路径，编排 CC 工具 + 增强节点。
---

# PACE — 6 路径路由器 (v9.5)

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
| Refactor | 10-50  | /batch                | superpowers + 交叉审查   | 是              |
| System   | 20+    | /feature-dev + /batch | 全增强                   | 是              |

Quick+ 路由完成 → project.json {path, stage, sprint} → 告知用户。

---

## 跨平台路由建议 (v9.5 新增, D3)

某些任务在 Codex 上比 CC 更经济/更准:

| 信号 | 建议 |
|------|------|
| 任务以终端命令为主 (build/test/grep/sed/find) | Codex Terminal-Bench 比 CC 强 12pp，考虑用 codex-plugin-cc 委派 |
| 大量重复改写 (改 100 个文件同样 import 路径) | Codex token 比 CC 少 3-4×，更经济 |
| 需要多 reviewer 互相 critique | CC 主跑 + /codex:adversarial-review 二审 (双模型 catch 单模型盲点) |
| 设计/架构判断 | CC Opus 4.7 略强，主跑 CC + 让 Codex review |

不强制——这是建议，不是规则。

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
**不自动升级**, 避免 Claude 借机扩 scope。

---

## PACE 节点插件推荐表 (v9.5 新增, best-fit, 不强依赖)

只有装了对应插件才用; 没装就走 CC 原生流程。**vibe-setup 检测后只显示已装的**——不诱导。

| 节点 | 推荐插件 (按场景) |
|------|-------------------|
| **Hotfix** | metronome (防跳步走捷径) |
| **Bugfix** | debugger / bug-fix / metronome |
| **Quick** | superpowers (brainstorm) / context7 (查文档) |
| **Feature 实现** | superpowers TDD + subagent dev / dev-workflows / context7 |
| **Feature 审查** | codex-plugin-cc / agent-peer-review / local-review |
| **Refactor** | superpowers / TypeScript LSP / Rust LSP / ast-grep |
| **Refactor 审查** | codex-plugin-cc / AgentLint |
| **System 实现** | superpowers / shipyard (IaC) / mcp-builder |
| **System 审查** | codex-plugin-cc / agent-peer-review |
| **跨节点** | claude-mem (跨 session 记忆, 替代删除的全局 lessons) / context-mode (大输出 sandbox 化) |

---

## 共享协议

### 审查协议 (Quick/Feature/Refactor/System 的 review 阶段共用)

```
1. /review → 第一份审查
2. [Feature+] /codex:review [--base main] [--wait] → 第二份审查
   → 必须看到真实 codex job ID 或命令输出 (铁律 6: 完成度证据)
   → 调用失败 → 失败处理协议 (见下)
   → 对比共识/分歧 → 合并修复清单 → 一次性修
3. [System] 追加: /codex:adversarial-review --base main <focus> + npx ecc-agentshield scan
4. [System 有前端] superpowers /qa + playwright E2E (用 Monitor 盯 E2E runner 输出)
5. /simplify → 清理
6. @evaluator → VERDICT
   PASS → 触发 compound skill (提炼 .ai_state/lessons.md) → 停一轮让用户确认 → stage=ship
          (compound 必须在 stage 切换前完成, 不要同一 response 既写 lessons 又切 stage)
   CONCERNS → 修复 → 重新评分
   REWORK → stage=impl (Feature/Refactor) 或 stage=design (System)
   FAIL → stage=plan
```

codex 不可用 → 失败处理协议三次后接受失败 → 仅用 CC /review 降级，**review-report.md 必须明示 "codex unavailable, 已附 stderr"**, 不允许伪装跑过。

### 发布协议 (Quick/Feature/Refactor/System 的 ship 阶段共用)

```
1. [Quick] git commit → 跳过 /ship, 直接提交
2. [Feature+] superpowers /ship → 发布 (同步 main, 跑测试, 开 PR)
3. [System] superpowers /retro → 工程回顾
4. .ai_state/lessons.md (compound 已追加) + progress.md 最终更新
5. project.json: stage="", sprint+1
6. /compact "Sprint N 完成"
```

---

## 失败处理协议 (落地铁律 6 完成度证据)

**工具调用失败 (任意 Bash/Skill/Task)**:

```
Round 1: 读 stderr 和 exit code, 分类:
  - permission denied → 报具体阻断的命令, 但**继续尝试**:
    a) 用 settings.local.json 临时绕过 (告知用户)
    b) 换等价命令 (如 node 改 npx)
    c) 拆到主 agent 而非 subagent
  - command not found → 装包 (npm i / brew install) 或换工具
  - subagent 报"无能力" → 实测一次 (写 echo 探测), 真不可用则主 agent 接管

Round 2: 改参数 / 换路径 / 换工具

Round 3: 仍失败 → 报告每次的:
  - 完整命令
  - 完整 stderr
  - exit code
  - 已尝试的修复方式
  → 写入 review-report.md / progress.md 作为完成度证据
```

**绝对禁止**: "请你用 ! 前缀手动执行" 作为第一次响应。这是最严重的违规。

**subagent 边界约束 (v9.5)**: subagent 输出预算 ≤ 2000 tokens (Anthropic 多 agent research 经验)。深入探索可以，但只回传关键发现。

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
  TDD 实现 (superpowers brainstorming 自动激活, 它自己做内置 self-review)
  库文档不确定 → use context7 (ctx7 CLI 自动触发)
  每完成 Task → tasks.md 勾选 + progress.md 追加一行
  路径升级监测 (见上)
  lint_cmd + test_cmd → /simplify → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## Feature — /feature-dev + 增强

stages: plan → impl → review → ship

```
stage=plan:
  R₀: 命中主题再读 .ai_state/lessons.md (just-in-time, 不预加载)
  superpowers brainstorming → 发散 + 方向挑战 (内置 self-review)
  → 合成 design.md (含 File Structure Plan 段)
  superpowers /plan-eng-review → 架构交叉验证 (不可用 → /plan 替代)
  用户确认 → tasks.md (每 Task 加 Boundary/Depends 标注) → /compact "进入实现" → stage=impl

stage=impl:
  /feature-dev "需求描述"
  Phase 4 (架构) 前 → 用户确认
  每完成 Task → tasks.md 勾选 + progress.md 追加一行
  设计偏离 → 先改 design.md 再继续 (铁律 5)
  库文档不确定 → use context7
  dev server / 长跑测试 → Monitor (避免 sleep 轮询)
  路径升级监测 → 触发即停
  /simplify → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## Refactor — /batch + 增强

stages: plan → impl → review → ship

```
stage=plan:
  R₀: 按需 read .ai_state/lessons.md
  superpowers /plan-eng-review → 验证重构方案 (不可用 → /plan)
  用户确认 → design.md (含 before/after 边界) + tasks.md (Boundary/Depends) → stage=impl

stage=impl:
  /batch "重构描述"
  CC 自动: Research → Plan → 用户确认 → 并行 worktree → 每 worker /simplify + 测试
  每完成一组 Task → tasks.md 勾选 + progress.md 追加
  路径升级: 发现需要新增模块 → 升 System
  → stage=review

stage=review: → 审查协议
stage=ship: → 发布协议
```

## System — 全链

stages: plan → design → impl → review → ship

```
stage=plan:
  R₀: 按需 read .ai_state/lessons.md
  superpowers /office-hours → 需求提取
  superpowers brainstorming → 发散 + 方向挑战
  → 合成 design.md → 用户确认 → stage=design

stage=design:
  superpowers /plan-eng-review → 架构锁定
  superpowers /plan-design-review → 设计审查 (有 UI 时)
  design.md 必含 File Structure Plan (定义模块边界) → tasks 据此拆
  → 合成 tasks.md (每 Task 含 Boundary/Depends) → 用户确认 → stage=impl

stage=impl:
  按 Task 性质选工具:
    批量同模式 → /batch 并行
    复杂独立 → /feature-dev
    跨模型委托 → /codex:rescue "<prompt 内容>" [--background] [--model gpt-5.4-mini]:
      Step 1: 用 find/Read 构造 handoff.md (实际文件树 + 相关代码片段 + 验收标准)
      Step 2: Read handoff.md 全文 → 作为字符串参数传给 /codex:rescue
              (Codex 不会自动读 handoff.md, 必须显式传入)
      Step 3: --background 时用 Monitor 盯 job 输出文件 + /codex:status 查状态
      Step 4: /codex:result 取回 → 验证引用的文件 test -f → 不存在的结论作废
      Step 5: 调用失败 → 失败处理协议三轮 → 真失败则 @generator 接管
      幻觉>50% → 降级到 @generator
  每完成 Task → tasks.md 勾选 + progress.md 追加
  设计偏离 → 先改 design.md 再继续
  /compact (每完成一组)
  全部完成 → /simplify → stage=review

stage=review: → 审查协议 (含 adversarial + ECC + /qa + E2E 用 Monitor)
stage=ship: → 发布协议 (含 /retro)
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

**跨项目记忆已删除**: Hermes 不做。需要的话装 claude-mem 或 superpowers。

delivery-gate (Stop hook) 在 stage="review" 时检查质量门 (Feature+ 要求外部审查, Quick 不要求)。
阶段转换 + 长任务中 → 主动 `/compact`，不等 context 满。

不间断工作: 不确定用什么库 → use context7。不确定现有代码 → Read 看。不确定测试怎么跑 → 读 project.json test_cmd。
只在以下情况停: 方案需用户确认 (plan 阶段), VERDICT 需判断 (review 阶段), 真正的阻塞 (失败 3 次后)。
