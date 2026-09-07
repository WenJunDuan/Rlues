---
name: spec-compliance
maxTurns: 70
description: |
  STUB 9.9.8 — 禁止 live 调度。Spec coverage 是一次多维 review 的第一维。
disable-model-invocation: true
---

每次任务最多 70 轮。到限前返回已完成内容、未提交改动、验证结果和剩余事项；未完成不得标记 PASS，不自动续派以绕过上限。

此角色已从 9.9.8 默认生命周期移除。不要 spawn spec-compliance。Spec coverage 由一次独立 review 的第一维承担。
