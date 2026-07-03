---
name: tdd
description: TDD — E阶段每个Task
context: main
---
## RED→GREEN→REFACTOR
1. 写失败测试 → 运行确认失败
2. 最小实现 → 运行确认通过
3. 清理 → 确认仍通过

测试命令: package.json→Cargo.toml→go.mod→pytest | 找不到→问用户
规则: 1:1对应, 每Task commit, 不测框架本身
