# vibe-plan

增强 `/plan`，生成结构化方案并写入 `.ai_state/plan.md`。

## 语法

```bash
vibe-plan "任务描述"
```

## 执行流程

```
1. /plan "任务描述"               # 调用官方 plan
2. sou.search("相关代码")         # 语义搜索上下文
3. 检索 .knowledge/               # 知识库参考
4. 检索经验库                     # 历史模式
5. 生成结构化方案 → .ai_state/plan.md
6. 从方案提取 TODO → .ai_state/todo.md
7. cunzhi [PLAN_READY]            # 寸止等待确认
```

## plan.md 输出格式

```markdown
# 方案: {{任务标题}}

## 目标
{{简明目标描述}}

## 技术方案
{{实现方案，含数据结构设计}}

## 影响范围
- 文件: {{涉及文件列表}}
- 模块: {{涉及模块}}
- 风险: {{潜在风险}}

## 任务拆解
1. [ ] {{子任务1}}
2. [ ] {{子任务2}}
...

## effort 级别
{{low/medium/high/max}} — 理由: {{评估依据}}

---
Created: {{timestamp}}
P.A.C.E. Path: {{A/B/C/D}}
```

## 与 todo.md 联动

plan.md 中的任务拆解会自动同步到 todo.md，格式：

```markdown
## 📥 待办
- [ ] [PLAN-1] {{子任务1}} (来源: plan.md)
- [ ] [PLAN-2] {{子任务2}} (来源: plan.md)
```
