# Gemini Integration

## 说明
此文件是 Gemini 集成的占位符。请从官方渠道获取 Gemini 的完整 SKILL.md。

## 下载来源
- Google AI 官方文档
- Claude Code 插件市场

## 预期能力
```yaml
长上下文:
  - 处理大型代码库
  - 多文件理解
  - 完整项目分析

多模态:
  - 图像理解
  - 图表分析
  - 设计稿解读
```

## VibeCoding 集成

### 调用时机
```yaml
Research 阶段:
  - 大型项目分析
  - 多文件依赖梳理

Innovate 阶段:
  - 设计稿理解
  - 架构图分析
```

### 配置
```yaml
# orchestrator.yaml
engines:
  available:
    - name: gemini
      model: gemini-2.0-flash
      strengths: [long-context, multimodal]
      skill_path: .claude/skills/gemini/SKILL.md
```

## 安装后
替换此文件为官方完整 SKILL.md，包含:
- API 调用方式
- 上下文限制说明
- 多模态使用方法
- 最佳实践
