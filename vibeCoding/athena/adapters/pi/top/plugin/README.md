# plugin · athena-pace

这是**插件**，不是私人配置。私人配置在 [`../config/`](../config/)。

Pi package：PACE + `.ai_state` 合同 + 门禁 + 核心 prompt。  
`.ai_state/` 在**每个项目仓库**，本包不携带 sprint。

```bash
pi install /绝对路径/vibeCoding/dist/pi/<版本>/plugin     # 本地包
pi install git:<host>/<owner>/<repo>@<tag>               # git 源；仓库根须是本包
```

Pi 版本：≥ 0.87。`peerDependencies` 按 Pi packages 约定写 `"*"`（宿主提供，不打包）。包版本 = Athena VERSION。

## 装进去什么

| 层 | 内容 |
|---|---|
| extensions | `athena-gates`（bash/write 门禁，`agent_before_settle` 硬 Stop）· `athena-lifecycle`（面包屑、compact、铁律短注入） |
| skills | pace · athena-dev · athena-init · athena-status · brainstorm · roadmap · athena-review · polish · athena-runtime-verify · architect-doc（由 core 生成） |
| prompts | `/generator` `/reviewer` `/architect` `/polish-worker` |
| core/IRON.md | 宪法（由 core/package/AGENTS.md 生成；lifecycle 每轮追加进 system prompt） |

不含：你的模型/API、fff/btw 等第三方包、quantum 业务 skill。那些放个人 `settings.json`。

## 新项目

git 仓库里 `/athena-init` → 建 `.ai_state/`。已有不覆盖。

## 硬 Stop

- 触发：`stage=ship` 收尾时 H2（证据）/ H3（审查）不过。
- 形态：`agent_before_settle` 返回 `{ entries: [...event.entries, 纠偏消息], continue: true }` → Pi 必须再发一次模型请求，agent 不能就此收尾。纠偏消息是 `custom_message`（`customType: athena-stop`），内容为门禁原因。
- 只评一次：Stop 只在 `agent_before_settle` 评估；`agent_end` 在硬停可用时不评估、不记账。
- 防循环：门禁核熔断，同一原因连续 3 次 → 放行 + `issues.md` 记一行 gate，UI 提示一次。不会无限续跑。
- 不拦：`outcome` 为 `aborted` / `error`（用户中断、模型出错不算交付声明）；非 ship 阶段；idle。
- 回退：Pi < 0.87 或读不到宿主版本 → `agent_end` 发 followUp 软纠偏（旧行为，同因只发一次）。

## codemode

- 外层 `codemode` 调用（入参是 JS 源码）放行，不解析脚本。
- 脚本里调的每个内置工具照常触发 `tool_call`（带 `parentToolCallId`）→ `write` / `edit` 走 H1，`bash` 走 H5，和直接调用同判。
- 写工具识别：`write`、`edit`，路径键 `path`（Pi 1.0.2 源码核对）。

## 限制

- `powershell` 工具不走 H5（只识别 `bash`）。
- 红区无 `isolation: worktree`，用 git worktree。
- 门禁逻辑进程内调用包内 `core/gate/hook.cjs`（与 `~/.athena/<ver>/` 同字节的 vendored 门禁核，由 build 生成）。

## 待本机验证

本包扩展未在真实 Pi 里跑过；适配逻辑由 fixture 覆盖（`evals/fixtures/test_pi_hard_stop.py`），`.ts` 已对 Pi 1.0.2 类型做过类型检查。

- `agent_before_settle` 硬停实跑：ship 无证据 → 续跑一轮 → 补证据后正常收尾。
- 熔断实跑：同因第 3 次放行，`issues.md` 有记录，UI 有提示。
- 宿主 `VERSION` 导出可读（读不到会静默回退 followUp）。
- codemode 脚本内 `write` 无 AC 时被拦，脚本拿到的是 block 原因。
- `pi install git:…` 装本包；包版本号带 `-dev` 后缀时 Pi 是否接受。
