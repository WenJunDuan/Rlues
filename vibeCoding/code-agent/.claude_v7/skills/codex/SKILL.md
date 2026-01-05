---
name: codex
description: 代码执行主力，所有代码变更通过此技能
mcp_tool: codex
---

# Codex Skill

代码执行的主要方法。Claude负责规划验证，Codex负责实际执行。

## 使用场景

- 任何代码编写、修改、删除
- 测试编写和执行
- 大规模重构
- 文件操作

## 调用方式

### 基本调用
```bash
codex "任务描述" [工作目录]
codex "重构 @src/auth.ts 添加JWT验证"
```

### HEREDOC语法（推荐复杂任务）
```bash
codex - <<'EOF'
实现用户认证模块：
1. 创建登录API端点
2. 添加JWT token生成
3. 实现密码哈希
4. 编写单元测试（仅用户要求时）
EOF
```

### 并行执行
```bash
codex --parallel <<'EOF'
---TASK---
id: backend_api
workdir: /project/backend
---CONTENT---
实现 /api/users 端点

---TASK---
id: frontend_ui
workdir: /project/frontend
dependencies: backend_api
---CONTENT---
创建Users页面
EOF
```

## 并行任务格式

| 字段 | 说明 |
|------|------|
| `---TASK---` | 任务块开始 |
| `id` | 唯一任务标识 |
| `workdir` | 工作目录（可选） |
| `dependencies` | 依赖任务ID（可选） |
| `---CONTENT---` | 任务内容开始 |

## 会话管理

```bash
# 首次任务
codex "添加表单验证"
# 输出: SESSION_ID: 019a7247...

# 恢复会话继续
codex resume 019a7247... - <<'EOF'
为每个验证规则添加错误消息
EOF
```

## 自我修复循环

```
Execute → Fail? → Analyze → Fix → Retry (max 3)
                                    ↓
                           寸止: 请求人工介入
```

## 降级策略

1. Codex是首选执行方法
2. 失败时重试一次
3. 连续两次失败 → 记录CODEX_FALLBACK → Claude直接执行
4. 下一任务重新尝试Codex

## 代码质量标准

- TypeScript 无 `any`
- 函数 <50行
- 组件 <200行
- 完整错误处理
- 输入验证

## 注意

**默认静默执行**：除非用户明确要求，不自动运行测试/编译
