# 指令索引

## 概述
VibeCoding 提供一系列 `/vibe-*` 指令，用于控制开发流程。

## 指令清单

### 工作流指令
| 指令 | 说明 | 参数 |
|:---|:---|:---|
| `/vibe-init` | 初始化项目 | [项目名] |
| `/vibe-code <desc>` | 执行编码 | 任务描述 |
| `/vibe-plan <desc>` | 仅生成计划 | 任务描述 |
| `/vibe-design <desc>` | 架构设计 | 设计描述 |

### 控制指令
| 指令 | 说明 |
|:---|:---|
| `/vibe-status` | 查看当前状态 |
| `/vibe-pause` | 暂停工作流 |
| `/vibe-resume` | 恢复工作流 |
| `/vibe-abort` | 中止工作流 |

## 指令详情

### /vibe-init
```yaml
用途: 初始化 .ai_state/ 目录
流程:
  1. 创建 .ai_state/ 目录
  2. 初始化状态文件
  3. 连接 Memory MCP
```

### /vibe-code
```yaml
用途: 执行完整编码流程
流程:
  1. 评估复杂度
  2. 选择路径 (A/B/C)
  3. 执行 RIPER 流程
参数:
  desc: 任务描述 (必需)
  --path: 强制指定路径 (可选)
```

### /vibe-plan
```yaml
用途: 仅生成计划不执行
流程:
  1. Research 分析
  2. Innovate 设计 (若需要)
  3. Plan 生成 TODO
  4. 寸止等待
输出: TODO.md + kanban.md
```

### /vibe-design
```yaml
用途: 架构设计
流程:
  1. Research 深度分析
  2. Innovate 架构设计
  3. 输出设计文档
输出: architecture.md
```

## 参数说明

### 路径参数 --path
```bash
/vibe-code --path=A "修复 bug"    # 强制快速路径
/vibe-code --path=B "添加功能"   # 强制计划路径
/vibe-code --path=C "重构模块"   # 强制系统路径
```

### 静默参数 --quiet
```bash
/vibe-code --quiet "任务"    # 减少输出
```

## 使用示例

### 快速修复
```bash
/vibe-code "修复登录按钮样式"
# 自动判断为 Path A，快速执行
```

### 功能开发
```bash
/vibe-code "添加用户个人资料页面"
# 自动判断为 Path B，需要计划
```

### 系统重构
```bash
/vibe-code "重构认证模块，支持 OAuth"
# 自动判断为 Path C，分阶段执行
```

### 仅规划
```bash
/vibe-plan "实现搜索功能"
# 只生成计划，不执行
```

### 仅设计
```bash
/vibe-design "设计插件系统架构"
# 只做设计，不执行
```
