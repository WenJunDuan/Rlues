# VibeCoding 指令索引

> 所有指令使用 `vibe-` 前缀，避免与官方命令冲突

---

## 工作流指令

| 指令 | 作用 | 加载文件 |
|:---|:---|:---|
| `/vibe-init` | 初始化项目 | 创建 .ai_state/ |
| `/vibe-plan` | 深度规划 | skills/plan.md |
| `/vibe-design` | 架构设计 | skills/innovate.md |
| `/vibe-code` | 执行编码 | skills/execute.md |
| `/vibe-review` | 代码审查 | skills/review.md |

---

## 控制指令

| 指令 | 作用 | 说明 |
|:---|:---|:---|
| `/vibe-status` | 查看状态 | 读取 .ai_state/ |
| `/vibe-pause` | 暂停工作流 | 保存状态，更新 session.lock |
| `/vibe-resume` | 恢复工作流 | 从 session.lock 恢复 |
| `/vibe-abort` | 中止工作流 | 删除 session.lock |

---

## 参数

```bash
# 引擎选择
--engine=claude    # 使用 Claude（默认）
--engine=codex     # 使用 Codex
--engine=gemini    # 使用 Gemini

# 路径强制
--path=A          # 强制 Path A
--path=B          # 强制 Path B
--path=C          # 强制 Path C

# 模式
--strict          # 严格模式
--tdd             # TDD 模式
```

---

## 使用示例

```bash
# 初始化新项目
/vibe-init

# 规划任务
/vibe-plan 实现用户认证功能

# 执行编码（自动评估路径）
/vibe-code 添加登录接口

# 强制使用 Codex 执行
/vibe-code --engine=codex 修复登录Bug

# 查看当前状态
/vibe-status

# 暂停当前工作流
/vibe-pause

# 恢复工作流
/vibe-resume
```
