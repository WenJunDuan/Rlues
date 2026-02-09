---
name: verification
---

# 验证循环

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| Superpowers verification-before-completion | Plugin Skill | 完成前结构化检查 | 自动: V 阶段触发 |
| cunzhi MCP | MCP | 验证失败时寸止 | `cunzhi.confirm(VERIFY_FAIL)` |
| skill/debugging | VibeCoding Skill | 2 次失败后加载 | 按需 |

## 流程

```
1. → Superpowers verification-before-completion
2. 执行验证清单 (按 Path 选择)
3. 通过? → done.md (verified: true)
4. 失败?
   → 分析原因 → 修复 → 重试 (max 3)
   → 第 2 次失败: 加载 skill/debugging
   → 第 3 次失败: cunzhi [VERIFY_FAIL] 请求人工
```

## 验证清单 (按 Path 分级)

### Path A — 基础验证

```
□ 所有测试通过
□ Lint 通过
□ 无 console.log / debugger 残留
```

不检查 plan.md (Path A 无 P 阶段)。

### Path B — 标准验证

```
□ 所有测试通过
□ TypeScript 类型检查 (tsc --noEmit)
□ Lint 通过
□ plan.md 目标逐项覆盖
□ 验收标准逐项满足
□ 无 console.log / debugger 残留
□ 无注释掉的代码块
```

### Path C/D — 严格验证

```
□ Path B 全部清单
□ 覆盖率达标 (C: 80%, D: 85%)
□ 无未使用 import
□ 组件 <200 行
□ 单文件 <500 行
□ 安全检查通过 (无硬编码密钥/未验证输入)
```

## .ai_state

- 通过 → done.md 标记 `verified: true`
- 失败 → todo.md 追加修复子任务

## 降级

Superpowers 未安装 → 直接执行上述清单 (AI 自主检查)。
