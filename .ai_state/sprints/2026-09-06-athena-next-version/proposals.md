# Proposals — 2026-09-06
- 触发：用户纠偏“你展示的三个选项都需要”。
- 提案：本次下一版设计同时覆盖流程效率、复杂任务并行、全栈业务交付；优先项不等于排除项。
- 处理：brainstorm.md 已调整为三条主线，后两条不再仅列可选扩展。
- 状态：范围已确认；架构和实现计划仍为提案，未修改现行规则。

## 状态档案减脂（2026-09-20 用户纠偏，纳入下版本；用户称 10.1.0，即本档规划的 9.10.0）

症状（切片 3/4 实测）：session-log 叙事化膨胀（单切片 20+ 条长段）；review 三重存储（_native receipt + 转录 md + session-log 标记行）；每次 stage 转换一个 chore(state) commit；诊断样本（如 pre-bash-guard 误拦）在 session-log 与 roadmap 两处重复。

候选机制（下版本设计时裁量，本版不动门禁）：
1. session-log 电报体硬预算：机器标记行之外每事件 ≤1 行，超预算 spill 到 sprint overflow。
2. review 存储单源：只存原生 receipt + 哈希；implementation-review.md 按需由 accept 生成，不三处重复。
3. ship 收口自动归档：完成 sprint 即移 archive/（9.9.8 机制默认化），热层只留当前 sprint。
4. 记账提交合并：stage 转换不单独 commit，随下一实质提交或收口一次落。
5. 诊断样本只进 roadmap 条目 notes，session-log 只留一行指针。

## 新坑七条内化（2026-09-22 quantum-agent 第七会话，纳入 10.1 提示词迭代）

来源：quantum-agent 第七会话（缺陷清尾专场四片 ship，commit c210103f）现场踩坑，逐条「坑 → 提案」。本版不动门禁，候选机制下版本设计时裁量。

1. 路由简报漏 path 字段
   - 坑：两片 Bugfix 派工漏改 `_index.path`，残留上一片的 System；Stop 时撞 R/S polish 门禁，现场 sed 补救。
   - 提案：路由简报模板把 path 列为必填字段（无默认继承）；spec-gate 与 Stop 侧加校验——`_index.path` 与当前 sprint slug 前缀一致性比对，失配即点名 block，不靠人工记得改。

2. 外部写者 Bugfix 接回缺 issue 三件套
   - 坑：grok 外部写者接回的 Bugfix 缺 fix-note，ship 门禁现场才抓到，返工补档。
   - 提案：外部写者接回简报模板（grok-exec / codex 派工节）加必填清单——Bugfix 路径必带 report / analyze / fix-note 三件套路径，接回前自检，不留给 ship 门禁兜底。

3. packet 验收节标题只认五个字面
   - 坑：packet 验收节写了花式标题，prepare 直接拒，报错未说明合法集合，靠试错定位。
   - 提案：合法标题白名单（`## 验收标准` / `## AC` 等五个字面）写进 packet 模板注释；prepare 拒绝时错误信息列出全部合法字面，一次报清。

4. pre-bash-guard 误拦跨仓 push
   - 坑：主仓 stage=impl 时 guard 连 Rlues 仓的 push 都拦，只能等主仓 ship 窗口才推成（quantum-agent 侧 proposals.md 已登同条）。
   - 提案：guard 按 push 目标仓路径判定——仅当 push 目标是当前项目仓时才受 stage 约束；跨仓（提示词源仓等）放行。

5. cat alias heredoc 静默写出 0 字节
   - 坑：同会话三次实害——`cat > file <<'EOF'` 被 alias 劫持，静默产出 0 字节文件，无报错。
   - 提案：写文件规范条目改为 `tee` 或 `command cat`，禁裸 `cat` heredoc；可并入 heredoc-aware-shell-guard sprint 的检测面统一拦。

6. compose 缺省 tag 已删
   - 坑：compose 文件删掉镜像缺省 tag 后，VM 手跑 compose 忘带 `QUANTUM_AGENT_IMAGE` 即起错镜像。
   - 提案：athena-vm skill 操作规程补一行「compose 操作必显式传镜像变量」。通用教训归项目侧规程模板：删缺省值必须同步所有调用点文档。

7. ship 收口子 agent 署名按子会话模型落
   - 坑：ship 收口由子 agent 执行，commit c210103f 落了子会话模型的 attribution 行，与主会话署名不一致；已推送不改。
   - 提案：派工模板固定句「commit 署名按你会话的 attribution 规则写」，明示主/子会话各自按自己的规则落，避免冲突与事后返工。

