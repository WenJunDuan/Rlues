---
version: "9.9.6"
type: "release"
slug: "athena-9.9.6"
status: "current — hotfix2 W35-W40 runtime verified"
updated: "2026-07-29"
supersedes: "athena-9.9.3.md"
---

# Athena 9.9.6 架构现状

主题：**Native Surface · Thin Prompt · Bounded Context**。

9.9.3 的两个内核不变 —— PACE(4 核心 + 5 条件 stage、红黄绿区、2+1 review、fail-closed gates) 与 `.ai_state`(持久化项目真相 + 有界检索入口)。9.9.6 hotfix2 保留这些边界，并把控制面收敛为：平台合同、常驻预算、护栏强度、语义契约。**26 个 skill 一个未删未并，PACE stage 一个未增未改名。**

## hotfix2 控制面现状 (W35-W40, 2026-07-29)

- 普通 prompt/Bash/Edit/MCP 不再写 raw `tool-trace`、token 明细或 compact snapshot；Stop 只保留 delivery-gate，validation command 才落脱敏 evidence。
- re-route 以 git diff/cached/untracked 三探针为源；breadcrumb 独立于 `next_action` 且受 240B 预算约束，`next_action` 只接受机器枚举。
- read-only architect/critic/reviewer/spec-compliance/explorer 走平台原生结果，不创建 writer lifecycle/violation；未隔离 writer 在 System 仍 fail-closed。
- AC 统一走 admissible evidence，模板/gate 对 manifest 采用 opt-in 单一契约；Codex fresh config 不手填 provider URL、context window 或 auto-compact 元数据。
- 新仪器 `vibeCoding/scripts/athena-metrics.py` 以 git 单源输出代码/手写状态量与 `verdict_ac2=PASS` 度量代理；真实 sprint 同时用 read-only/worktree 行为夹具验证设计 AC2，AC9 A/B 留给下一 sprint。

## 与 9.9.3 的架构差异

### 1. 注入层：从"整段倾倒"改为"字段白名单"

9.9.3 的 SessionStart 注入 `_index.md` 的**整份 frontmatter**(73 键，含注释与 `route_history`)。9.9.6 改为白名单渲染：

```
core      version / path / stage / 双 slug / next_action / plan_model / platforms_enabled
skip      仅当值为 true 才输出
pointers  latest_decisions / latest_lessons 只留首项 + "(+N more)"
```

`latest_design|review|cleanup|requirement` 由 memory router 段负责，白名单不重复注入。历史、统计、能力探测一律改为按需 Read。

摘要截断从**按字符**改为**按字节** —— 中文 1 字 3 字节，600 字符的旧上限实际产出约 1,800 字节，超预算 3 倍。

同时修了 CX `parse_frontmatter` 不剥引号与行尾注释的缺陷 —— 该缺陷导致 CX 的 `stage` 长期解析成 `"impl"   # 注释`，`stage_hints` 静默失效。

### 2. Skill 层：路由与正文分离

| 层 | 何时常驻 | 9.9.6 做法 |
|---|---|---|
| catalog(name+description) | 每轮 | 26 条 description 改 trigger-only：只写触发条件、对象、非目标 |
| SKILL.md 正文 | 调用后留到会话结束 | 10 个超 4 KB 的单文件 skill 正文下沉 `references/playbook.md`(原文未改，可逆) |
| references / templates | 按需 Read | 不变 |

判据来自官方 skills 文档的生命周期定义："the rendered SKILL.md content enters the conversation as a single message and **stays there for the rest of the session**"。

副作用 skill 双端锁隐式调用：CC `disable-model-invocation: true`(官方："Only you can invoke"，且其描述不进 context)；CX `<skill>/agents/openai.yaml` 的 `policy.allow_implicit_invocation: false`。

**未合并任何 skill** —— 合并提案在 review 中被否：(a) 会推翻 `compound/2026-07-13-decision-quantum-7-to-2-consolidation.md` 的既有用户决策(quantum 已按"生成 vs 运行时读取"分轴合到 2 个 hub)；(b) catalog 瘦身后合并净收益降至约 200–300 字节，代价是命令与门禁合同。

### 3. 状态层：并发写者必须走原子 IO

`_index.md` 是双端多个 hook 的共享可写状态。同事件的 command hooks 并发执行、不保证顺序；read-modify-write 会 lost update，**丢的是 `design_changed_after_impl` 这类门禁标记且不报错 —— 静默放行**。

```
_index-io.cjs / _index_io.py
  acquire()      O_EXCL 锁文件 + stale(10s) 自动打破 + 800ms 超时退化(告警不阻塞)
  update()       读-改-写全程持锁
  write_atomic() tmp + rename
```

接入者：`index-updater`、`design-change-detector`、`pace-continuator`(双端各 3)。`token-usage-collector` 本已原子写。

### 4. 护栏层：强度必须匹配权限面

