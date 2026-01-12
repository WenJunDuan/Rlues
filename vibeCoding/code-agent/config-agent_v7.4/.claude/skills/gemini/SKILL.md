---
name: gemini
description: Gemini AI执行引擎，可选引擎之一
type: execution-engine
---

# Gemini Skill

Gemini AI执行引擎，作为**可选引擎之一**。

## 定位

Gemini是LD角色可调用的**引擎之一**：
- 长上下文处理
- 多模态任务
- 特定场景优化

## 调用方式

### 通过指令指定
```bash
/vibe-code --engine=gemini "优化性能"
```

### 直接调用
```bash
gemini "任务描述"
```

## 能力范围

### 代码任务
- 代码优化
- 性能分析
- 长文件处理

### 多模态任务
- 图片理解
- 文档分析
- 视觉相关代码

## 使用建议

根据 orchestrator.yaml 配置或用户指定使用。

如果没有配置或指定，默认使用主引擎。
