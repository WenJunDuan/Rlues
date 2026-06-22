---
name: athena-runtime-verify
description: |
  PACE impl 后的运行时验证环 (v9.8.0 新, Codex). 用 Codex Goals 承载"实跑接口→自测自改→模拟环境/数据"自驱循环, 补 PACE 只单测不实跑的洞.
  System/Refactor 强制, Feature 可选, Bugfix/Quick/Hotfix 跳过.
  Loop Engineering 落地: DOER (generator 改) + CHECKER (Goals 完成判定 + delivery-gate), 不自批不自造 loop.
effort: high
attach_to_stages: [impl, runtime-verify, review]
---

# /athena-runtime-verify — 运行时验证环 (v9.8.0, Codex)

## 为什么存在 (痛点)

PACE 到 impl 为止, review + 单测只验证 "想的问题实现没 / 单测过没", 不验证 **实际运行**.
单测全绿 ≠ 真实接口跑得通 / 边界数据不炸 / 换环境不挂.
本 skill 在 impl 与 review 之间插 **运行时验证环**: 写完 → 实跑 → 自测自改 → 直到真能跑.
把"人盯着跑测试、贴日志、让它改"换成 **系统自己跑、自己发现、自己改** (Loop Engineering).

## 触发 (按 PACE 级别)

| 路径 | runtime-verify | Goals 承载范围 |
|---|---|---|
| Hotfix | 跳过 (救火) | — |
| Bugfix / Quick | 跳过 (单测够) | — |
| Feature | 可选 (碰外部接口/有状态/多环境 → 做) | impl+runtime (可选) |
| Refactor | 强制 | impl+runtime |
| System | 强制 + 完整 Sprint | 全程 PACE |

> 小改动不强制 (铁律[不过度工程]).

## 核心: 用 Codex Goals 承载, 不自造 loop

Codex Goals (0.133+ 默认开启 [官方 release 0.133]) 是 CX 端的 objective-driven loop: 持续执行直到完成条件满足.
本 skill 不重新发明 loop, 把"运行时验证"写成 Goals 完成条件, 让 Codex 自驱.

### Step 0 · 开环前自检 (Loop Readiness · 借 cobusgreyling/loop-engineering loop-audit)

把 Goals 这种自驱 loop 放出去前, 主 thread 先给自己打分 —— "agent in loop and check" 把 check **前移**:
让 loop 跑之前就有能说 no 的东西, 而不是烧完 token 才发现没护栏。三项全绿才进 Step 1。

| 自检项 | 不通过则 |
|---|---|
| **CHECKER 能说 no?** 有 test / typecheck / lint / delivery-gate 能判失败 | 无硬验证 → 先补一个会失败的断言再开环 |
| **预算护栏有硬数字?** turn/时间上限 (大任务) token 预算 | 没写 → 补上限; 大任务额外估 token (借 loop-cost 思路) |
| **状态落盘点?** 进展写 .ai_state 而非只在 context | 不落盘 → 一断片就失忆; 配 /athena-checkpoint |

> 把 loop-audit 的 "Loop Readiness Score" 做成 agent 自评的一次性 gate —— 不引外部 CLI, 不自造轮子。

### Step 1 · 主 thread 设 Goals (impl 完成后)

完成条件三件套:
1. **可测终态**: 实跑结果可判定 (HTTP 200 / 退出码 0 / 边界用例全过)
2. **stated check** (怎么证明 — 见陷阱): 把实跑命令 + 输出晒进对话
3. **约束 + turn 上限护栏**: 改哪些不能动 + turn/时间上限 (Goals continuation 撞 usage limit/重复 blocker 自动停, 但上限仍要写)

### ⚠️ 完成判定只看对话里展示的 (致命陷阱)

同 CC /goal: 完成判定基于 agent 在对话里**实际展示**的东西, 不读文件.
→ 完成条件必须写成"输出能演示的", 每次实跑把 **命令 + 输出** 晒进对话.

| ❌ 错误 | ✅ 正确 |
|---|---|
| "接口测试通过" | "运行 `curl ... \| jq .status` → 输出 200" |
| "边界都覆盖了" | 5 个用例的实跑命令 + 实际输出逐条贴出 |

### Step 2 · 主 thread 在 Goals 循环内自驱 (DOER + CHECKER)

每轮自己决定下一步 (即"自己给自己提要求"):
- **写测试场景**: 实际接口调用 / 模拟数据 (正常+边界+异常) / 不同环境
- **实跑** (按类型):
  - 前端 / E2E → config.toml 的 `browser@openai-bundled` + `computer-use@openai-bundled` plugin (启服务 + 浏览器驱动)
  - 后端 / API → `curl` / 真实 HTTP / 测试库真实读写 (shell)
  - CLI → 实际命令 + 退出码 + stdout 断言
- **测出问题 → 自己改 → 复跑** (自测自改)
- 循环到完成条件满足

### Step 3 · 执行者判定 (CX 本平台 Goals 主路径)

默认 **CX 本平台 Goals**. 密集测试想隔离/省 token → spawn_agent generator.toml 分派 (multi-agent v2), opt-in.

## Step 4 · reflect (写完先自测, 再想哪里没完善)

Goals 跑完, 触发结构化反思 (Loop Engineering "系统自己发现任务"):
- 对照 design.md 验收 + 实跑暴露的现实, 列 "还有哪些没覆盖 / 没完善"
- 写 runtime-verify.md 的 `## Reflect` 段
- 决策: 发现缺口 → 回 impl 补 (写进 checklist.yaml 新 task); 够了 → next_action=review

> reflect 不发散新需求 (那是项目级 brainstorm); 只查本 sprint 落地完整性.

## 产出

`sprints/{slug}/runtime-verify.md` (用 apply_patch 写): 含 `## /goal 完成条件` `## 测试场景 (实跑)` (表格: 场景/类型/命令/实际输出/判定) `## 自测自改记录` `## Reflect` `## VERDICT`.

## delivery-gate 联动

System/Refactor + stage=ship 时, delivery-gate.py 检查 runtime-verify.md 存在 + 含 `## 测试场景` 段. 缺失 → block.

## 与单测/review 分工

| | 单测 (impl) | runtime-verify (本) | review |
|---|---|---|---|
| 验什么 | 函数逻辑 | **真实运行** | 代码质量+spec |
| 怎么验 | mock+断言 | 实跑+真实数据+自测自改 | 读代码对照 design/checklist |

## 不做

- ❌ 不自造 loop (用 Codex Goals)
- ❌ 不替代单测 (单测在 impl)
- ❌ 不无限循环 (turn 上限护栏必写)
- ❌ Hotfix/Bugfix/Quick 不强制
- ❌ reflect 不发散新需求

## 例外

- 纯库/纯算法 (无接口无 UI): 降级为"真实数据跑示例 + 边界", 不强求起服务
- `_index.skip_runtime_verify = true`: 跳过 (不推荐 System/Refactor 跳)