Codex 端运行在 `approval_policy = never` + `sandbox_mode = danger-full-access`，9.9.3 却只给了平坦正则护栏，覆盖面约为 CC 的 1/4。9.9.6 把 CX `pre-bash-guard` 对齐 CC 的 shell 分析器：

递归命令替换(不可解析 fail-closed) · 目标路径归一化(`//` `/*` `/**` `/.` 尾斜杠) · env 前缀剥离 · `bash -c`/`eval`/`xargs` 内层重分析 · `git` 带值选项定位 · 管道 `curl|wget → shell` · 深度上限 2 · 解析失败 fail-closed。

实测已修复的绕过：`rm -rf /*`、`rm -rf //`、`rm -rf /.`、`rm -rf $HOME/`。
**已知共有限制**：`` rm -rf `echo /` `` 双端都拦不住 —— 替换结果需执行才可知，静态分析做不到。

### 5. 语义层：sprint contract

`checklist.yaml` 顶部的 `done_contract` 成为 generator 与 evaluator 的**共同判据**，堵评审的两大失效模式：自评偏高、评审时移动球门。判据变更必须回 design，不在 impl 里私改。

### 6. 平台原语优先

`runtime-verify` 双端统一用官方 `/goal` 承载。Codex goals 自 rust-v0.133.0 起 default-on 且不再 experimental，CX 此前自造的 Step 0–3 状态机是铁律[不抱金饭碗讨饭]的直接违反 —— 这是 9.9.3 双端唯一的**机制路线**分歧。

## 常驻预算(实测字节)

| 指标 | 9.9.3 | 9.9.6 | 门 |
|---|---:|---:|---:|
| CC SessionStart | 7,801 | 2,316 | ≤2,500 |
| CX SessionStart | 7,631 | 2,241 | ≤2,500 |
| CC breadcrumb | 797 | 291 | ≤400 |
| CX breadcrumb | 1,008 | 295 | ≤400 |
| CC skill catalog | 8,621 | 3,149 | ≤4,000 |
| CX skill catalog | 8,834 | 3,744 | ≤4,000 |
| SKILL.md 热路径合计 | 93,327 | ~26,700 | 单文件 ≤4,096 |

## 双端对称性合同

| 维度 | 状态 |
|---|---|
| `.ai_state` schema | 一致 |
| PACE stage / 路由语义 | 一致 |
| 26 skill 名与职责 | 一致(6 个字节级一致，其余语义一致) |
| runtime-verify 载体 | **9.9.6 起一致** —— 双端都用 `/goal` |
| hook 事件面 | 不对称且诚实标注：CC 独有 `Notification`/`ConfigChange`/`InstructionsLoaded`/`StopFailure`(Codex 无对应事件) |
| 工具名 | 不伪造对称。Codex 只认 `apply_patch`(别名 `Edit`/`Write`)；`MultiEdit` 已从 matcher 移除 |
| 角色模型 | 分层对齐、值不同：fable/opus ↔ sol/terra |

## 校验入口

```
python3 vibeCoding/scripts/validate-athena-9.9.6.py     # 66 PASS / 0 FAIL / 0 SKIP (local-only)
python3 vibeCoding/scripts/athena-metrics.py . <sprint-slug> <base-ref>
```

覆盖：包结构 · env 黑名单(每条挂官方出处) · provider/multi_agent_v2 合同 · 双端角色矩阵 · skill frontmatter/catalog/热路径预算 · 隐式调用锁 · hook 文件齐全与死 matcher · `_index` 无非原子写 · pre-bash-guard 14 例绕过回归 · sprint contract 与 `/goal` 双端命中 · 宪法无 legacy verification 劝导 · 四项注入预算实跑实测。

**不覆盖**：A/B eval、migration/rollback。这些是独立的 runtime/发布门；hotfix2 本轮已覆盖双端安装态、边界、脱敏、配置解析与 SQLite 可读性。

## 未决与风险

1. **A/B eval 尚未执行** —— AC9 的 N≥3 质量/回合/p50 对照留给下一 sprint；本轮记录 `verdict_ac2=PASS` 度量代理，并用行为夹具完成设计 AC2 判定。
2. **CX 红区 worktree 只有审计、没有门禁。** Codex 0.145 MultiAgent V2 的 `spawn_agent` handler 不派发 `PreToolUse`，故不注册该 matcher（死分支）。改用 `subagent-worktree-audit.py` 挂 `SubagentStart` 事后检测 + 落 `worktree-violations.jsonl`；CC 端仍为 `PreToolUse(Agent)` 真阻断。剩余缺口：违规记录未接入 ship 门禁。
3. 模型实调仍受阻：CC CLI 未登录；Terra 在账户目录可见，但直连和本地代理均因 TLS handshake EOF 未完成请求。
4. 无 A/B eval，无 migration/rollback fixture，无 N≥3 统计。
5. **并行写者风险已实证**：本次迭代中另一会话多次覆盖 `settings.json` / `config.toml`；旧 validator 还曾把错误合同硬编码为 PASS。当前已确认单一写者并把用户最终合同写入 validator。
