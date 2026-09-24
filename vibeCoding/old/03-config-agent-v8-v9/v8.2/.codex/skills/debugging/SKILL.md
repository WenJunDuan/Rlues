---
name: debugging
description: "Systematic four-phase debugging: reproduce, locate, fix, verify with chrome-devtools"
---

# 系统化调试

## 工具

| 工具 | 类型 | 用法 | 调用方式 |
|:---|:---|:---|:---|
| SP debugging | Superpowers | 四阶段调试方法论 | 读取 ~/.codex/superpowers/skills/debugging/SKILL.md |
| sou | MCP | 搜索相关代码+错误模式 | `sou.search("错误关键词")` |
| chrome-devtools | MCP | 前端运行时调试 | Codex 专属 |
| skill/tdd | VibeCoding Skill | 修复阶段写测试 | 内部加载 |

## 触发条件

- `vibe-debug` 命令直接触发
- skill/verification 2 次失败自动加载
- 用户报告 bug

## 四阶段

```
1. 复现
   → 确认 bug 可稳定复现
   → 记录 expected vs actual
   → 前端: chrome-devtools 抓错误 (Codex 专属优势)

2. 定位
   → sou.search("错误关键词") 搜索相关代码
   → SP debugging: 二分法缩小范围
     降级: SP 未安装 → 直接二分法
   → chrome-devtools: 检查 DOM/Network/Console

3. 修复
   → skill/tdd: 写修复测试 (RED) → 最小修复 (GREEN)

4. 验证
   → 运行全测试套件
   → chrome-devtools 验证前端修复
   → 记录 root cause → .knowledge/experience/mistakes.md
```

## 禁止

随机改代码、不复现就修、同时改多处、不写测试就提交。
