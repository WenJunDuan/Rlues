---
name: tdd
description: TDD 操作手册 — E 阶段每个 Task 使用
context: main
---
## 管道位置: E → 每个 Task 循环 RED→GREEN→REFACTOR

## 循环
1. **RED**: 写失败的测试 → 运行确认失败
2. **GREEN**: 写最小实现 → 运行确认通过
3. **REFACTOR**: 清理代码 → 运行确认仍然通过

## 测试命令检测
按优先级: package.json scripts.test → Cargo.toml → go.mod → pytest
找不到测试命令时 → 问用户

## 规则
- 测试文件和源码文件 1:1 对应
- 每个 Task 完成时 commit (feat/fix/refactor: 简述)
- 不要写测试来测试框架本身的功能
