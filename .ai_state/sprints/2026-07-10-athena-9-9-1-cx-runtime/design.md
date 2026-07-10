---
sprint_slug: "2026-07-10-athena-9-9-1-cx-runtime"
roadmap_item: "cx-runtime-contract"
path: "System"
created: "2026-07-10"
---

# Design — CX Runtime Contract

## Scope

实现总设计 `../2026-07-10-athena-9-9-1-release/design.md` 的 AC1、AC3–AC6、AC12、AC18–AC19 与 AC20 的“9.9.0 零改动”部分：复制 9.9.0 基线、先写失败 fixtures，再修 portable config、PostToolUse wire、assignment/lifecycle、delivery gate 与 native collaboration 文本契约。AC20 的发布身份与未来版本串由最终 validation sprint 关闭。

## TDD Sequence

1. 复制双端包，固定 base commit `5eb6189`。
2. 新增 validator/fixtures；保存空 provider、手工 context/compact、strict config/schema、字符串 response 假过、Start 绕过、gate 缺件、旧 orchestration 文本等红灯。
3. 仅修改 `codex/9.9.1` CX runtime 写集。
4. 用同一 fixtures 转绿；9.9.0 路径必须零 diff。

## Acceptance

- PostToolUse 不再默认 pass；不可确认状态为 unknown。
- raw Start 提供真实 agent_id；主线程用唯一未绑定 Start 与 task_name/role 完成握手；gate 按 agent_id/sprint 关联 Stop。
- Athena ship gate 对缺件、歧义、畸形、unknown-only 与 fail evidence 输入 fail-closed。
- config 使用内置 provider 与 catalog slug `gpt-5.6-sol`，不写空 endpoint 或手工 context 上限；skills.config 指向 `~/.agents/skills`。
- CX 热路径只描述 surfaced native collaboration tools，不出现 shell `spawn_agent`、`--cwd`、`assign_task`、裸 `wait`。

## Round 1

继承 release 总设计第一轮 critic 结论并已修订。

## Round 2

独立 critic 要求写死状态字段、JSONL schema、setup 分流、Athena 判定与 config 红灯范围；已在总设计 Round 3 修订。

## Round 3

独立 critic 最终复审 PASS；可进入 impl。

## Runtime Review 1

REWORK：v2 spawn 只返回 task_name，原 assignment 预写 agent_id 不可执行；evidence 非空检查会让 unknown/fail 假过。已按官方源码修订设计并新增 T6。
