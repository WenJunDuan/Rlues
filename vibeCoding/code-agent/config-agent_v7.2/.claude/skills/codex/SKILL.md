---
name: codex
description: 代码执行主力，Talk is cheap, show me the code
mcp_tool: codex
---

# Codex Skill

> **"Talk is cheap. Show me the code."** — Linus Torvalds

代码执行的主要方法。用代码说话，不用文字解释。

## 核心原则

- **静默执行**: 默认不测试/不编译/不运行，除非用户要求
- **简洁代码**: 函数<50行，无any，错误处理完整
- **自我修复**: 失败自动重试，3次后请求人工
- **验证闭环**: 修改后必须验证生效

## 调用方式

### 基本调用
```bash
codex "任务描述 @文件路径"
```

### HEREDOC（复杂任务）
```bash
codex - <<'EOF'
任务: T-XXX
参考: @.ai_state/active_context.md
范围: @src/auth/
要求:
1. 实现功能
2. KISS原则
3. 完整错误处理
EOF
```

### 并行执行
```bash
codex --parallel <<'EOF'
---TASK---
id: api
workdir: /project/backend
---CONTENT---
实现后端接口

---TASK---
id: ui
dependencies: api
workdir: /project/frontend
---CONTENT---
实现前端页面
EOF
```

## 执行前自检

- [ ] 逻辑清晰？（Taste）
- [ ] 输入验证？（Security）
- [ ] 无any，类型完整？
- [ ] 函数<50行？
- [ ] 错误处理完整？

## 验证回路

```
Execute → Verify → Pass? → Done
              ↓ No
         Analyze → Fix → Retry (max 3)
                          ↓ Fail
                    寸止: 人工介入
```

## 自我修复循环

```
1. 执行代码
2. 验证结果
3. 如果失败:
   - 分析原因
   - 修复问题
   - 重试(最多3次)
4. 3次后仍失败 → 寸止请求人工
```

## 降级策略

```
Codex失败 → 重试一次
再失败 → 记录CODEX_FALLBACK
       → Claude直接执行
       → 下一任务重试Codex
```

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

## 注意事项

- 遇到不确定的依赖，**先用sou搜索确认**
- 修改代码后，**必须验证修改是否生效**
- 不在任务清单里的工作，**不要做**
