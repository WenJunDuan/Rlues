---
effort: medium
attach_to_stages: [review, polish]
attach_to_subagents: [reviewer, polish_worker]
---

<important if="writing docs, comments, or running polish">
# Doc Style · 文档与注释规范

> 适用于代码注释 / API 文档 / README / 设计文档.
> polish stage 强制注入本规则.

## 何时写注释

### 必须写 (P0, 违反 = REWORK)
- 公开 API (export 的 function / class / const) → docstring / JSDoc
- 复杂业务逻辑 (≥ 30 行的 function, 含分支判断 ≥ 5 个)
- 非显然的算法选择 ("这里用 quickselect 而不是 sort, 因为 ..." )
- 兼容老接口的 hack ("workaround for issue #1234, 可在 v2 删除")
- 性能关键路径 ("这里 cache 因为下游频繁调用")

### 应该写 (P1)
- 函数有副作用 (修改全局状态 / 写文件 / 网络请求)
- 错误处理逻辑非显然 (为什么 retry, 为什么吞掉异常)
- 类型断言 (`as Foo` / `cast(Foo, x)`) 必须说明为什么安全

### 不要写 (违反 P2)
- 重复代码本身 (`i++ // 增加 i`) → 删
- 历史变更说明 → 用 git log, 不在注释里
- TODO 不带 issue 号 → 必须 `// TODO(issue-123): ...` 或删
- 注释掉的代码 → 删 (git history 找得到)

## 注释格式

### Python
```python
def foo(x: int) -> str:
    """One-line summary.

    Longer explanation if needed.

    Args:
        x: Description of x.

    Returns:
        Description of return value.

    Raises:
        ValueError: When x is negative.
    """
```

### TypeScript / JavaScript
```typescript
/**
 * One-line summary.
 *
 * @param x - Description of x.
 * @returns Description of return value.
 * @throws {ValueError} When x is negative.
 */
export function foo(x: number): string { ... }
```

### Inline 注释
- 用 `//` 或 `#`, 不用 `/* */`
- 注释**在被解释行的上面**, 不是行尾
- 行尾注释只能用于简短旁注 (≤ 20 字符)

## README 规范

### 最小集 (任何项目)
- 项目名 + 一句话描述
- Quick start (复制粘贴可运行的命令)
- 主要 commands / scripts

### 标准集 (生产项目)
- 上述 + 架构图 (mermaid 或 SVG)
- 配置项说明 (环境变量 / config 文件)
- 部署步骤
- 测试运行方式
- License + 贡献指南链接

## 设计文档 (`.ai_state/sprints/{current_sprint_slug}/design.md`)

每个 Feature / Refactor / System 路径必须有 design.md:
- **背景**: 为什么做这个改动 (问题 / 需求 / 痛点)
- **方案**: 选定的实现路径 (含 ≥ 1 个备选方案的对比)
- **影响范围**: 改动哪些文件 / 模块 / 数据库
- **风险与缓解**: 已知风险 + mitigation
- **验收标准**: 怎么验证完成 (测试 / 手动验证步骤)

## 量化 AC 记法 (2026-07-28)

计数类验收标准 (行数 / 测试数 / 文件数 / 覆盖率) 的写法按写者数分两种:

- **并行多写者 → 必须写绝对相等 + 构成式**, 禁用 `≥`。
  形如 `测试总数 = 1966 (基线) + 12 (片A) + 8 (片B) = 1986`。
  理由: `≥1966` 允许「一片删测试、另一片加测试」互相抵消, 合并后仍满足门槛却掩盖了净损失 (实测踩过)。
- **单写者可用下界** (`≥N`), 但基线值 `N` 必须附**测量命令与出处**, 不得凭印象。

两种写法都受 coding-standards「量化验收标准必先核基线」约束: design 阶段先测被改对象的当前值,
基线已越线的对象要么纳入本批修复、要么显式记豁免。基线条目本身写进 route-note 的
**「已验证基线」节** (含单条可复跑的测量命令), 派工时随契约下传; 无测量命令的基线视同未验证。

## polish stage 特殊检查

polish_worker 加载本规则后, 重点扫描:
1. 公开 API 是否缺 docstring (P0)
2. 复杂业务逻辑是否缺解释性注释 (P1)
3. TODO / FIXME 是否带 issue 号 (P1)
4. 注释掉的代码是否还在 (P2, 清除)
5. 行尾注释是否过长 (P2, 移到上面)

## 例外

- 测试代码可放宽注释要求 (但测试名称必须清晰说明在测什么)
- 第三方代码 / vendor 不要求注释
- 自动生成的代码 (codegen / protobuf 等) 跳过本规则

## Agent 输出纪律 (v9.9.1)

- 结果优先; 结构只服务于理解, 不强制表格或极端压缩
- 引用文件给路径和必要行号, 避免重复粘贴整段原文
- 使用自然完整句; 对复杂权衡给足可核验证据, 不暴露私有思维链
- delivery-gate block reason 必须包含阻塞事实、失败证据与可执行解锁动作
</important>