## 第八～第十会话沉淀内化（2026-09-23 盘点，待用户周末更新）

来源：quantum-agent 第八～第十会话（2026-09-22/23）handoff「本会话新坑」段 + 项目 `.ai_state/proposals.md` 2026-09-21/22 六条。已同步不重列：post-review allowlist 补 roadmap（b1a9513）、ship 期 Write 只拦仓库内（2d6f65a）、validateEvidence 缺件点名（289fddb）；跨仓 push 与 `cat` heredoc 已在上节七坑 #4/#5。级别：门禁修复 4 · 提示词措辞 8 · 技能简报 5 · 只记 4。

| # | 来源（会话/proposals 行） | 现象一句 | 建议落点（文件:节） | 建议改法一句 | 级别 |
|---|---|---|---|---|---|
| 1 | S10 坑①；memory feedback-parallel-writers-worktree-only | bind 报 `review input changed: source_sha256`，聚合摘要无逐文件归因，首轮 reviewer 白跑 | `pace/scripts/review-binding.cjs`:bind；`gate-contracts.md`:review 行 | prepare 同时存逐文件 sha 清单，bind 拒绝时点名漂移文件与预期/实际 sha | 门禁修复 |
| 2 | S10 坑①（同因） | 文档 agent 在主仓工作树改 README/deploy，恰在 prepare→accept 窗口内，bind 恒拒 | `stages.md`:impl 黄区/红区条款 + review 节；`orchestration.md`:原生机制表 + worktree 节 | 黄区「worktree 可选」加限定：有 review 窗口在飞或存在任一并行写者（含纯文档）即强制 worktree；review 节加「窗口内主仓源文件冻结」 | 提示词措辞 |
| 3 | S10 坑②；关联上节七坑 #2 | Bugfix 片 ship 才被 delivery-gate 拦 `fix-note.md` 缺失，Stop 后补档 | `athena-dev/SKILL.md`:分诊表 Bugfix 行；`athena-issue/SKILL.md`:触发描述 | 分诊落 Bugfix 时同步输出三件套路径（report/analyze/fix-note）并把 fix-note 列为 ship 前自检项，不留门禁兜底 | 提示词措辞 |
| 4 | S10 坑⑧；quantum be40d493 用户纠偏 | grok 把 tdd-evidence.yaml 写到仓库根，接回后才归位 | `grok-exec/SKILL.md`:步骤 2 简报内容 + 步骤 5 收尾 | 简报模板加固定行「tdd-evidence.yaml 只写 `.ai_state/sprints/<slug>/`」；cherry-pick 前 `git show --stat` 核路径 | 技能简报 |
| 5 | S10 坑③ | grok-4.7 Build 余额 402 耗尽，施工中途停，stopReason 非 end_turn | `grok-exec/SKILL.md`:已知坑 | 加条目：日志见 402 即停派、不重试；worktree 与简报原地留给内部 generator 接手续做，产物仍按外部写者接回 | 技能简报 |
| 6 | S10 grok 模型核对 | 模型名靠人记，升版时易沿用过期硬编码 | `grok-exec/SKILL.md`:模型单一维护点行 | 核名命令改为 `grok models` 列表（现写 `grok --help`），升版先跑一次再改行 | 技能简报 |
| 7 | S9 坑④ | `--output-format json` 是多行 JSON，直接 parse 失败 | `grok-exec/SKILL.md`:步骤 4 轮询 | 明写「解析取最后一个顶层对象」并给一行 node/jq 取法 | 技能简报 |
| 8 | S10 坑⑤ | 外部写者先 cherry-pick 后建 sprint，evidence 记到旧 sprint；补档 push 把未审代码一并推上 | `grok-exec/SKILL.md`:步骤 5；`stages.md`:ship「推送与小改动」 | 接回顺序固定：建 sprint + 切 `_index` → cherry-pick → 复跑入账；ship 节加「补档 push 前核 main 无未审 cherry-pick」 | 技能简报 |
| 9 | S10 坑④ | 派 Agent 带 `model:` 覆盖，Fable 扫描误成 Opus 重派 | `orchestration.md`:原生机制表下派工条款 | 派工不带 `model:`（用户点名模型时除外），沿用会话默认 | 提示词措辞 |
| 10 | S10 坑⑥ | reviewer 自拟 run id / yaml frontmatter / `Reviewed …` 三行，accept 前须剥 | `agents/reviewer.md`:输出模板（:44 `review_run_id: "<uuid>"`）；`athena-review/SKILL.md`:落盘节 | 模板删 run id 占位，明写「run id/frontmatter/Reviewed 行由 accept 生成，reviewer 只回 verdict+findings 正文」 | 提示词措辞 |
| 11 | S8 坑② | dispatch receipt 写了 `09:XXZ` 占位时戳 | `athena-review/SKILL.md`:receipt 段；`execution-contracts.md`:CC 审查 CLI | 加一句「不确定时戳宁省略字段，禁占位值」（时戳伪造属历史红线） | 提示词措辞 |
| 12 | S8 坑⑤ | accept 已自动落盘 `reviews/implementation-review.md`，SKILL 仍写「转录」 | `athena-review/SKILL.md`:42 | 措辞改「accept 自动生成，主 agent 不手转录、不改定级」，receipt 用 Agent 返回 agentId 绑定 | 提示词措辞 |
| 13 | quantum proposals 2026-09-22「design_changed_after_impl」 | Quick 同轮 design+impl，design 首次落盘被判「impl 后改设计」，两会话各误拦一次 | `hooks/delivery-gate.cjs` + `delivery-gate.py` | 基线 commit 处 `git cat-file -e` 不存在的 design 视为新增免判；仅基线已有且 sha 变化才 block | 门禁修复 |
| 14 | quantum proposals 2026-09-22「features_count 误计」 | 零 Feature 批次 `counts.features_count` 自动 +1，committed 已 20 | `hooks/index-updater`:counts 计算 | 只对 sprint `path=Feature` 计入；或改名 `sprints_count` 名实相符 | 门禁修复 |
| 15 | quantum proposals 2026-09-21「承诺闭合校验」（用户已裁定） | design 写集含编辑 `vm-pending.md` 被当承诺登账，L0 片被迫落空行 | `hooks/delivery-gate.cjs`:承诺闭合校验 | 句式收窄（`→ 记 vm-pending`/`转台账`/`登台账`）+ `path=Quick` 且写集已含 vm-pending.md 豁免，并用 | 门禁修复 |
| 16 | quantum proposals 2026-09-21「转录类事实断言」（用户已点头） | VM 观察/外部写者自述未核原件直进 design/部署文档，两条真 P1 到第三轮才抓 | `stages.md`:design 义务；`review-packet` 模板 + `review-binding.cjs`:prepare（可选硬校验）；reviewer 简报 | 转录断言行内带 `[核:<file:line> 或 commit 或 实测命令]`；packet 加 `transcribed_claims` 节，reviewer 至少抽查 1 条 | 提示词措辞 |
| 17 | S9 坑⑤ | 记账 agent 若先切 stage=ship 再写别的文件，门禁按 ship 合同拦后续写入 | `stages.md`:ship 节首行 | 加「记账顺序：`_index.stage` 切 ship 必须是本轮最后一次写入」 | 提示词措辞 |
| 18 | S9 坑③；gate-contracts ship·evidence 行 | `npm test … \| tail` 无 pipefail 被采集器记 unknown | — | 已生效（gate-contracts 已写 `set -o pipefail`）；ship 前裸跑 `npm test`/`npm run typecheck` 自动记 pass | 只记 |
| 19 | S8 坑①；S9 坑②；上节七坑 #3 | packet 验收节标题白名单、frontmatter `source_design_sha256` 返修后重绑、AC 行首锚定 | — | 已生效并在 gate-contracts 列全，无需再改 | 只记 |
| 20 | S9 坑①；S10 坑⑦ | 本 shell `cat` alias 到不存在的 `bat`；macOS 无 `timeout` | 派工简报口径 / compound | 读文件用 Read 或 `/bin/cat`；护栏超时用 `perl -e alarm` 或 `gtimeout`，简报别写裸 `timeout` | 只记 |
| 21 | S8 坑③ features_count 复核 | index-updater 自动改 counts/pointers 与主 agent 手工编辑 `_index.md` 并存，偏移沉进基线难溯 | `state-contract.md`:`_index` 归属说明 | 注明哪些键只由 index-updater 写、哪些只手改；对账时以 sprint 元数据重算 | 只记 |

优先级建议：
1. 先修门禁点名文件（#1）与两条恒误报（#13/#15），同批带 #14 计数——都是 fail-closed 门禁误伤，每次现场复位都在消耗信任。
2. 再改 grok-exec 简报模板（#4/#5/#6/#7/#8）一次落齐，外部写者接回链才不靠人记。
3. 措辞类（#2/#3/#9/#10/#11/#12/#16/#17）周末批量，一次改 stages/orchestration/athena-review/reviewer 四处；只记类（#18–#21）不动文件。
