# 代码规范 — VibeCoding Kernel v9.3.5

> 本规范适用于所有由 Agent 生成和审查的代码。违反任何 P0 规则将触发 REWORK。

---

## P0: 硬性规则 (违反 = REWORK)

### DRY — Don't Repeat Yourself
- 相同逻辑禁止出现两次。发现重复 → 立即提取为函数/模块/常量
- 魔法数字必须定义为命名常量 (`MAX_RETRY = 3`, 不是 `3`)
- 配置项存配置文件/环境变量, 不硬编码在源码中

### SRP — Single Responsibility Principle
- 每个函数只做一件事, 函数体不超过 40 行
- 每个模块/类只有一个变更理由
- 文件超过 300 行 → 必须拆分

### 安全
- 禁止硬编码密钥/密码/token
- 用户输入必须验证和转义 (SQL注入/XSS/命令注入)
- 使用 `execFileSync` 不用 `execSync` (防 shell 注入)
- 依赖项必须锁定版本

### 类型安全
- 禁止 `any` 类型 (TypeScript) — 用具体类型或 `unknown`
- 禁止 `as` 强制类型断言, 除非有注释说明为什么安全
- 函数参数和返回值必须有类型声明

---

## P1: 工程原则 (违反 = CONCERNS)

### KISS — Keep It Short And Simple
- 优先选择最简单的实现方案
- 不写"聪明"的代码 — 清晰胜过简短
- 嵌套不超过 3 层; 超过 → 提取函数或 early return
- 三元表达式不嵌套

### YAGNI — You Ain't Gonna Need It
- 只实现当前需求要求的功能, 不预测未来
- 不写"以防万一"的抽象层
- 不添加 spec 中未提及的功能

### SOLID (完整)
- **OCP**: 对扩展开放, 对修改关闭 — 用接口/策略模式, 不改已有代码
- **LSP**: 子类必须能替换父类, 不改变行为契约
- **ISP**: 接口小而专, 不强迫实现不需要的方法
- **DIP**: 依赖抽象, 不依赖具体实现

### 组合优于继承 (Composition Over Inheritance)
- 默认用组合 (has-a), 不用继承 (is-a)
- 继承层次不超过 2 层
- 需要共享行为时 → 用 mixin/trait/组合, 不是深继承

### 委托原则 (Delegation)
- 对象不应自己处理不属于其职责的事务
- 通过委托将任务分派给专门的对象

---

## P2: 质量标准 (影响评分但不阻断)

### 命名
- 变量/函数: camelCase, 语义化 (`getUserById` 不是 `getData`)
- 类/类型: PascalCase
- 常量: UPPER_SNAKE_CASE
- 布尔值: `is/has/should/can` 前缀
- 函数名用动词开头

### 错误处理
- 不吞异常 — catch 块必须有处理逻辑 (日志/重抛/降级)
- 异步操作必须有 try-catch 或 .catch()
- 边界条件: 空输入、超长输入、并发、网络中断

### 测试
- 新功能必须有对应测试 (TDD 优先)
- 测试覆盖: 正常路径 + 至少 2 个边界条件
- 测试命名: `should_[预期行为]_when_[条件]`
- Mock 外部依赖, 不 mock 被测模块内部

### 文档 (DYC — Document Your Code)
- 公共 API 必须有 JSDoc/TSDoc
- 复杂算法写 "为什么" 注释, 不写 "做什么" 注释
- README 包含: 安装、使用、API、示例
- 修改代码时同步更新相关文档

### 重构 (Refactor)
- 修 bug 时顺手重构周边代码 (Boy Scout Rule)
- 提取方法 > 重命名 > 内联 > 替换魔法数字 > 合并重复
- 重构必须有测试覆盖, 不改变外部行为

### Clean Code
- 不留注释掉的代码 — 用 git 管理历史
- 不留 TODO 超过 1 个 sprint — 要么做要么删
- import 按类型分组排序
- 文件末尾保留一个空行

---

## 评分维度对照

本规范直接映射到 4 维评分体系:

| 评分维度 | 对应规则 |
|:---|:---|
| Engineering Quality (30%) | SRP, SOLID, DIP, 组合优于继承, 委托 |
| Spec Compliance (30%) | YAGNI (不多不少), 测试 (验收标准) |
| Craft (20%) | KISS, 命名, Clean Code, 文档, 重构 |
| Robustness (20%) | DRY, 安全, 错误处理, 类型安全, 边界条件 |
