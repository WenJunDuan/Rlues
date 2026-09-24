---
name: vibe-code
aliases: ["/vc"]
description: 编码执行模式，支持多技能选择
loads:
  agents: ["ld"]
  skills: ["选定skill"]
  plugins: ["commit-commands"]
---

# /vibe-code - 编码执行模式

> **Execution**: 只做 active_context.md 里分配给你的任务。

## 触发方式

```bash
/vibe-code                          # 自动选择技能
/vibe-code --skill=codex            # 指定Codex执行
/vibe-code --skill=gemini           # 指定Gemini执行（未来）
/vibe-code --tdd                    # TDD模式
/vibe-code --path=C                 # 强制Path C逐步思考
/vc                                 # 简写
```

## 技能选择

### Codex (默认)
```bash
/vibe-code --skill=codex "实现用户登录"
```
- AI代码执行引擎
- 支持并行任务
- 自我修复循环

### Gemini (未来扩展)
```bash
/vibe-code --skill=gemini "优化性能"
```
- 备选AI引擎
- 特定场景优化

### Claude原生
```bash
/vibe-code "简单修复"  # 无--skill参数时
```
- 直接由Claude执行
- 适合简单任务

## 工作流

```
读取任务 → 选择技能 → 执行 → 验证 → [PRE_COMMIT](大规模时)
```

## 执行步骤

### 1. 状态同步
```
读取 project_document/.ai_state/active_context.md
确认当前任务: T-XXX
```

### 2. 技能调用

#### 使用Codex
```bash
codex - <<'EOF'
任务: T-XXX
参考: @project_document/.ai_state/active_context.md
范围: @src/auth/
要求:
1. 实现功能
2. KISS原则
3. 完整错误处理
EOF
```

#### 使用Claude原生
```
直接执行代码修改
使用标准编辑工具
```

### 3. 执行前自检
- [ ] 逻辑清晰？（Taste）
- [ ] 输入验证？（Security）
- [ ] 无any，类型完整？
- [ ] 函数<50行？
- [ ] 错误处理完整？

### 4. 验证回路
```
Execute → Verify → Pass? → Done
              ↓ No
         Analyze → Fix → Retry (max 3)
                          ↓ Fail
                    寸止: 人工介入
```

### 5. 寸止点（大规模修改时）
```
输出 [PRE_COMMIT]
等待用户确认
```

## TDD模式

```bash
/vibe-code --tdd "实现用户注册"
```

流程:
```
1. 先写测试（红）
2. 写最小实现（绿）
3. 重构（蓝）
```

## Path C 逐步思考

```bash
/vibe-code --path=C "重构认证系统"
```

强制启用逐步思考:
```
1. 分解为小问题
2. 一步一步执行
3. 每步验证
4. 阶段性寸止确认
```

## 任务完成

更新 `project_document/.ai_state/active_context.md`:

```markdown
- [x] T-001: 任务描述 ✅
  - **验证**: [测试通过证据]
  - **变更**: [文件列表]
```

## 与commit-commands插件集成

加载官方 `commit-commands` 插件，支持:
- 智能commit message生成
- Git操作辅助
