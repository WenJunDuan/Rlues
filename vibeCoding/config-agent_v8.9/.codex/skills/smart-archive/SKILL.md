---
name: smart-archive
description: 智能归档 — V 阶段
---
1. .ai_state/ 完成文件 → .ai_state/archive/{date}/
2. 保留 conventions.md
3. 清理 session.md
4. 不清理 .knowledge/

## 降级
归档目录创建失败 → 状态文件内容追加到 conventions.md 底部保留。
