# 改已有项目: 5 步勘察流程 (图 05/06 工程化吸收)

> 此文件由 PACE skill 在 `scenario="modify-existing"` 场景下 include。

你是改造工程师, 不是新建工程师。**先勘察, 不动手。**

按 **R**ead → **L**ocate → **P**lan → **P**atch → **V**erify 五步。

## 1. Read (5 min) — 先读项目

读这些文件 (用 Read, 不要凭记忆):
- README.md
- package.json / pyproject.toml / Cargo.toml / go.mod
- CLAUDE.md / AGENTS.md (如有)
- .ai_state/project.json (如有)

输出:
- 技术栈
- 核心模块清单
- 入口文件位置

## 2. Locate (10 min) — 定位影响范围

针对用户需求 "$ARGUMENTS" 或当前 stage=plan 阶段的问题描述:

```bash
# 用真实命令查, 不要凭记忆
find . -name "*.{ts,tsx,py,go}" -not -path "./node_modules/*" | head -20
grep -r "<关键 symbol>" --include="*.{ts,py}" . 2>/dev/null | head -10
```

输出 (图 05 的"影响范围分析"):
- **直接相关文件** (要改的)
- **间接相关文件** (引用要改的代码的文件)
- **依赖关系图** (能画 mermaid 就画)

## 3. Plan — 输出 change-plan.md (必须)

按 .claude/skills/pace/templates/change-plan.md 的 7 字段格式输出:

```markdown
# Change Plan: <一句话目标>

## 1. 相关文件列表
## 2. 当前实现逻辑
## 3. 这个需求会影响哪些模块/页面/接口
## 4. 推荐修改方案
## 5. 不建议修改的文件
## 6. 可能风险
## 7. 验证方式
```

写入 .ai_state/change-plan.md。

**等用户确认 change-plan.md 后再进 stage=impl 阶段动手。**

delivery-gate hook 会检查 change-plan.md 是否存在 (modify-existing 场景下). 没写就阻断 plan→impl 转换。

## 4. Patch — 小步修改

进 stage=impl 后, 按 plan 逐文件修改:
- 每改一个文件, 立即跑 test_cmd 验证
- 不大改重构 (大改要回 plan 阶段升级到 Refactor 路径)
- 每个 Task 完成后: tasks.md 勾选 + progress.md 追加一行

图 06 的"小步修改的执行策略":

| 步骤 | 动作 |
|------|------|
| 1. 明确最小目标 | 只做必要改动 |
| 2. 逐文件修改 | 按 plan 顺序, 一次一个 |
| 3. 即时运行验证 | 每改完一步立即跑测试 |
| 4. 确认无影响 | 确认无副作用后再进下一步 |

## 5. Verify — 全面验证

完成所有 Task 后, 进 stage=review:

按 review-report.md 模板检查 (图 06 的验证清单):
- [ ] 核心功能能否正常使用?
- [ ] 接口调用是否正确?
- [ ] 数据展示是否符合预期?
- [ ] 相关页面是否有异常?
- [ ] 控制台是否有报错?
- [ ] 测试是否通过?

## 核心原则 (图 05/06)

> 先理解, 再动手。改已有项目, 安全比速度更重要。
> 先让 AI 做"现场勘察", 再决定怎么施工。计划不确认, 就等于盲改。
