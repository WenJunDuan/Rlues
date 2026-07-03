# Testing Rules

## 原则
- 测试行为，不测试实现
- 每个功能至少 1 个 happy path + 1 个 edge case
- Mock 最小化

## 命名
- describe("模块名")
- it("should 行为描述 when 条件")

## 默认静默
除非用户明确要求，不自动运行测试/编译。
