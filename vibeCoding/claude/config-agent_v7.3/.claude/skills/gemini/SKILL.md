---
name: gemini
description: Gemini AI执行引擎，备选技能（未来扩展）
type: execution-engine
status: planned
---

# Gemini Skill (未来扩展)

Gemini AI执行引擎，作为**备选技能**。

## 定位

Gemini是LD角色可调用的**备选技能**，与Codex形成互补：
- 特定场景优化
- 长上下文处理
- 多模态任务

## 调用方式（规划中）

### 通过指令指定
```bash
/vibe-code --skill=gemini "优化性能"
```

### 直接调用
```bash
gemini "任务描述"
```

## 规划能力

### 代码任务
- 代码优化
- 性能分析
- 长文件处理

### 多模态任务
- 图片理解
- 文档分析
- 视觉相关代码

## 与Codex对比

| 维度 | Codex | Gemini |
|:---|:---|:---|
| 状态 | 可用 | 规划中 |
| 特长 | 代码执行 | 长上下文 |
| 适用 | 通用任务 | 特定优化 |

## 集成计划

```markdown
Phase 1: 接口定义
Phase 2: 基础集成
Phase 3: 场景优化
Phase 4: 自动选择
```

## 使用建议

当前版本请使用 Codex 或 Claude原生执行。

Gemini技能将在未来版本中提供。
