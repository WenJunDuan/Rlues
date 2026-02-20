---
name: code-quality
description: 代码质量审查 — Plugin 编排
context: main
---
Rev 阶段按顺序:
1. 运行 `/review` 官方审查
2. validator 子代理: 测试+lint+类型
3. security-auditor 子代理: 安全扫描 (Path C+)
4. 四问检查: 这代码必要吗? 逻辑最简吗? 边界覆盖吗? 可读可维护吗?
