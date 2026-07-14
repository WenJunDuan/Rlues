---
name: athena-runtime-verify
description: |
  PACE impl 后的运行时验证环 (v9.8.0 新). 用官方 /goal 承载"实跑接口→自测自改→模拟环境/数据"自驱循环, 补 PACE 只单测不实跑的洞.
  System/Refactor 强制, Feature 可选, Bugfix/Quick/Hotfix 跳过.
  Loop Engineering 落地: DOER (generator 改代码) + CHECKER (/goal supervisor + delivery-gate), 不自批不自造 loop.
---

# /athena-runtime-verify — 运行时验证环 (v9.9.2)

## 为什么存在 (痛点)

PACE 到 impl 为止, review 三件套 + 单测只验证 **"我们想的问题实现没 / 单测过没"**, 不验证 **实际运行**.
代码单测全绿 ≠ 真实接口跑得通 / 边界数据不炸 / 换个环境不挂.
本 skill 在 impl 与 review 之间插一个 **运行时验证环**: 写完 → 实跑 → 自测自改 → 直到真能跑.

把"人盯着跑测试、贴日志、让它改"这件事, 换成 **系统自己跑、自己发现、自己改** (Loop Engineering).

## 触发 (按 PACE 级别)

| 路径 | runtime-verify | /goal 承载范围 |
|---|---|---|
| Hotfix | 跳过 (救火无时间) | — |
| Bugfix / Quick | 跳过 (改动小, 单测够) | — |
| Feature | **可选** (主 agent 判断: 碰外部接口 / 有状态 / 多环境 → 做) | impl+runtime (可选) |
| Refactor | **强制** | impl+runtime |
| System | **强制 + 完整 Sprint** | 全程 PACE |

> 不在小改动上强制 (铁律[不过度工程]). 单测能覆盖的别上 /goal, 杀鸡用牛刀。

## 核心: 用官方 /goal 承载, 不自造 loop

官方 `/goal` (CC 2.1.139+) 就是现成 loop 引擎: observe-act-observe, 独立 supervisor 审计 [官方 code.claude.com/docs/en/goal].
本 skill **不重新发明 loop**, 只把"运行时验证"写成一个 /goal 完成条件, 让 CC 自己跑到完成.

### Step 0 · 开环前自检 (Loop Readiness · 借 cobusgreyling/loop-engineering loop-audit)

把 /goal 这种自驱 loop 放出去前, agent 先给自己打分 —— 这是 "agent in loop and check" 把 check **前移**:
让 loop 跑之前就有能说 no 的东西, 而不是烧完 token 才发现没护栏。三项全绿才进 Step 1。

| 自检项 | 不通过则 |
|---|---|
| **CHECKER 能说 no?** 有 test / typecheck / lint / delivery-gate 能判失败 | 无硬验证 → 先补一个会失败的断言再开环 (没有 no 的 loop 会安静地烧钱) |
| **预算护栏有硬数字?** turn 上限 + (大任务) token/时间预算 | 没写 → 补 "Stop after N turns"; 大任务额外估 token (借 loop-cost 思路) |
| **状态落盘点?** 进展写 .ai_state 而非只在 context | 不落盘 → loop 一断片就失忆; 配 /athena-checkpoint 固化接续点 |

> 这是把 loop-audit 的 "Loop Readiness Score" 做成 agent 自评的一次性 gate —— 不引外部 CLI, 不自造轮子, 只把"开环前该问的三件事"固化成动作。

### Step 1 · 主 agent 设 /goal (impl 完成后)

完成条件三件套 (官方, ≤4000 字符):

1. **可测终态**: 实跑结果可判定 (HTTP 200 / 退出码 0 / 边界用例全过 / 响应字段匹配)
2. **stated check** (Claude 怎么证明 — 见下方陷阱): 把实跑命令 + 输出晒进 transcript
3. **约束 + turn 上限护栏**: 改哪些不能动 + "Stop after N turns" (/goal 无内建 token 预算, 上限必写)

示例 (后端 API):
```
/goal 对本 sprint 新增的 /api/refresh 端点做运行时验证, 直到:
  (a) 运行 `curl -s -X POST localhost:3000/api/refresh -d @test/normal.json | jq .status` 输出 200;
  (b) 5 个边界用例 (空 token / 过期 token / 篡改签名 / 并发刷新 / 超长 payload) 各跑一次, 把命令和输出贴进对话, 每个都返回预期错误码而非 500;
  (c) 测出的每个问题都已改代码并复跑通过.
  约束: 只动 src/api/ 和 src/auth/, 不碰 .ai_state. Stop after 25 turns.
```

### ⚠️ /goal supervisor 只读 transcript (致命陷阱)

官方明确: **supervisor 只判断 Claude 在对话里实际展示出来的东西, 不读文件、不跑命令**.
→ 完成条件必须写成 **"Claude 输出能演示的"**, 每次实跑把 **命令 + 输出** 晒进 transcript.

| ❌ 错误 (supervisor 看不到) | ✅ 正确 (晒进 transcript) |
|---|---|
| "接口测试通过" | "运行 `curl ... \| jq .status` → 输出 `200`" |
| "边界都覆盖了" | 5 个用例的实跑命令 + 实际输出逐条贴出 |
| "改完没问题了" | 改后复跑命令 + 输出, 证明从 fail 变 pass |

