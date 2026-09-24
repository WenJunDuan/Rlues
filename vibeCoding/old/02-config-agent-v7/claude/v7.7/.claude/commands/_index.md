# 指令索引 (v7.7)

## 概述
VibeCoding v7.7 提供一系列 `/vibe-*` 指令，用于控制开发流程。

## 核心指令

| 指令 | 说明 | 参数 |
|:---|:---|:---|
| `/vibe-dev <desc>` | 需求研发入口 | 任务描述 |
| `/vibe-service <n>` | 加载服务上下文 | 服务名 |
| `/vibe-exp <action>` | 经验操作 | search/deposit/show |
| `/vibe-kb <action>` | 知识库操作 | load/search/list |

## 控制指令

| 指令 | 说明 |
|:---|:---|
| `/vibe-status` | 查看当前状态 |
| `/vibe-pause` | 暂停工作流 |
| `/vibe-resume` | 恢复工作流 |
| `/vibe-abort` | 中止工作流 |

## 兼容指令 (v7.6)

| 指令 | 说明 | 映射 |
|:---|:---|:---|
| `/vibe-init` | 初始化项目 | → /vibe-dev --init |
| `/vibe-code` | 执行编码 | → /vibe-dev |
| `/vibe-plan` | 仅生成计划 | → /vibe-dev --plan-only |
| `/vibe-design` | 架构设计 | → /vibe-dev --design-only |

## 指令详情

### /vibe-dev
主入口指令，通过 phase-router 智能路由到相应流程。

```bash
# 新建需求
/vibe-dev "添加用户登录功能"

# 继续任务
/vibe-dev REQ-001

# 指定动作
/vibe-dev REQ-001 --design
/vibe-dev REQ-001 --develop

# 指定路径
/vibe-dev --path=A "修复 bug"
/vibe-dev --path=C "重构系统"

# 仅规划
/vibe-dev --plan-only "新功能"

# 仅设计
/vibe-dev --design-only "架构设计"
```

### /vibe-service
加载服务上下文到当前会话。

```bash
# 加载单个服务
/vibe-service user-service

# 加载多个服务
/vibe-service user-service auth-service

# 分析服务
/vibe-service analyze user-service
```

### /vibe-exp
经验库操作。

```bash
# 搜索经验
/vibe-exp search "缓存策略"

# 沉淀经验
/vibe-exp deposit

# 查看经验
/vibe-exp show EXP-001

# 列出经验
/vibe-exp list
```

### /vibe-kb
知识库操作。

```bash
# 加载知识
/vibe-kb load standards/code-style.md

# 搜索知识
/vibe-kb search "认证规范"

# 列出知识
/vibe-kb list
```

## 使用示例

### 典型开发流程
```bash
# 1. 开始新需求
/vibe-dev "实现用户搜索功能"

# 2. 用户确认需求后，继续设计
(自动进入方案设计)

# 3. 用户确认设计后，继续开发
(自动进入开发实施)

# 4. 开发完成，确认归档
(自动沉淀经验)
```

### 继续已有任务
```bash
# 查看状态
/vibe-status

# 继续任务
/vibe-dev REQ-001

# 或指定动作
/vibe-dev REQ-001 --develop
```

### 使用知识库和经验
```bash
# 开发前搜索经验
/vibe-exp search "类似功能"

# 加载相关知识
/vibe-kb load project/architecture.md
```
