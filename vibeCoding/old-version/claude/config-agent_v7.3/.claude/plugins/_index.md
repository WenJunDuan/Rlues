---
name: plugins-index
description: 官方Claude Code Plugins引用索引
source: https://github.com/anthropics/claude-code/tree/main/plugins
---

# Official Plugins Index

集成的官方Claude Code插件列表。

## 插件列表

| 插件 | 用途 | 加载时机 |
|:---|:---|:---|
| `code-review` | 代码审查 | /vibe-review |
| `commit-commands` | Git提交命令 | /vibe-code |
| `feature-dev` | 功能开发 | /vibe-plan |
| `frontend-design` | 前端设计 | /vibe-design |
| `learning-output-style` | 学习输出风格 | 全局 |
| `hookify` | 钩子系统 | 全局 |
| `pr-review-toolkit` | PR审查工具 | /vibe-review --pr |
| `security-guidance` | 安全指导 | /vibe-review, SA角色 |
| `ralph-wiggum` | 创意模式 | 按需 |

---

## 插件详情

### code-review
**来源**: [anthropics/claude-code/plugins/code-review](https://github.com/anthropics/claude-code/blob/main/plugins/code-review)

**用途**: 增强代码审查能力

**加载**:
- `/vibe-review` 自动加载
- QE角色自动加载

---

### commit-commands
**来源**: [anthropics/claude-code/plugins/commit-commands](https://github.com/anthropics/claude-code/blob/main/plugins/commit-commands)

**用途**: Git提交命令增强

**加载**:
- `/vibe-code` 自动加载
- LD角色自动加载

---

### feature-dev
**来源**: [anthropics/claude-code/plugins/feature-dev](https://github.com/anthropics/claude-code/blob/main/plugins/feature-dev)

**用途**: 功能开发流程

**加载**:
- `/vibe-plan` 自动加载

---

### frontend-design
**来源**: [anthropics/claude-code/plugins/frontend-design](https://github.com/anthropics/claude-code/blob/main/plugins/frontend-design)

**用途**: 前端设计能力增强

**加载**:
- `/vibe-design --ui` 自动加载
- UI角色自动加载

---

### learning-output-style
**来源**: [anthropics/claude-code/plugins/learning-output-style](https://github.com/anthropics/claude-code/blob/main/plugins/learning-output-style)

**用途**: 学习优化输出风格

**加载**: 全局可用

---

### hookify
**来源**: [anthropics/claude-code/plugins/hookify](https://github.com/anthropics/claude-code/blob/main/plugins/hookify)

**用途**: 钩子系统增强

**加载**: 全局可用

---

### pr-review-toolkit
**来源**: [anthropics/claude-code/plugins/pr-review-toolkit](https://github.com/anthropics/claude-code/blob/main/plugins/pr-review-toolkit)

**用途**: PR审查工具集

**加载**:
- `/vibe-review --pr` 自动加载

---

### security-guidance
**来源**: [anthropics/claude-code/plugins/security-guidance](https://github.com/anthropics/claude-code/blob/main/plugins/security-guidance)

**用途**: 安全检查指导

**加载**:
- `/vibe-review --security` 自动加载
- SA角色自动加载

---

### ralph-wiggum
**来源**: [anthropics/claude-code/plugins/ralph-wiggum](https://github.com/anthropics/claude-code/blob/main/plugins/ralph-wiggum)

**用途**: 创意/幽默模式

**加载**: 按需手动加载

---

## 使用方式

插件在相应指令/角色加载时自动激活，无需手动配置。

如需手动加载:
```
加载 plugins/code-review
```
