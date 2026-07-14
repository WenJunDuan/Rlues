---
sprint_slug: ""
created: ""
path: ""                       # Refactor | System (其他路径不强制 polish)
polish_worker: ""              # 谁做的: 主 agent | polish_worker subagent
---

# Cleanup Pass — {sprint_slug}

> Refactor / System 路径强制. 由 polish/SKILL.md 触发.

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

## Finishing-a-development-branch (借 Superpowers)

完成后必须:
- [ ] 跑测试验证 (`npm test` / `pytest` / ...)
- [ ] 提示用户选: merge | 创 PR | 继续工作 | 丢弃
- [ ] 清理 worktree (`git worktree remove ...`)

## review 意见合并

[本 sprint 最新 reviews/passN.md 的 P1/P2 findings 在 polish 阶段一并处理. 列出已处理项]

- F1 (P1): [reviewer 提的问题] → ✅ 已处理
- F2 (P2): ... → ✅ 已处理
- F3 (P1): ... → ⏸ 推后 (理由: ...)

## 归档到 compound/

[本 sprint 的 learning / trick / decision 触发清单]

- [ ] compound/{date}-learning-{slug}.md (踩坑教训)
- [ ] compound/{date}-trick-{slug}.md (可复用模式)
- [ ] compound/{date}-decision-{slug}.md (技术决策)

## VERDICT

- ✅ Pass: 全部 5 检查项通过 + finishing 完成
- ⚠️ Concerns: 部分项推后 (列出原因)
