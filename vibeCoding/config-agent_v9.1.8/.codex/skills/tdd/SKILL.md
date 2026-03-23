---
name: tdd
description: TDD 操作手册 — E 阶段每个 Task
---
## 管道位置: E → 每个 Task 循环 RED→GREEN→REFACTOR

## 循环
1. **RED**: 写失败测试 → 运行确认失败
2. **GREEN**: 写最小实现 → 运行确认通过
3. **REFACTOR**: 清理 → 确认仍通过

## 测试命令检测
package.json scripts.test → Cargo.toml → go.mod → pytest
找不到 → 问用户

## 规则
- 测试文件和源码 1:1 对应
- 每个 Task 完成时 commit (conventional commits)
- 不测框架本身的功能
