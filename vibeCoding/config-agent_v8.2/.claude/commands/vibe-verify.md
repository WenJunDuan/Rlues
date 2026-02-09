# vibe-verify

验证循环。触发 RIPER-7 V 阶段。

## 语法

```
vibe-verify
```

## 用户体验

```
你: vibe-verify

系统:
  ✓ 12/12 测试通过
  ✓ 3/3 plan 目标覆盖
  ✓ 验收标准全部满足
  ✗ 发现 console.log 残留 → 自动清理
  → done.md verified: true
```

失败处理: 1次→修复重试, 2次→加载 debugging skill, 3次→寸止人工介入。

加载 skills: verification。
