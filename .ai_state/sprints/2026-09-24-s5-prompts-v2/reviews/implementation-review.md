# Implementation review — S5 prompts v2

独立 reviewer：general-purpose 子 agent，只读，对照 gate/cli 源码逐条核 CLI 用法、模板路径、删除内容去向。

| 轮 | 结论 | 要点 | 处置 |
|---|---|---|---|
| r1 | CONCERNS | P0：athena-init 把 `cross_family_review` 写反（实为 A10 升 H3 硬门）。P1：pace 引用已删 mcp.md；roadmap playbook items schema 与模板不符；Bugfix 三段式两套叫法；宪法无条件 `athena init`；rules 失去路径作用域；DELTA 过宽、build 新校验无负例。P2：shell 空 heredoc 实为 warn；mapPrefix 首个匹配/目录键无斜杠/未匹配键静默；stages.md 何时列显示 kind；init 写序、位置参数、旧 git；残留 skip_roadmap/_index.skip_runtime_verify/compound；Pi 悬空引用；旧 CLAUDE.md 两条未记去向；review 窗口并行写者非 H4 机械项 | 全部修复：描述改正；链接测试扩到裸路径×三端；schema 对齐模板；统一 当前/期望/不变；宪法改「经用户同意」+ 三次失败条；rules 加 CC `paths`，决定记 core/rules.md；5 个 build 负例；最长前缀、斜杠一致、未匹配即失败；init 最后写 _index、拒位置参数、不依赖 --path-format；Pi 加 athena-vm/athena-requirements；K11 + coding 例外；execution.md 标为指引并给 `parallel_writers: 2` |
| r2 | CONCERNS | P1：athena-dev 仍「修改类先 athena init」。P2：security paths 漏 `.env*`；负例只断言退出码；_index「同名覆盖」无依据 | 改「经用户同意」；加 `**/.env*`；负例断言错误文本；改「同时生效，冲突以项目为准」 |

终态：r2 发现项全部修复；154/154；athena999 231 OK。test_build 对 skills/rules/agents 层整体声明为 S5 改写，逐文件约束由 test_prompts 承担（已知取舍）。

VERDICT: PASS
