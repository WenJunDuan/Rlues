# 九步工作流 (Path C/D)

## 流程

```
需求创建 → 需求审查 → 方案设计 → 方案审查
    → 环境搭建 → 开发实施 → 代码提交 → 版本发布 → 完成归档
```

## 详情

| Step | 阶段 | Agent | 寸止 |
|:---|:---|:---|:---|
| 1 | 需求创建 | requirement-mgr | - |
| 2 | 需求审查 | requirement-mgr | [REQ_READY] |
| 3 | 方案设计 | design-mgr | - |
| 4 | 方案审查 | design-mgr | [DESIGN_READY] |
| 5 | 环境搭建 | impl-executor | - |
| 6 | 开发实施 | impl-executor | [PHASE_DONE] |
| 7 | 代码提交 | impl-executor | - |
| 8 | 版本发布 | impl-executor | [RELEASE_READY] |
| 9 | 完成归档 | experience-mgr | [TASK_DONE] |
