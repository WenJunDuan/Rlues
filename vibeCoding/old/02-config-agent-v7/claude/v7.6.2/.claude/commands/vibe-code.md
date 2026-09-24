# /vibe-code

## 用途
执行完整的编码开发流程

## 语法
```bash
/vibe-code <任务描述> [--path=A|B|C] [--quiet]
```

## 参数
| 参数 | 说明 | 默认值 |
|:---|:---|:---|
| 任务描述 | 要完成的任务 | 必需 |
| --path | 强制指定路径 | 自动判断 |
| --quiet | 减少输出 | false |

## 执行流程

### 1. 前置检查
```yaml
检查:
  - .ai_state/ 存在
  - session.lock 状态
  - 无进行中的任务
```

### 2. 复杂度评估
```yaml
评估因素:
  - 涉及文件数
  - 预计代码行数
  - 是否跨模块
  - 是否需要设计

输出: 推荐路径
```

### 3. 路径选择
```yaml
自动选择:
  Path A: 单文件 & <30行
  Path B: 2-10文件
  Path C: >10文件或跨模块

强制指定:
  --path=A/B/C
```

### 4. 执行 RIPER
```yaml
加载对应 workflow:
  - workflows/path-a.md
  - workflows/path-b.md
  - workflows/path-c.md

执行阶段:
  R → I → P → E → R2
```

### 5. 寸止点
```yaml
Path A: [TASK_DONE]
Path B: [PLAN_READY], [TASK_DONE]
Path C: [PLAN_READY], [DESIGN_FREEZE], [PHASE_DONE]×n, [TASK_DONE]
```

## 路由逻辑

### 可路由到其他指令
```yaml
若只需规划:
  内部调用 /vibe-plan 逻辑

若只需设计:
  内部调用 /vibe-design 逻辑
```

## 示例

### 自动判断路径
```bash
/vibe-code "修复按钮点击无反应"
# → 判断为 Path A，直接执行

/vibe-code "添加用户设置页面"
# → 判断为 Path B，先规划后执行

/vibe-code "重构整个认证系统"
# → 判断为 Path C，分阶段执行
```

### 强制路径
```bash
/vibe-code --path=B "修复 bug"
# 即使是简单 bug，也走完整规划流程
```

### 静默模式
```bash
/vibe-code --quiet "快速修复"
# 减少中间输出
```

## 输出示例

### 开始执行
```markdown
## 任务开始

### 描述
添加用户设置页面

### 路径选择
Path B (计划开发)
- 原因: 预计涉及 3-5 个文件

### 开始 Research 阶段...
```

### 寸止输出
```markdown
## [PLAN_READY] 计划生成完成

### 任务数
5 个

### 预计时间
1.5 小时

### 首要任务
1. [components/Settings.tsx] 创建设置组件

确认执行？
```

## 错误处理
```yaml
任务进行中:
  - 提示有未完成任务
  - 建议 /vibe-resume 或 /vibe-abort

初始化未完成:
  - 自动执行 /vibe-init
  - 然后继续
```
