---
name: execute
effort: high
context: fork
description: >
  代码实现。project.json stage 为 E 时触发。三级委托 + Task 循环。
allowed-tools: Bash, Read, Write, Edit, MultiEdit, Grep, Glob, Task
---

# Execute: E 阶段

读 .ai_state/project.json 取 test_cmd。
读 .ai_state/tasks.md 确认待办。
运行 `bash .ai_state/init.sh` 确认环境正常。

## 三级委托 (遇到错误立即降级，不要求用户手动操作)

<important>
禁止模拟工具调用。/codex:rescue 必须产生真实的 tool_use 响应。
如果调用后 /codex:status 没有显示对应任务，说明调用未实际执行 → 立即降级。
</important>

**Level 1: /codex:rescue**

生成 .ai_state/handoff.md (参照 templates/handoff.md), 必须包含:
- 实际文件树: `find . -name "*.py" -not -path "./venv/*" | head -50` (或对应语言)
- 与 Task 相关的代码片段 (关键函数/类，用 Read 工具取)
- Codex 可能无法访问项目文件，handoff.md 里的代码是它唯一信息源

```
/codex:rescue --background [Task描述], 参照 .ai_state/handoff.md
```

**验证链 (每步必须有真实 tool_use 响应，不接受自己编的文字):**
1. `/codex:rescue` → 必须返回 task ID 或确认信息
2. `/codex:status` → 必须显示该任务正在运行或已完成
3. `/codex:result` → 取回真实输出

如果 /codex:status 没有显示活跃任务 → /codex:rescue 没有实际执行 → 立即降级。

**取回后验证文件路径:**
- codex 提到的文件 → `test -f [路径]` 确认存在
- 引用不存在文件的结论 → 作废
- 幻觉超 50% → 整体作废 → 降级

**以下任一情况立即降级到 Level 2，不重试、不问用户:**
- `/codex:rescue` 没有产生真实 tool_use 响应
- `/codex:status` 没有显示对应任务
- `/codex:status` 显示 failed
- 等待超过 10 分钟无响应
- codex 命令不存在

**Level 2: @generator**

```
@generator [Task描述], 参照 .ai_state/handoff.md
```

**以下情况降级到 Level 3:**
- @generator 返回错误或无法启动

**Level 3: 手动 TDD**

自己写。superpowers TDD 自动激活。
1. 写测试 → 运行确认失败
2. 写实现 → 运行确认通过
3. 重构 → 确认仍通过

## Task 循环

每个待办 Task:

1. 按三级委托实现
2. 取回结果 → Claude 审查代码 (对照验收标准)
3. **立即运行测试** (不要跳过、不要交给用户):
   ```bash
   # 用 project.json 里的 test_cmd, 例如:
   npm test
   # 或 pytest, 或 uv run pytest, 或 cargo test
   ```
4. 测试失败 → `/debug` → 修复 → 重新运行测试 (循环直到通过)
5. 测试通过 → tasks.md: `- [x]` + progress.md: 追加一行
6. 下一个 Task

Path C/D: `/batch` 并行独立 Task 或 Agent Teams

## 完成

全部 [x] → `/simplify` → stage="T"

## Path A

Grep 定位 → 手动 TDD 修复 → 运行测试确认通过 → stage="T"
