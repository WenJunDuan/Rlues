---
name: iterative-retrieval
description: |
  Large context iterative retrieval. For tasks requiring
  information from many files, retrieves in batches to avoid
  overwhelming the context window.
---

# Iterative Retrieval Skill

## 策略

不要一次性读取所有相关文件。分批检索：

```
1. sou.search(高优先级关键词) → 核心文件
2. 分析核心文件 → 识别依赖
3. sou.search(依赖关键词) → 补充文件
4. 重复直到上下文充足
```

## 与 1M 上下文配合

虽然有 1M 窗口，但无意义地塞满上下文 = 浪费 token + 降低注意力。
精准检索 > 大量加载。

## 批次大小建议

| 上下文使用量 | 每批文件数 |
|:---|:---|
| <100K | 5-10 文件 |
| 100K-500K | 3-5 文件 |
| >500K | 1-2 文件 (考虑归档) |
