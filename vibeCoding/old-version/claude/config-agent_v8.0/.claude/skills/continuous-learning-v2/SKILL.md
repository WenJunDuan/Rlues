---
name: continuous-learning-v2
description: |
  v2 Instinct-based learning system. Builds confidence through
  repeated observations and evolves high-confidence patterns into skills.
---

# Continuous Learning v2 (Instinct System)

## Instinct 生命周期

```
观察 → 记录 instinct (confidence=0.3)
  → 再次观察同一模式 → confidence += 0.15
  → confidence > 0.8 AND count > 5 → 建议 evolve
  → evolve → 生成独立 skill 文件
```

## Instinct 格式

```yaml
- id: INST-{{序号}}
  pattern: "描述"
  confidence: 0.45
  observations: 3
  first_seen: "2026-02-06"
  last_seen: "2026-02-06"
  category: "coding-pattern"
```

## 存储

`.knowledge/experience/instincts.md`

## 命令集成

- `vibe-learn` → 手动触发提取
- `vibe-learn --export` → 导出 instincts JSON
- `vibe-learn --import FILE` → 导入 instincts
