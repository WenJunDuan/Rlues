---
name: tdd
description: 测试驱动开发 — E 阶段, 先写测试后实现
context: main
---
## 触发: E(执行) 阶段

## 分级策略
- **Level 1** (Path A): 功能验证, 可手动测试
- **Level 2** (Path B): 单元测试 + 集成测试, RED→GREEN→REFACTOR
- **Level 3** (Path C+): + E2E 测试, 测试覆盖率 >80%

## 步骤 (Level 2+)
1. 读 plan.md 当前任务
2. 写失败测试 (RED)
3. 写最小实现通过测试 (GREEN)
4. 重构 (REFACTOR)
5. 更新 doing.md 看板 (TODO→DOING→DONE)
6. git commit

## 测试命令自动检测
package.json scripts.test → npm test
pytest.ini/pyproject.toml → pytest
Cargo.toml → cargo test
go.mod → go test ./...
