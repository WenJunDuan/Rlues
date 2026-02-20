---
name: tdd
description: TDD 循环 — RED-GREEN-REFACTOR
context: main
---
Path B+: RED (写失败测试) → GREEN (最小实现通过) → REFACTOR (优化)
Path A: 现有测试通过即可, 不强制 TDD。
Path C+: TDD 强制, 每个子任务独立 RED-GREEN 循环。
Commit 策略: RED 不 commit, GREEN commit, REFACTOR commit。
