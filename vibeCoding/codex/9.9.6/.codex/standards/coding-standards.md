---
effort: medium
attach_to_stages: [impl, review, polish]
attach_to_subagents: [generator, reviewer, polish_worker]
---

<important if="writing or reviewing code">
# Coding Standards · 代码规范

> 适用于所有由 Athena 路径生成 / 审查的代码.
> 违反 P0 → evaluator VERDICT=REWORK; ≥ 3 个 P1 → CONCERNS.

## P0 (硬性, 违反 = REWORK)

### DRY — Don't Repeat Yourself
- 相同逻辑禁止出现两次. 发现重复 → 立即提取为函数 / 模块 / 常量
- Magic number 必须定义为命名常量 (`MAX_RETRY = 3`, 不是 `3`)
- 配置项存配置文件 / 环境变量, 不硬编码在源码中

### SRP — Single Responsibility Principle
- 每个函数只做一件事, 函数体 ≤ 40 行
- 每个模块 / 类只有一个变更理由
- 文件 > 300 行 → 必须拆分

### 安全
- 禁止硬编码密钥 / 密码 / token
- 用户输入必须验证和转义 (SQL注入 / XSS / 命令注入)
- 子进程命令优先 `execFile` / `spawn` 数组形式, 不用字符串拼接 + shell=true
- 依赖项必须锁定版本

### 类型安全
- TypeScript: 禁止 `any`, strict mode 必开
- Python: 公开 API 必须有 type hints
- 异常必须有归宿: 信任边界统一处理, 或显式向上传播 (async/Promise 不允许 unhandled rejection); 禁止空 catch 与吞异常 — 不要求每层都 try-catch

### Sisyphus 完整性
- 任务清单 (plan.md) 中所有 Task 必须**全部完成**才能声明 stage=ship
- 不允许 "差不多了" — 要么全完成, 要么标 `blocked` 并说明原因

## P1 · 反过度工程 (铁律[反过度工程], 违反 = CONCERNS)

- 无第二消费者不抽象: 单实现禁止配接口/抽象类; 第二个消费者出现时再提取
- 无现实需求不加配置项/参数/扩展点/feature flag; spec 没要的泛化 = 删
- 防御只设在信任边界 (用户输入 / 外部 API / DB / 文件 / 网络 / 跨进程 / 权限面):
  - 边界内信任类型系统与已验证的不变量, 不逐层重复校验
  - 禁 blanket try-catch / 逐行 null 偏执 / "以防万一"的 fallback 分支
  - fail-fast: 内部不变量被破坏 = 立即抛错, 禁静默降级
- 判据: 删掉该抽象/分支/参数后测试仍全绿且无真实调用方 = 过度, 删
- 双向: 上述任何一条不构成削减信任边界防御的理由 (边界缺防御是 P0 安全项)

## P1 (重要, 违反 = CONCERNS)

- Function ≤ 50 行 (P0 是 40, P1 是 50)
- 有意义的命名 (不用 `x`, `temp`, `data`, `data2`)
- 错误消息对用户友好 (不要 raw stack trace 暴露给 end user)
- 测试覆盖关键路径 (每个 Feature ≥ 1 个测试, 边界条件覆盖)
- 错误处理统一 (不要一会 throw 一会 return null)

## P2 (建议)

- 复杂逻辑有 docstring / JSDoc
- 公共 API 有完整签名 + 用法示例
- 避免深层嵌套 (≤ 3 层)
- 提取常量 (无 magic number, 无 magic string)

## 例外处理

- 测试代码可放宽 SRP (一个测试函数可包含 setup + act + assert)
- mock / stub / fixture 可重复 (不强制 DRY)
- 第三方库的适配层可超过 40 行 (复杂适配需要)
- 若违反 P0 是有意为之, **必须在 PR description 写明理由**, 才能跳过 REWORK 判定
</important>
