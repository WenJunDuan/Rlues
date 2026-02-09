# 官方指令参考

## 增强使用 (VibeCoding 先调用官方，再增强)

| Official | VibeCoding | 增强内容 |
|:---|:---|:---|
| /init | vibe-init | + .ai_state + .knowledge |
| /plan | vibe-plan | + KB + EXP + effort 映射 |
| /todos | vibe-todos | + 三态流转 + Kanban |
| /review | vibe-review | + code-quality + 安全 |
| /status | vibe-status | + .ai_state 全状态 |
| /resume | vibe-resume | + 上下文恢复 |

## 直接使用官方 (不增强)

```
/config     /permissions  /model    /mcp      /hooks    /plugin
/cost       /context      /stats    /usage    /help     /doctor
/clear      /compact      /rewind   /sandbox  /security-review
```

## 原则

1. 增强指令必须先调用官方版本
2. 官方功能 (统计/追踪/权限) 不被跳过
3. 官方更新自动继承
