# RIPER-7 工程编排 (Codex)

## 统一工具调度表

| 阶段         | Skill                     | MCP                       | 状态文件    |
| :----------- | :------------------------ | :------------------------ | :---------- |
| R₀b 头脑风暴 | brainstorm                | augment-context, deepwiki | design.md   |
| R 研究       | context7                  | augment-context, deepwiki | design.md   |
| D 设计       | context7                  | deepwiki                  | design.md   |
| P 规划       | plan-first                | —                         | plan.md     |
| E 开发       | tdd, code-quality         | augment-context           | doing.md    |
| T 测试       | verification, e2e-testing | chrome-devtools           | verified.md |
| V 验收       | smart-archive, knowledge  | cunzhi                    | review.md   |

## 阶段详情

### R₀b — 头脑风暴 (Path B+)

💡 理解需求, 探索方案, 不写代码

1. augment-context-engine 搜索现有代码
2. 读 .knowledge/pitfalls.md
3. 加载 skills/brainstorm — 逐个提问, 方案对比
4. deepwiki 查候选库文档
5. 输出 .ai_state/design.md
6. cunzhi [DESIGN_DIRECTION]

### R — 研究

1. context7 拉取库文档
2. 验证方案可行性
3. 更新 design.md

### D — 设计

1. context7 查 API 细节
2. 写入 .knowledge/decisions.md
3. 完成 design.md 终稿
4. cunzhi [DESIGN_READY]

### P — 规划

1. /plan 进入规划模式
2. 读 design.md → 生成 plan.md
3. cunzhi [PLAN_CONFIRMED]

### E — 执行

1. TDD 分级 (Path A: 手动验证 / B: 关键测试 / C+: 全覆盖)
2. 逐个执行任务:
   - Path A: 直接开始开发 (无 plan.md)
   - Path B+: 按 plan.md 任务列表逐个执行
3. doing.md 更新 TODO→DOING→DONE
4. Path C+: /collab 启动协作模式, 并发 shell 执行

### T — 测试

1. verification 分级清单
2. Path C+: chrome-devtools 浏览器调试
3. 输出 verified.md

### V — 验收

1. delivery-gate hook 自动检查
2. cunzhi [DELIVERY_CONFIRMED]
3. 加载 skills/knowledge — 沉淀经验到 .knowledge/
4. 加载 skills/smart-archive — 归档 .ai_state/
