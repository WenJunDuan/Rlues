---
name: systematic-debugging
description: 结构化调试 — Bug修复时自动激活
context: main
effort: high
---
## 触发: 需求含 bug/fix/error/crash/失败/报错

## 四阶段 (不允许跳过)

### 1. 复现
- 找到稳定触发步骤
- 写失败测试证明bug
- **不能复现 = 不能修复**

### 2. 根因追踪
- 从错误往上追调用链
- augment-context-engine 搜相关代码
- LSP diagnostics / ast-grep 辅助 (如可用)
- 确认根因, 不是表面症状

### 3. 防御性修复
- 修根因, 不绕症状
- 添加防御检查防同类
- 失败测试变绿

### 4. 验证
- 全量测试无回归
- ast-grep搜同类bug (如可用)
- lessons.md 记录

## 禁止
- 看到报错就改, 没复现
- 只修症状不查根因
- 改完不测
