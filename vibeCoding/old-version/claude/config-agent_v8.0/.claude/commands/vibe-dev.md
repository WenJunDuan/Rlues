# vibe-dev

智能开发入口。自动评估复杂度，路由到正确的 P.A.C.E. 路径。

## 语法

```bash
vibe-dev "任务描述"
vibe-dev --path=C "任务描述"    # 强制指定路径
vibe-dev --team "任务描述"      # 强制 Agent Teams (Path D)
```

## 执行流程

```
1. 读取 .ai_state/session.md      # 恢复上下文
2. 读取 .ai_state/doing.md        # 检查进行中任务
3. sou.search("任务关键词")        # 语义搜索相关代码
4. 评估复杂度 → 选择 P.A.C.E. 路径
5. 执行对应工作流
```

## P.A.C.E. v2.0 路由

| 路径 | 条件 | effort | 工作流 |
|:---|:---|:---|:---|
| A | 单文件, <30行 | low | R1→E→R2, 寸止仅结束时 |
| B | 2-10文件 | medium | R1→I→P→E→R2, 寸止在计划和结束 |
| C | >10文件 | high/max | 完整九步, 每阶段寸止 |
| D | 架构级/可并行 | max | Agent Teams, lead 寸止 |

## Path D (Agent Teams) 触发条件

满足任意两项即建议 Path D：
- 涉及 >3 个独立模块
- 前端/后端/测试可并行
- 预估 >4 小时
- 用户显式 `--team`

## 所有路径共同要求

1. 将任务写入 `.ai_state/todo.md`
2. 开始执行时移到 `.ai_state/doing.md`
3. 完成后移到 `.ai_state/done.md`
4. 核对 todo 与 done 一致
5. 调用 cunzhi 确认
