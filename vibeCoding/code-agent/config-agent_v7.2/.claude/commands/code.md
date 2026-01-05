---
description: 编码执行模式
triggers: ["/code", "编码", "开发"]
loads: ["ld", "codex/"]
---

# /code - 编码执行模式

> **Execution**: 只做 active_context.md 里分配给你的任务。

## 工作流

```
读取任务 → 执行代码 → 验证 → [PRE_COMMIT] → 用户确认
```

## 执行步骤

### 1. 状态同步
```
读取 .ai_state/active_context.md
确认当前任务: T-XXX
```

### 2. 执行代码
```bash
# 通过 codex skill 执行
codex - <<'EOF'
任务: T-XXX
参考: @.ai_state/active_context.md
要求:
1. 实现功能
2. 保持KISS原则
3. 完整错误处理
EOF
```

### 3. 执行前自检
- [ ] 逻辑清晰？（Taste）
- [ ] 输入验证？（Security）
- [ ] 无any，类型完整？
- [ ] 函数<50行？
- [ ] 错误处理完整？

### 4. 验证回路
```
Execute → Verify → Pass?
              ↓ No
         Analyze → Fix → Retry (max 3)
```

### 5. 寸止点（大规模修改时）
```
输出 [PRE_COMMIT]
等待用户确认
```

## 参数

- `/code` - 标准执行
- `/code --tdd` - TDD模式（先测试后实现）
- `/code --parallel` - 并行执行多任务

## TDD模式

```markdown
1. 先写测试（红）
2. 写最小实现（绿）
3. 重构（蓝）
```

## 自我修复循环

```
Execute → Fail? → Analyze → Fix → Retry (max 3)
                                    ↓
                           寸止: 请求人工介入
```

## 任务完成

更新 `.ai_state/active_context.md`:

```markdown
- [x] T-001: 任务描述 ✅
  - **验证**: [测试通过/截图]
  - **变更**: [文件列表]
```

## 行为准则

- 遇到不确定的依赖，先用 `sou` 确认，**禁止幻觉**
- 修改代码后，**必须验证修改是否生效**
- 不在任务清单里的工作，**不要做**
