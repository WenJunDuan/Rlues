---
name: verification
---

# 验证循环

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| SP verification-before-completion | Superpowers | 完成前检查 | 读取 ~/.codex/superpowers/skills/verification-before-completion/SKILL.md |
| cunzhi MCP | MCP | 验证失败时寸止 | `cunzhi.confirm(VERIFY_FAIL)` |
| chrome-devtools | MCP | 前端运行时验证 | Codex 专属 |
| skill/debugging | VibeCoding Skill | 2 次失败后加载 | 按需 |

## 流程

```
1. → SP verification-before-completion
   降级: SP 未安装 → 直接执行清单
2. 前端项目: chrome-devtools 验证运行时行为
3. 通过? → done.md (verified: true)
4. 失败?
   → 修复 → 重试 (max 3)
   → 第 2 次: 加载 skill/debugging
   → 第 3 次: cunzhi [VERIFY_FAIL] 请求人工
```

## 验证清单 (按 Path 分级)

### Path A — 基础验证

```
□ 所有测试通过
□ Lint 通过
□ 无 console.log / debugger 残留
```

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

### Path C — 严格验证

```
□ Path B 全部清单
□ 覆盖率 ≥80%
□ 无未使用 import
□ 组件 <200 行, 单文件 <500 行
□ 手动安全检查 (无硬编码密钥/未验证输入)
```
