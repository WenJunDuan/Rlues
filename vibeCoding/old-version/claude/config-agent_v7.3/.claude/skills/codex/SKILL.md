---
name: codex
description: AI代码执行引擎，可选技能之一
type: execution-engine
mcp_tool: codex
---

# Codex Skill

AI代码执行引擎，作为**可选技能之一**（不是唯一执行方式）。

## 定位

Codex是LD角色可调用的**技能之一**，用于：
- 代码编写和修改
- 文件处理（包括PDF等）
- 并行任务执行
- 复杂代码重构

## 调用方式

### 通过指令指定
```bash
/vibe-code --skill=codex "实现用户登录"
```

### 在LD角色中调用
```bash
# 单任务
codex "任务描述 @文件路径"

# HEREDOC（复杂任务）
codex - <<'EOF'
任务: T-XXX
参考: @project_document/.ai_state/active_context.md
要求:
1. 实现功能
2. KISS原则
EOF

# 并行执行
codex --parallel <<'EOF'
---TASK---
id: api
---CONTENT---
实现后端接口

---TASK---
id: ui
dependencies: api
---CONTENT---
实现前端页面
EOF
```

## 能力范围

### 代码任务
- 编写新代码
- 修改现有代码
- 代码重构
- Bug修复

### 文件任务
- PDF处理（未来扩展）
- 文档生成
- 配置文件修改

## 验证回路

```
Execute → Verify → Pass? → Done
              ↓ No
         Analyze → Fix → Retry (max 3)
                          ↓ Fail
                    寸止: 人工介入
```

## 自检清单

执行前必须检查：
- [ ] 逻辑清晰？
- [ ] 输入验证？
- [ ] 无any？
- [ ] 函数<50行？
- [ ] 错误处理完整？

## 会话管理

```bash
# 首次任务
codex "添加表单验证"
# 输出: SESSION_ID: 019a7247...

# 恢复会话
codex resume 019a7247... - <<'EOF'
添加错误消息
EOF
```

## 降级策略

Codex不可用时：
1. 降级到Claude原生执行
2. 记录降级原因
3. 下次任务重试Codex

## 与其他技能对比

| 技能 | 特点 | 适用场景 |
|:---|:---|:---|
| **Codex** | AI执行引擎 | 复杂代码任务 |
| **Gemini** | 备选引擎 | 特定优化任务 |
| **Claude原生** | 直接执行 | 简单任务 |
