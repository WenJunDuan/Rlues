---
description: VibeCoding自定义指令定义，使用vibe-前缀避免与官方指令冲突
---

# VibeCoding Commands (vibe-前缀)

## 设计原则

1. **前缀隔离**: 所有自定义指令使用 `vibe-` 前缀，避免与官方Claude指令冲突
2. **分离架构**: 指令只负责调度，具体执行由角色(Agent)和技能(Skill)完成
3. **参数化**: 支持 `--engine=xxx` 指定执行引擎

---

## 🚀 核心指令

| 指令 | 简写 | 描述 |
|:---|:---|:---|
| `/vibe-plan` | `/vp` | 深度规划模式 |
| `/vibe-design` | `/vd` | 架构设计模式 |
| `/vibe-code` | `/vc` | 编码执行模式 |
| `/vibe-review` | `/vr` | 代码审查模式 |
| `/vibe-debug` | `/vdb` | 问题调试模式 |

## 🔧 系统指令

| 指令 | 描述 |
|:---|:---|
| `/vibe-init` | 初始化项目，创建 `project_document/.ai_state/` |
| `/vibe-state` | 查看/同步当前状态 |
| `/vibe-clean` | 清除上下文，重新加载 |
| `/vibe-help` | 显示帮助信息 |

---

## 🛡️ 参数说明

### --engine 参数
指定执行引擎（用户指定优先于配置）：

```bash
/vibe-code --engine=codex "实现登录功能"
/vibe-code --engine=gemini "优化性能"
```

### --strict 参数
启用严格模式：

```bash
/vibe-review --strict  # 攻击性代码审查
```

### --tdd 参数
启用TDD模式：

```bash
/vibe-code --tdd "实现用户注册"
```

### --path 参数
强制指定P.A.C.E.路径：

```bash
/vibe-code --path=C "重构认证系统"  # 强制使用Path C逐步思考
```

---

## 🔗 与官方指令共存

VibeCoding指令与官方Claude Code指令完全兼容：

```bash
# 官方指令（保持不变）
/init
/compact
/clear
/help

# VibeCoding指令（vibe-前缀）
/vibe-plan
/vibe-code
/vibe-review
```

---

## 📝 官方 Plugins 放置位置

官方 plugins 从 GitHub 复制到此目录：

```bash
# 从 https://github.com/anthropics/claude-code 复制
cp claude-code/.claude/commands/code-review.md .claude/commands/
```

详见: `.claude/docs/plugins-guide.md`
