---
description: Slash指令系统定义，解耦"意图"与"执行角色"
---

# Slash Commands Definitions

## 🚀 流程指令

| 指令 | 描述 | 加载角色/技能 |
|:---|:---|:---|
| `/plan` | 进入深度规划模式，生成WBS和风险评估 | `pdm` + `pm` + `meeting/` |
| `/design` | 进入架构与交互设计模式 | `ar` + `ui` + `thinking/` |
| `/code` | 进入编码执行模式 | `ld` + `codex/` |
| `/review` | 进入代码审查模式 | `qe` + `verification/` |
| `/state` | 强制同步状态 | 读取 `.ai_state/active_context.md` |
| `/debug` | 进入问题诊断模式 | `ld` + `thinking/` |

---

## 🛡️ 参数化指令

### `/review --strict`
- **行为**: 加载 `qe`，启用攻击性测试思维
- **附加**: "忽略礼貌，严厉指出逻辑漏洞、边界条件、并发问题"

### `/code --tdd`
- **行为**: 加载 `ld`，严格TDD流程
- **附加**: "先写测试，再写实现。测试先行，代码跟随"

### `/fix --auto`
- **行为**: 自动读取最近Error Log
- **流程**: 尝试最多3次自我修复循环
- **失败**: 寸止请求人工介入

### `/plan --quick`
- **行为**: 快速规划模式
- **附加**: "跳过风险评估，直接生成任务清单"

---

## 🔧 系统维护

| 指令 | 描述 |
|:---|:---|
| `/clean` | 清除当前上下文记忆，重新加载Bootloader |
| `/help` | 列出当前可用指令 |
| `/init` | 初始化项目，创建 `.ai_state/` 目录 |
| `/sync` | 强制同步 `.ai_state/active_context.md` |

---

## 📝 快捷指令

| 指令 | 描述 |
|:---|:---|
| `/commit` | 计算git状态，生成commit message |
| `/pr` | 生成PR描述 |
| `/test` | 运行测试并分析结果 |

---

## 🎯 指令执行规范

### 指令解析流程
```
1. 解析指令和参数
2. 加载对应角色/技能
3. 执行角色定义的工作流
4. 在寸止点等待用户确认
```

### 指令链式调用
```
/plan -> [PLAN_READY] -> 用户确认 -> /code -> [PRE_COMMIT] -> 用户确认
```

### 指令冲突处理
- 新指令覆盖当前角色
- 切换前自动保存状态到 `.ai_state/`

---

## 🔗 自定义指令

用户可在 `.claude/commands/` 下定义自定义指令：

```markdown
---
description: 自定义指令描述
---

# /my-command

## 行为
[定义行为]

## 加载
[定义要加载的角色/技能]
```
