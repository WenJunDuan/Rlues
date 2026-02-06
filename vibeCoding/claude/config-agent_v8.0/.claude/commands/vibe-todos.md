# vibe-todos

增强 `/todos`，三态 Kanban 视图 + 文件联动。

## 语法

```bash
vibe-todos                # 显示看板
vibe-todos add "任务"     # 添加待办
vibe-todos start TASK-ID  # todo → doing
vibe-todos done TASK-ID   # doing → done
```

## 执行流程

```
1. /todos                         # 调用官方 todos
2. 读取 .ai_state/todo.md         # 待办
3. 读取 .ai_state/doing.md        # 进行中
4. 读取 .ai_state/done.md         # 已完成
5. 输出合并 Kanban 视图
```

## Kanban 输出格式

```
📥 TODO (3)                🔄 DOING (1)              ✅ DONE (2)
─────────────             ─────────────             ─────────────
[ ] TASK-1 搭建路由       [→] TASK-4 用户认证       [✓] TASK-5 DB模型
[ ] TASK-2 API接口                                  [✓] TASK-6 项目初始化
[ ] TASK-3 单元测试
```

## 三态流转规则

```
todo.md  ──start──→  doing.md  ──done──→  done.md  ──archive──→  archive.md
                        │
                    (max 3 并行)
```

约束：doing.md 中同时进行的任务不超过 3 个。超出时提醒先完成再开新任务。

## 任务 ID 格式

`TASK-{序号}` 自动递增，格式示例：

```markdown
## 📥 待办
- [ ] [TASK-7] 实现搜索功能 | effort:medium | path:B
- [ ] [TASK-8] 添加缓存层 | effort:low | path:A
```
