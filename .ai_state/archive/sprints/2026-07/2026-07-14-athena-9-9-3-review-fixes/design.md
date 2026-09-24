# Athena 9.9.3 Review-Fix Design

## Why

9.9.3 已具备大部分发布实现，但 review 发现 Codex breadcrumb 安装路径错误、核心 evaluator 语义偏离最终设计、M5 产物缺失、validator 基线错误、发布卫生与证据漂移。目标是修正真实行为与发布合同，而不是只改文案绕过失败。

## Scope

- 修复 CC/CX breadcrumb 解析、安装路径与总行数预算。
- 对齐 CC/CX evaluator 的反过度工程 VERDICT 规则。
- 补齐双端包根设计与 harness-iteration v1.1 产物。
- 将 release validator 基线切到 committed 9.9.2，并补覆盖上述缺口的负向/实装测试。
- 清理发布垃圾文件，刷新最终真实验证记录。
- 不改 9.9.2 包内容，不修改用户私有配置，不把临时 npm/runtime 依赖提交进仓库。

## Acceptance Criteria

- AC1: fresh CX setup 仅存在 canonical `~/.agents/skills/pace/...` 时，UserPromptSubmit 能输出当前 stage breadcrumb；canonical 与 stale `~/.codex/skills` 同时存在时必须优先 canonical；`breadcrumb: off`、缺索引、缺 stages 时静默 fail-open。
- AC2: CC/CX breadcrumb 的 `additionalContext` 总行数均不超过 10 行，且包含 stage/path/sprint/next_action 与当前 stage 义务。
- AC3: CC/CX evaluator 对 1 个或 2 个未消化 over-engineering finding 均输出 CONCERNS；finding 已明确消化且无其他阻塞时才可 PASS。reviewer 样例标识与 evaluator 合同须双端一致，并在正式 evaluator 行为冒烟中验证。
- AC4: M5 的唯一合同是“包根可分发工件”，不是 Athena 内置/自动安装 skill；skills 数保持 26。`build-spec-final.md` 与 `harness-iteration-v1.1.md` 在 CC/CX 9.9.3 包根可读且双端内容一致，BUILD-SPEC/CHANGELOG/RELEASE 均明确用户手动安装/替换边界且无断链。
- AC5: validator 明确保护 committed 9.9.2 双端树与工作区，不再错误声明 9.9.1 是 baseline。临时 Git fixture 分别证明 tree hash 漂移、staged、unstaged、untracked 9.9.2 内容都会失败，负向测试不得修改真实 9.9.2 树。
- AC6: 9.9.3 release roots 无 `.DS_Store`、`__pycache__`、`*.pyc`、`tmp`。
- AC7: Codex doctor/prompt-input 对 spawn failure、timeout、signal、非零退出、成功但非 JSON 均先报真实 binary/exit/stderr，再决定是否解析；只有 exit=0 且 stdout 为 JSON 时可进入语义断言。
- AC8: 使用临时安装且路径明确的 exact `@openai/codex@0.144.1`，保存 binary 路径与 `codex --version`；release validator、CX runtime、CC runtime、fresh setup/doctor/prompt-input 零 FAIL、零未审 SKIP。无法获得完整 runtime 必须 BLOCKED，不得降为 SKIP/PASS。
- AC9: RELEASE/CHANGELOG active 9.9.3 的配置、模型与验证数字由最终保存输出交叉校验；不得保留旧 PASS/FAIL/SKIP 数字、旧 model pin 或“环境失败等同 package PASS”表述。
- AC10: 9.9.3 正式 review 最新 passN 为 PASS，polish/architecture/compound 收口；提交后实际 fast-forward main，删除任务 worktree 与已合并分支，推送 `origin/main`。最终 `git worktree list --porcelain` 无任务 worktree、`git branch --list codex/athena-9.9.3-review-fixes` 为空，`git fetch origin main --prune` 后 `git rev-list --left-right --count main...origin/main` 为 `0 0`。

## TDD Strategy

1. 先为 CX fresh-install/canonical 优先级 breadcrumb、总行数、evaluator policy、双端根产物、9.9.2 baseline 四种漂移和 Codex 进程失败形态写失败测试并保存 RED 输出。
2. 最小实现修复后运行定点 GREEN。
3. 跑双端 runtime 与完整 validator；发现新失败回 impl，最多 4 轮。

## Runtime-Verify Readiness

- Checker: Python unittest、Node runtime harness、release validator、temp HOME setup、Codex doctor/prompt-input、`git diff --check`。
- 最大迭代: 4 轮；仍失败则保留 stderr 与已试方案，不降级为 PASS。
- 允许写集: 9.9.3 双端包、9.9.3 scripts/fixtures/tests/validator、当前 sprint、architecture/ 与单个 compound learning。
- 禁止: 9.9.2 包、用户 HOME、远端服务、现有 9.9.2 trace/token 记录。

## TDD Evidence Contract

主 agent 落 `tdd-evidence.yaml`，每条记录包含 `ac_id`、`test_file`、`red_command`、`red_exit_code`、`red_summary`、`implementation_started_after_red`、`green_command`、`green_exit_code`、`green_summary`。AC1–AC9 每项至少映射一条自动化或正式 evaluator 行为证据；不存在 RED 的既有回归必须如实标 `pre_existing_green`，不得伪造。

## Round 1 · Critic Findings

**VERDICT: NEEDS_REVISION**

- P1: 补实际 merge/worktree/branch/push/remote 0 0 终验。
- P1: 明确 M5 为包根可分发工件，不是第 27 个 Athena skill；同步修正 BUILD-SPEC 合同。
- P1: evaluator 增加 1/2 unresolved 与 resolved 行为矩阵。
- P1: Codex 0.144.1 exact binary + 多失败形态必须 fail-closed。
- P2: baseline 覆盖 tree/staged/unstaged/untracked；canonical skill root 优先；TDD evidence schema；验证数字机械交叉校验。

## Round 2 · Critic Findings

**VERDICT: PASS**

- AC10 已覆盖实际 fast-forward merge、worktree/分支删除、push 与远端 `0 0` 终验。
- AC4 已把 M5 收敛为双端包根可分发工件，不新增第 27 个内置 skill，并要求同步修正文档合同。
- AC3 已明确 1/2 unresolved 与 resolved 三组双端 evaluator 行为矩阵。
- AC7–AC8 已要求 exact Codex 0.144.1、版本证据与五类进程失败 fail-closed。
- AC5、TDD evidence 与 AC9 已覆盖 baseline 四态、RED→GREEN 映射与最终数字交叉校验。

结论: 可进入 TDD implementation。
