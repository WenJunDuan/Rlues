# Path A: 快速修复

## 适用条件
- 单文件修改
- 代码量 < 30行
- 无架构变更
- 简单 bug 修复

## 简化九步
```
需求创建 → 开发实施 → 代码提交 → 完成归档
   1           6           7           9
```

## 流程详解

### 1. 需求创建 (简化)
```yaml
Agent: requirement-mgr
Skills:
  - knowledge-base (检索代码规范)
  - experience (检索相关经验)
  - riper/research (快速分析)

动作:
  - 快速理解需求
  - 识别目标文件
  - 简要记录到 active_context.md

注意: 不生成完整需求文档，直接进入开发
```

### 6. 开发实施
```yaml
Agent: impl-executor
Skills:
  - riper/plan (生成简要 TODO)
  - riper/execute (执行修改)
  - code-quality (质量检查)

动作:
  - 读取目标文件
  - 执行修改
  - 本地验证

无需寸止 - 计划简单，直接执行
```

### 7. 代码提交
```yaml
Agent: impl-executor
Skills:
  - riper/review (快速验证)
  - code-quality (规范检查)

动作:
  - 验证修改结果
  - 检查无副作用
  - 提交代码
```

### 9. 完成归档
```yaml
Agent: experience-mgr
Skills:
  - experience (可选沉淀)
  - cunzhi (寸止)

寸止: [TASK_DONE]

输出:
  - 完成摘要
  - 验证结果
  
等待: 用户确认
```

## 时间预估
- 总耗时: 5-15分钟
- 寸止点: 1个 ([TASK_DONE])

## 知识库/经验检索
```yaml
自动检索:
  - knowledge-base: 代码规范
  - experience: 类似修复经验

示例:
  "检索到相关经验: EXP-023 类似 bug 的修复方法"
```

## 示例
```
用户: "修复登录按钮点击无反应"

执行:
  1. 快速分析 → 目标: src/components/LoginButton.tsx
  2. 检索经验 → 发现类似问题处理经验
  3. 读取文件 → 理解现有代码
  4. 执行修复 → 添加事件处理
  5. 验证 → 功能正常
  6. [TASK_DONE] → 等待确认
```
