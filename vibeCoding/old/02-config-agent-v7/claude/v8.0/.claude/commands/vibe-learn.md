# vibe-learn

模式提取与 Instinct 学习。

## 语法

```bash
vibe-learn                 # 从当前会话提取模式
vibe-learn --export        # 导出 instincts
vibe-learn --import FILE   # 导入 instincts
```

## 执行流程

```
1. 分析当前会话中的模式
2. 提取 instinct (模式 + 置信度)
3. 写入 experience skill
4. 高置信度模式 → 建议 evolve 为 skill
```

## Instinct 格式

```yaml
- pattern: "API 路由总是需要输入验证"
  confidence: 0.85
  source: "3次重复观察"
  category: "coding-pattern"
```

## 演化路径

```
观察 → instinct (低置信度) → 多次验证 → instinct (高置信度) → evolve → skill
```
