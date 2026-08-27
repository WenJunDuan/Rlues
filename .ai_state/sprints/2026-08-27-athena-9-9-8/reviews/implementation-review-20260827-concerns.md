---
schema_version: 1
mode: implementation
packet_sha256: "c68cd5ea7597238654f16f2177a863b936aabc6f65011ad00583da31c8aa5eb8"
reviewed_diff_sha256: "26e8abecd8bb23adb3df808281e9b21d050a49c341026e34c3496327b93bf764"
reviewed_tree_sha256: "65d74213e665fa761777081a440e0fbfbe67ee6195cf7d655cc63c489218bc4f"
review_run_id: "impl-rev-20260827-fable5-01"
native_output_ref: "direct"
reviewer: "claude-fable-5 (Cowork fallback reviewer, 非实现者会话)"
implementer: "grok"
review_date: "2026-08-27"
verdict: CONCERNS
finding_counts: {P0: 0, P1: 4, P2: 3}
dimensions: [spec, correctness, security, tests, overengineering, evidence]
---

# Implementation Review — Athena 9.9.8

按 `review-packet.md` (mode: implementation) 执行。方法：9.9.6↔9.9.8 双端全量 diff（各 20 文件改 + 新增 REVIEW.md/模板）、delivery-gate/pre-bash-guard/continuator/index-updater 逐行、validator 实跑（本机 VM py3.10：**75 PASS / 4 FAIL / 4 SKIP**）、packet/design hash 现场重算、baseline 与 gitignore 实查。注：`reviewed_diff_sha256` 按 REVIEW.md 公式计算，但该公式看不见 untracked 文件（见 F1），故补 `reviewed_tree_sha256` 锚定 271 个实际交付文件。

总评：实现方向和主体质量高——一次异步原生 review、派生 packet 双射校验、critic/evaluator/spec-compliance 三 stub、polish 前移、单引号 parser 修复、版本 pin 黄区处置、validator 回填 9.9.3 检查族，全部落地且与 design rev2 一致。4 个 P1 集中在"diff hash 口径"与"新 gate 逻辑无 runtime fixture"两个面，均可在本 sprint 内修复。

## Findings

### F1 [P1] sourceDiffSha256 看不见 untracked 文件 — review 绑定失效的真实安全洞
- AC: AC5/AC6 · 位置: `claude/9.9.8/.claude/hooks/delivery-gate.cjs` sourceDiffSha256 / `codex/.../delivery-gate.py:908`
- 事实: 公式 = `git rev-parse HEAD` + `git diff HEAD -- . ':(exclude).ai_state'`。**本次交付物（双端 9.9.8 树 + validator）整体是 untracked 新目录，`git diff HEAD` 输出为空** —— hash 只覆盖 tracked 文件修改。
- 反例: review PASS 落盘后，实现者再改任意 untracked 文件（如 delivery-gate.cjs 本身）→ hash 不变 → ship gate 放行未审代码。AC5 的"review 后代码变化必须 block"被击穿。
- 次要（同函数）: hash 绑定 HEAD——内容零变化的纯 commit 也会使 hash 失效并 block（fail-closed，不降安全，但把"代码变更才失效"变成"任何 commit 都失效"）。
- 修: 公式改为 `git add -N`（intent-to-add）后 diff，或 `diff` 输出 + `git ls-files --others --exclude-standard` 逐文件 sha256 拼接；frontmatter 记 `base_commit`，gate 比对 base_commit 起的内容 diff 而非 HEAD 瞬时值。双端同步修。

### F2 [P1] CX 与 CC 的 diff hash 公式不一致 — 双端互认失败
- AC: AC8 · 位置: `codex/9.9.8/.codex/hooks/delivery-gate.py:919`
- 事实: CC `execFileSync(...).trim()` 后拼 `${head}\n${diff}`；CX `head.stdout` **未 strip**，实际拼出 `abc\n\n<diff>`。同一仓库状态两端算出不同 hash。
- 反例: `platforms_enabled: ["both"]`（当前 `_index` 即如此）下，CC 会话完成 review 落盘，CX 会话跑 ship gate → `reviewed_diff_sha256 does not match` → 永久 false block。
- 修: CX 加 `.strip()`；validator 增跨端 parity fixture（同一 fixture 仓库两端各算一次，断言相等）。

### F3 [P1] gate 新核心逻辑零 runtime fixture — packet 明文要求的 fail-closed 用例缺席
- AC: AC2/AC3 · 位置: `scripts/validate-athena-9.9.8.py` check_998_review_contract
- 事实: AC2 要求"fixture 对陈旧 hash、漏/重 AC 必须 fail closed"；设计 AC3 要求"通知丢失"用例。validator 对 delivery-gate 只做 `node --check`/py_compile 语法 + 字符串在场断言。validateReviewPacket / validateReview / sourceDiffSha256 没有任何一条被真实执行过。9.9.6 review 的核心教训（"76 PASS 证明字符串在场，不证明配置跑得起来"）在**新增面**上重演。
- 修: validator 建 temp sprint fixture 驱动 gate 进程五用例：陈旧 design hash → block；packet 漏/多 AC → block；`implementation-review.md` 缺失（通知丢失）→ block；`native_output_ref` 指向不存在路径 → block；diff hash 不匹配 → block。CX 侧同构。
- 备注: continuator 的 await-review-result 与 CX quote fixture 是真实调用，值得肯定；本 finding 只针对 gate 面。