### Step 2 · agent 在 /goal 循环内自驱 (DOER + CHECKER)

每轮 agent 自己决定下一步 (这就是你说的"自己给自己提要求"):

- **写测试场景**: 实际接口调用 / 模拟数据 (正常 + 边界 + 异常) / 不同环境 (空库 / 满库 / 慢网络)
- **环境矩阵 (v9.9.0)**: `_index.tools_available.vm_available=true` → 先 `/athena-vm doctor` 自检,
  然后关键场景在远程 VM 复跑一轮 (`ssh athena-vm-{name} 'cd {workdir} && ...'`) —
  干净环境暴露隐式依赖, 真实发行版暴露平台差异; ssh 命令 + 远端输出照旧晒进 transcript.
  VM 不通 → 降级回本机模拟, runtime-verify.md 里记一行"VM 未覆盖"进 Reflect
- **实跑** (按类型选已装插件/工具):
  - 前端 / E2E → `$playwright` skill / 官方 `playwright-skill` 插件 (启 dev server + 浏览器驱动 + 断言 + 可复跑测试)
  - 后端 / API → `curl` / 真实 HTTP 调用 / 测试库真实读写
  - CLI → 实际命令执行 + 退出码 + stdout 断言
- **测出问题 → 自己改代码 → 复跑** (自测自改)
- 循环到完成条件满足 → supervisor 独立审计

### Step 3 · 执行者判定 (CC /goal 主路径)

默认 **CC /goal** (本平台). 理由: /goal 是有状态连续 loop + 自带 supervisor; codex exec 每次独立 session 断片、无 supervisor 层; 交互式 CC 在订阅内.
**codex 特例**: System 级密集测试想省 token / 隔离 → impl 完成后 `/codex:transfer` 移交 CX 端跑重测试环 (见 orchestration M5c), opt-in. 不默认。

## Step 4 · reflect (写完先自测, 再想哪里没完善)

runtime-verify 跑完, 触发一次 **结构化反思** (Loop Engineering 的"系统自己发现任务"):

- 对照 design.md 验收 + 实跑中暴露的现实 (性能 / 边界 / 兼容), 列 **"还有哪些没覆盖 / 没完善"**
- 写 `runtime-verify.md` 的 `## Reflect` 段
- 决策:
  - 发现实质缺口 → 回 impl 补 (写进 checklist.yaml 新 task)
  - 够了 → next_action=review

> 这一步把"人来发现还缺什么"换成"系统跑完自己反思". 不是 brainstorm 新需求 (那是项目级), 是 **本 sprint 落地完整性的自检**.

## 产出

`sprints/{slug}/runtime-verify.md`:
```markdown
# Runtime Verify — {slug}

## /goal 完成条件
[设的 goal 原文]

## 测试场景 (实跑)
| 场景 | 类型 | 命令 | 实际输出 | 判定 |
|---|---|---|---|---|
| 正常刷新 | API | curl... | 200 | ✅ |
| 过期 token | 边界 | curl... | 401 | ✅ |
| 并发刷新 | 异常 | ... | 改前 500→改后 409 | ✅ (已修) |
| 干净环境启动 | VM | ssh athena-vm-dev 'cd work && npm ci && npm start' | 启动 OK, 暴露缺 dotenv 依赖→已补 | ✅ (已修) |

## 自测自改记录
- 问题 1: 并发刷新返回 500 → 根因: 无锁 → 改: 加乐观锁 → 复跑 409 ✅

## Reflect (还有哪里没完善)
- [ ] 未覆盖: refresh token 轮换后的旧 token 失效 (design 没要求, 但实跑发现风险) → 回 impl 补 T7
- [x] 已确认完整: 正常 + 5 边界全过

## VERDICT: PASS | REWORK(回 impl)
```

## delivery-gate 联动

System/Refactor + stage=ship 时, delivery-gate 检查:
- `runtime-verify.md` 存在
- 含 `## 测试场景 (实跑)` 段且有实际输出 (不是空模板)

缺失 → block, 解锁动作: 跑 /athena-runtime-verify.

## 与单测 / review 的分工

| | 单测 (impl 内) | runtime-verify (本) | review (之后) |
|---|---|---|---|
| 验什么 | 函数逻辑对不对 | **真实运行跑不跑得通** | 代码质量 + spec 覆盖 |
| 怎么验 | mock + 断言 | 实跑接口 + 真实数据 + 自测自改 | 读代码 + 对照 design/checklist |
| 谁做 | generator | /goal 循环 (DOER+CHECKER) | reviewer/spec-compliance/evaluator |

## 不做

- ❌ 不自造 loop 引擎 (用官方 /goal)
- ❌ 不替代单测 (单测在 impl; 这里是运行时实跑)
- ❌ 不无限循环 (/goal turn 上限护栏必写, 撞上限停下来报告)
- ❌ Hotfix/Bugfix/Quick 不强制 (小改动过度工程)
- ❌ reflect 不发散成新需求 (那是项目级 brainstorm; 这里只查本 sprint 落地完整性)

## 例外

- 项目无可运行环境 (纯库 / 纯算法, 无接口无 UI): 降级为"用真实数据跑示例 + 边界", 不强求起服务
- `_index.skip_runtime_verify = true`: 跳过 (用户自负责, 不推荐 System/Refactor 跳)
