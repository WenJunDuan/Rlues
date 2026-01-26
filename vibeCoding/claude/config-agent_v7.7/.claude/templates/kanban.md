# Kanban 模板

## 使用说明
此文件用于追踪任务状态，采用三栏看板：TODO → DOING → DONE

## 格式规范

### 任务格式
```markdown
- [ ] [文件名] 任务描述 (预计时间)
- [x] [文件名] 任务描述 ✓
```

### 状态流转
```
TODO → DOING → DONE
  │       │
  │       └── 完成时移入
  └── 开始时移入
```

---

## 模板

```markdown
# Kanban

## 项目
[项目名称]

## 更新时间
[自动更新]

---

### TODO
> 待执行的任务

- [ ] [file1.ts] 任务描述 (~30min)
- [ ] [file2.ts] 任务描述 (~45min)

---

### DOING
> 正在执行的任务 (同时只有一个)

---

### DONE
> 已完成的任务

---

## 统计
- 总任务: 0
- 完成: 0
- 进度: 0%
```

---

## 操作指南

### 开始任务
```yaml
操作: 从 TODO 移到 DOING
触发: beforeTask 钩子

示例:
  TODO:
    - [ ] [auth.ts] 实现登录
  
  变为:
  
  DOING:
    - [ ] [auth.ts] 实现登录
```

### 完成任务
```yaml
操作: 从 DOING 移到 DONE，打勾
触发: afterTask 钩子

示例:
  DOING:
    - [ ] [auth.ts] 实现登录
  
  变为:
  
  DONE:
    - [x] [auth.ts] 实现登录 ✓
```

### 任务回退
```yaml
场景: 任务失败需要重做
操作: 从 DOING 移回 TODO

示例:
  DOING:
    - [ ] [auth.ts] 实现登录
  
  变为:
  
  TODO:
    - [ ] [auth.ts] 实现登录 (重试)
```

---

## 与 TODO.md 的关系
```yaml
TODO.md: 完整任务列表，包含详细描述和阶段划分
kanban.md: 实时状态追踪，轻量级

同步规则:
  - 任务创建 → 两者都添加
  - 状态变更 → kanban.md 更新
  - 完成确认 → TODO.md 打勾
```
