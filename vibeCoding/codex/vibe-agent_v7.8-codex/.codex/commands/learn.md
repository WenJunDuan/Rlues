---
name: learn
description: 提取当前会话中的可复用模式
---

# learn - 提取会话模式

## Usage

```bash
learn                      # 提取所有模式
learn --type=debugging     # 特定类型
learn --dry-run            # 预览
```

## Workflow

1. **分析会话** - 扫描问题和解决方案
2. **识别模式** - 过滤可复用的非显而易见模式
3. **确认** - 展示发现供用户确认
4. **存储** - 保存到 `.ai_state/experience/learned/`
5. **更新索引** - 添加到经验索引