### F4 [P1] 交付状态声明与现场不符 — "validator 87/0/0" 在当前树不可复现
- AC: AC11(evidence 纪律)/AC7 · 位置: `_index.md` status_snippets · `codex/9.9.8/.codex/hooks/__pycache__/`
- 事实: 本机实测 75/4/4。4 FAIL 中三个是环境因素（VM py3.10 无 tomli 子进程、codex 二进制缺失连带），但 **"CX package has no junk" 是环境无关 FAIL**：`.codex/hooks/__pycache__/*.pyc`（含 cpython-314，系实现者自己运行时产生）在 canonical 包内，validator 自己的断言当场打脸。声明 0 SKIP 也与 fixture 依赖外部资源的事实不符。
- 修: 删 `__pycache__`（hook 已含 `sys.dont_write_bytecode` 类防护的应加齐；validator 运行后应重跑确认零污染）；在实现机重跑 validator，把 SUMMARY + 当时树 hash 一并写进 evidence 再声明；`_index` snippet 更正。

### F5 [P2] CC 端 rg quote fixture 缺失 — "双端 fixture" 只做了一端
- AC: AC8 · 位置: validator（只 import 了 CX `pre-bash-guard.py` 做真实调用）
- CC `pre-bash-guard.cjs` 的单引号闭合修复（本次 diff 可见）没有任何执行测试，只有 `node --check`。修: node 一侧加等价 fixture（`node -e` 调用解析函数断言 `rg 'foo$(x)bar'` 不报、裸 `$(x)` 报）。

### F6 [P2] AC9 残余未完成且部分未声明；迁移文档未更新
- AC: AC9/AC10 · 事实: (a) 7 个 telemetry 文件仍在 git index（gitignore 不解除已跟踪，需 `git rm --cached` + 保留本地副本——设计明文步骤）；(b) `.ai_state/.runtime/` 无 gitignore 条目，baseline 目录可被误 commit；(c) `_index` 160B 溢出搬运未实现（已自 declare，OK）；(d) `AI-MIGRATION-GUIDE.md` 与 9.9.6 逐字节相同——passN→implementation-review、critic 删除、telemetry 迁移对存量安装的迁移步骤全部缺失。
- 修: 补 (a)(b)(d)；(c) 保持 declare 并在 ship 前完成。

### F7 [P2] 交付物卫生与自述漂移
- 位置: `scripts/validate-athena-9.9.8.py` docstring 引用不存在的 `REVIEW-9.9.8.md`；自述 "local-only by design" 但 .gitignore 只 ignore 了 9.9.6 系 validator，9.9.8 无对应规则；本次审查在 `scripts/` 遗留 `.vv310.py`（VM 无删除权限，可手动删）。修: docstring 改指 `reviews/implementation-review.md`；按 9.9.6 先例补 ignore 规则。

### F8 [INFO] AC11 eval 未执行（RELEASE 已如实声明 in progress）
- baseline 冻结做了（inventory + sha256，内容可由 git 历史按 hash 回取，可接受）；但代表性任务对照（成功率/控制面 tokens ↓≥40%/占比 ≤1/3）未跑。AC11 在 eval 落盘前不可判 PASS —— 这是 ship 的硬前置，不是本 review 可豁免项。

## MISSING / EXTRA / DEVIATED

| 类 | 项 |
|---|---|
| MISSING | untracked 覆盖的 diff hash（F1）· 跨端 hash parity（F2）· gate runtime fixtures 五用例（F3）· CC quote fixture（F5）· telemetry index 移除 + `.runtime` ignore + 迁移指南（F6）· AC11 eval（F8） |
| EXTRA | CX 包内 `__pycache__/*.pyc`（F4）· `scripts/.vv310.py`（审查遗留，删）· docstring 引用幽灵文件（F7） |
| DEVIATED | CX hash 公式 vs CC（F2）· "87/0/0" 声明 vs 当前树 75/4/4（F4） |

## 核对确认（经得住的部分，一行带过）

design/packet hash 未被实现者改动（现场重算一致，无契约篡改）· 三 stub `disable-model-invocation: true` 双端在场，live emitter 无 critic/evaluator/spec-compliance 调度 · polish→review 顺序、异步里程碑、同因 ×2 终止、`native_output_ref` 契约在 CLAUDE.md/stages/athena-review/REVIEW.md 四处一致 · generator 去 pace、architect 保留（符合 rev2 决策）· critic 标题计数已从 gate 移除 · 版本 pin V1–V3 黄区处置正确（CC 2.1.231 / CX 0.150.0 实测，0.146+ 特性未当唯一路径）· validator 回填 package-parity/F-series/install/runtime 检查族（9.9.6 P1-5 修复）· config.toml 模型默认未动、setup 不覆盖安装（AC10）· orchestration 并发假设已同步 · 无过度工程新增面。

## 处置

F1–F4 修复后目标复核只看：两个 gate 函数的增量 diff + 新增 fixtures + 清理后的 validator SUMMARY evidence + `_index` snippet 更正。F6(a)(b)(d)/F5/F7 随同修复；F8 是 ship 硬前置。按 AC4：若复核再出同因新 P0 ×2 → 交还用户。

VERDICT: CONCERNS
