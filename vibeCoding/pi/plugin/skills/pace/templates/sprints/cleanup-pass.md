---
sprint_slug: ""
created: ""
path: ""                       # Refactor | System (其他路径不强制 polish)
polish_worker: ""              # 谁做的: 主 agent | polish_worker subagent
---

# Cleanup Pass — {sprint_slug}

> Refactor / System 强制. 电宝体: 五项各一行结论。VERDICT 须含 PASS/completed/完成。

## 5 检查项 (借 polish skill)

### 1. 临时代码 / 调试痕迹
- 检查 `console.log` / `print` / `debugger` / TODO/FIXME 标记
- 行动: [清理列表 / 已清理]

### 2. 注释完整性
- 检查公开 API / 复杂逻辑是否有文档
- 行动: [补充列表 / 已补充]

### 3. 冗余 / 重复代码
- 检查相似函数 / 复制粘贴块
- 行动: [提取/合并列表]

### 4. 低效模式
- 检查 N+1 query / 阻塞 IO / 无谓循环
- 行动: [优化列表]

### 5. 过度设计
- 检查 YAGNI 违反: 未来才用的抽象 / 没必要的接口
- 行动: [简化列表]

## Finishing-a-development-branch

polish 在独立 review 之前。本阶段只跑受影响测试并留下 worktree。
- [ ] 跑测试验证 (`npm test` / `pytest` / ...)
- [ ] **不要** merge / 开 PR / `git worktree remove`
- [ ] 下一动作是一次独立 review，不是 ship

## review 意见合并

polish 不读取 implementation-review 作为前置。本段只记本轮清理中发现并处理的问题。

- F1 (P1): [reviewer 提的问题] → ✅ 已处理
- F2 (P2): ... → ✅ 已处理
- F3 (P1): ... → ⏸ 推后 (理由: ...)

## 归档到 compound/

[本 sprint 的 learning / trick / decision 触发清单]

- [ ] compound/{date}-learning-{slug}.md (踩坑教训)
- [ ] compound/{date}-trick-{slug}.md (可复用模式)
- [ ] compound/{date}-decision-{slug}.md (技术决策)

## VERDICT

- ✅ Pass: 全部 5 检查项通过；测试绿；worktree 仍在，交给 review
- ⚠️ Concerns: 部分项推后 (列出原因)
