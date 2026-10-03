# 门禁（Athena 10.1）

一个 JS 门禁核（`~/.athena/current/hook.cjs`），三端同一套规则。硬门 fail-closed：拦下并给 reason；提示项只 warn。规则表见 [stages.md](stages.md)。

## 硬门

| id | 何时查 | 放行条件 |
|---|---|---|
| H1 | 写文件前（仓库内、`.ai_state` 外） | 当前 sprint design.md 有 ≥1 条非占位 `- ACn:`（行首锚定，如 `- AC1: 导出 CSV 含表头`） |
| H2 | ship 时 Stop | 主仓 `.ai_state/.runtime/evidence/<sprint>.jsonl` 有 provable、exit 0、tree_sha 等于当前源码树的记录 |
| H3 | ship 时 Stop | `sprints/<slug>/review.json` PASS、tree_sha 与 AC 摘要都等于当前 |
| H4 | 派子 agent 前 | 红区（Refactor/System 或 `parallel_writers ≥2`）的写者隔离：CC `isolation: worktree`，或任务里写 `worktree: /abs/path`（已注册的非主 worktree） |
| H5 | 执行 shell 前 | 危险命令表；推送本项目仓库只在 ship、brainstorm、roadmap 或空闲时放行；直接改门禁账本被拦 |

源码树 sha 不含 `.ai_state` 和 design 的 `review_ignore`。改了源码，旧证据和旧 review 就不再对得上——这是设计，不是误拦。

## 证据可证明性（H2）

`athena run [--env K=V] -- <cmd>` 记录 exit 与 tree_sha。`--env` 可多次，注入子进程并写进 command 与独立 env 字段；显式 env 的重放内容保留完整长度（仍脱敏），不采集调用时的隐式 env。变量名任意位置含 KEY、TOKEN、SECRET、PASSWORD、PASSWD、PWD、CREDENTIAL、AUTH、DATABASEURL/DATABASE_URL，或以 PASS 结尾、含 PASS_ 时拒收；仅精确名称 TOKENIZERS_PARALLELISM、MAX_TOKENS、KEYBOARD_LAYOUT、MONKEY 作为误报白名单。白名单也须通过序列化赋值的基线凭据脱敏检查，凭据改走 env 文件。以下判为 unprovable：
- 检查放后台（`&`），或 `||` / `exit` / `exec` 让检查可能不跑；
- 检查后还有非 `&&` 的命令，或管道没开 `pipefail`；
- `trap`、`alias`、函数、`source`（venv activate 除外）、`PATH=` 可能遮蔽检查命令；
- 显式 `--env` 覆盖执行环境族（大小写不敏感）：`npm_config_*` / `NPM_CONFIG_*`、`HOME`、`USERPROFILE`、`XDG_*`、`NODE_*`、`PYTHON*`、`PYTEST_*`、`LD_*`、`DYLD_*`、`BASH_ENV`、`ENV`、`SHELL`、`PATH`、`COMSPEC`、`*_OPTIONS`、`*_OPTS`、`*_ADDOPTS`、`*_CONFIG*`、`*RC`：允许执行并记录，因可改变执行体、配置或测试收集（含 `HOME/.npmrc` 的 script-shell），标记 `validation_shadowable`，不能用作 H2 证据。普通功能开关如 `QUANTUM_AGENT_LIVE`、`CI`、`TEST_MODE` 仍可证明；
- argv[0] 被包装、运行期间源码树变了。
- 测试 exit 0，但输出中任一明确汇总为零用例或全跳过（node `ℹ tests N` / `# tests N` 为 0 或 skipped 等于 tests；pytest `collected 0 items` / `no tests ran` 或全 skipped，支持附加 `N subtests passed` 等计数，含 npm test 包装）：标记零用例，后续非零汇总不能覆盖；未知格式按现状。

reason 字段写明原因；照 reason 改写命令后重跑。

## 提示项（A1–A10）

写者溯源、R/S 的 runtime-verify 与 polish 记录、architecture 更新、记账闭合、design 在实现后改动、指针存在、梳理阈值、豁免将到期、Bugfix 复现测试被改（`bugfix_test_lock`）、reviewer 与作者同家族（开 `flags.cross_family_review` 后升为 H3 硬门）。warn 不拦；ship 前看一遍。

## 豁免

`athena exemption add --key <key> --until <YYYY-MM-DD> --reason "<理由>"`；同 key 重加替换旧条目。`athena exemption list` 查看，`athena exemption remove --key <key>` 撤销。CLI 写 `_index` frontmatter并回读校验，增删在 issues.md 留 closed 审计行（撤销记录原理由）；审计失败回滚 `_index`。remove 可按原样 key 撤销既有无效条目，add 仍只允许下列 key。

`until` 按 UTC 当天包含，不能早于今天、截止时刻距现在 ≤14 天；reason 必填。key ∈ `h4_worktree`、`skip_runtime_verify`、`skip_polish`、`skip_architecture_check`、`harness_target_outside_repo`。H2/H3 没有豁免。过期或无效条目被忽略，`athena exemption list` / `athena status` 会列出。

## 熔断与误拦

同一 Stop 拦截连续 3 次：放行本次，并在 issues.md 记一条 G 行。认为是误拦：`athena issue add --type gate --text "<门禁 id + 命令/路径 + 为什么是误拦>"`，请用户决定；不要改写 `.runtime` 或账本绕过。
