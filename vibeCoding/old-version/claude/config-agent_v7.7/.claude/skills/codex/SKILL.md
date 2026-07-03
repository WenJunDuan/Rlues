# Codex Integration

## 说明
此文件是 Codex 集成的占位符。请从官方渠道获取 Codex 的完整 SKILL.md。

## 下载来源
- OpenAI 官方文档
- Claude Code 插件市场

## 预期能力
```yaml
代码生成:
  - 从描述生成代码
  - 补全代码片段
  - 生成样板代码

重构:
  - 代码转换
  - 语法更新
  - 模式应用
```

## VibeCoding 集成

### 调用时机
```yaml
Execute 阶段:
  - 大量 CRUD 代码
  - 重复模式生成
  - 样板代码填充
```

### 配置
```yaml
# orchestrator.yaml
engines:
  available:
    - name: codex
      model: codex-latest
      strengths: [code-generation, refactoring]
      skill_path: .claude/skills/codex/SKILL.md
```

## 安装后
替换此文件为官方完整 SKILL.md，包含:
- 详细 API 调用方式
- 参数配置
- 最佳实践
- 示例代码
