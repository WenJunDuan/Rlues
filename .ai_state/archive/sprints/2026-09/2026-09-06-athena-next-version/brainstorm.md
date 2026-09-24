---
doc_type: brainstorm
created: "2026-09-06"
status: superseded
superseded_by: "../2026-09-06-athena-9-9-9/design.md"
baseline_release: "9.9.8"
candidate_releases: ["9.9.9", "9.10.0"]
implementation_authorized: false
goals: ["减少卡顿和重复流程", "提升复杂任务与并行交付", "增强全栈业务交付"]
route: "System / brainstorm；本轮交付调研与方案，实施时进入 roadmap"
route_candidates: "9.9.9 一致性修复 + 9.10 能力升级；暂缓 10.0 平台重写"
---
# Athena 下一版：一致的流程、可靠的并行、完整的业务交付

> 历史提案：用户后续确定全部统一为9.9.9，并以PACE/.ai_state、单平台完整/多平台增强为核心；以下9.10及共源框架建议已由 [9.9.9设计](../2026-09-06-athena-9-9-9/design.md) 取代，保留原文便于追溯。

用户最终要求三个目标全部覆盖。建议 9.9.9 先修一致性，9.10.0 同时建设共源发行、复杂任务协作与全栈业务交付；用行为评测验证速度和质量。这是设计提案，未修改发行包、安装配置或现行门禁。
本机 2026-09-06 实测 CC 2.1.236、CX 0.153.4；这是安装版本，不是官网最新版本声明。两端最高发行目录均为 9.9.8，根提示词与安装态逐字一致；HEAD 为 aa0ae23。索引中的 CC 2.1.231 / CX 0.150.0 是旧实测记录。

## 当前基础与确定问题

| 观察 | 证据（仓库相对路径，均以 9.9.8 为基线） | 影响 |
|---|---|---|
| 根文件较小，外围重复维护较多 | CC CLAUDE.md 3,286 B；CX AGENTS.md 3,876 B；两端各 26 skills；95 个同路径 skill 资源中 56 个字节一致 | 优先处理共享规则与冲突；磁盘字节不等于常驻 token |
| 验收真相源冲突 | CX skills/pace/references/stages.md:38 对 agents/generator.toml:19；CC generator.md:33 同样残留 | PACE 以 design.md 为准，generator 却把可选 checklist.yaml 当唯一依据 |
| polish/review 顺序冲突 | CX stages.md:76、athena-review/SKILL.md:10 对 polish/SKILL.md:3、10 | 可能互相等待，或审查后改代码使结果失效 |
| 平台语法串线 | CX stages.md:45 要求 isolation: worktree；CX 根指令要求主 thread 建 worktree 并交付绝对路径 | 可能尝试当前工具不存在的参数 |
| 分诊规则仍有旧副本 | roadmap/SKILL.md 用模块数触发，PACE 已改为可独立验收的切片数 | 同一个需求可能被两套规则重复拆解或升级 |
| 全栈入口仍触发旧审查 | biz-delivery-loop/SKILL.md 第 13 步写“review 三件套”；PACE 已改一次多维 review | 业务任务会重新带回已退役流程 |
| 模板与发布状态漂移 | CX skills/pace/templates/_index.md:3–4 仍为 9.9.6；两端 RELEASE.md:3 写 implementation in progress | 新项目可能重新载入旧义务 |
| 安装态有重复入口 | 抽查 pace/polish/athena-review/athena-dev 同时位于 ~/.agents/skills 和 ~/.codex/skills，均匹配发行件 | 本会话目录也重复列出；迁移应按 Athena ownership 清理 |
| 退役与异常残留 | token-usage-collector.* 仍分发但当前默认配置未注册；CX delivery-gate.py:908–935 在 git 失败时生成空树哈希 | 前者是维护残留，后者是已知异常状态表达缺陷，不能夸大为普遍绕过 |

现有能力值得保留：PACE + .ai_state、一次独立审查、Done Contract、biz-delivery-loop、quantum-codegen 六种 mode、quantum-data、Convention Pack 和 runtime-env。下一版应把这些接成可靠交付链，避免把已有能力重新命名后当新增。
根因判断：流程正文、skill 描述、agent、模板和 gate 各携带部分合同，升级时没有同步全部消费者。新模型更强的指令遵循会放大矛盾；解决重点是合同一致性、适用范围与完成条件。

## 架构与目录

共同语义只维护一份，原生适配分别维护，项目约定留在项目仓库。复杂任务与全栈交付都是 PACE 的能力，使用同一份状态，不新增调度循环或第二状态机。
```text
vibeCoding/
├── athena/                       # 下一版起唯一手工编辑源码
│   ├── VERSION
│   ├── core/
│   │   ├── instructions.md       # 稳定协作约定，生成两端入口
│   │   ├── pace/
│   │   │   ├── routing.md        # 分诊依据，唯一正文
│   │   │   └── stages.yaml       # 顺序/条件/产物位置，生成 stage 提示
│   │   ├── skills/              # 共享技能正文与 references
│   │   ├── agents/              # 角色职责正文，不混平台工具参数
│   │   └── templates/           # _index、Done Contract、review
│   ├── adapters/
│   │   ├── cc/                  # 原生配置、角色头、hooks、特有说明
│   │   └── cx/                  # 原生配置、角色头、hooks、特有说明
│   ├── packs/
│   │   ├── delivery/            # biz-delivery-loop + quantum-* 及其合同
│   │   └── integrations/        # VM / Antigravity 等按任务启用
│   ├── evals/                   # 人工认可的行为预期 + 真实任务
│   └── build.py                 # 确定性组装、版本、managed-file 清单
├── claude/9.10.0/               # 生成的原生发行快照
├── codex/9.10.0/                # 生成的原生发行快照
└── scripts/                    # 复用现有校验、迁移、回滚测试
```
这些是维护目录，平台不会自动加载 core/ 或 packs/；发布脚本输出原生支持的结构。先共享正文、静态合同和测试案例；保留 CC CJS / CX Python hook 实现，暂不强行统一语言。stages.yaml 只承载有限静态事实，其 Markdown 输出不可再手改；不用通用 DSL 治理提示词。
CC 安装到 ~/.claude；CX 用户 skills 映射到 ~/.agents/skills，配置/agents/hooks 留在 ~/.codex。只迁移受管文件，保留用户覆盖和回滚；发行版本、配置语法和能力探测以当前平台实测为准，不假定官网滚动文档全适用于本机。
项目侧继续使用 docs/ai/convention-pack/、runtime-env 和 .ai_state。_index 只存当前路由与指针；必要 stage 字段在转换时更新，结论集中收尾。requirements/architecture/compound 为耐久层，archive 为冷层，.runtime 为可重建缓存。自动记忆不能覆盖验收与已采纳决策。

## 提示词设计：从流程口号转成行为合同

共同入口建议保留如下语义；具体工具、版本、角色型号、长检查表分别放适配层和按需文档。以下是下一版草案，实施时需联动修改 gate，不能单换根文件。
```text
围绕用户已授权的目标持续推进，并对最终整合结果负责。
合理、可逆的实现选择自行决定；缺少关键输入时先推进独立部分，再提出具体问题。
保留用户最新纠偏，不因旧 skill 或历史记录再次要求已给出的授权。
遵守平台指令和权限边界；本地工作流只在其适用范围内生效。
先读 .ai_state/_index.md，再按指针读取完成当前工作所需的信息。
以统一的 PACE 阶段合同和 Done Contract 判断完成。
按依赖、写入边界和实际收益委派任务；结果必须在整合后验证。
使用适合改动的验证；新增变更、失败或未消除风险才扩大或重复检查。
清理后审查最终代码；真实结果与证据优先于文档数量或 agent 次数。
简洁说明结果、必要证据和未解决限制，不暴露私有推理过程。
```
Skill 统一成“何时用/不用 → 输入 → 最短步骤 → 完成条件 → 失败返回路径”。brainstorm 能形成可观察验收时就结束，删除固定“再问三个”；小文案/机械迁移用结构校验，行为代码与 bug 修复使用适当测试，不伪造 red→green。
根入口负责原则，stage 合同负责义务，agent 只负责本次任务输入/边界/输出，hook 只做确定性判断。明确主 agent 可以完成授权的小改动；复杂任务的委派依据是独立性、上下文与冲突面。此为后续规则变更建议，当前执行仍遵守现行红黄绿区。

## 复杂任务与并行交付：依赖明确，整合负责

复用 roadmap/items.yaml 表达切片依赖，确有缺口时才增加 depends_on 等最小字段。子任务的允许写集、基线、绝对 workdir、输入引用、验收命令与输出合同放现有 design/原生派工消息，不另建任务书或状态账本。
先定义共享 API/数据合同，再让互不冲突的前端、后端或测试任务并行；公共 schema、锁文件与 .ai_state 由指定单一写者处理。只读探索不承担写者门禁；写者保留当前真实 agent_id 绑定与 worktree 约束，绑定窗口串行，已绑定工作并行。
主 agent 负责整合顺序、冲突解决与整合后的测试；各 worktree 单测通过不等于集成交付通过。子 agent 返回改动、验证结果、剩余阻塞；不要把中间搜索日志灌回主上下文。已有角色能承担职责就复用，不为 FE/BE/DB 各新增永久人格。
CC/CX 交接记录当前基线、未提交改动的可访问载体、验收与证据、剩余事项，由接收端重验实际工作树。隔离目录不会自动含有父会话未提交内容，需显式准备任务所需状态，避免“审了另一份代码”。
异步 review 仅适用于真实异步入口；等待不重复派发，主任务保持责任，用当前界面可用的等待/续接能力恢复。Goals、定时与外部事件交给平台已授权机制，不用 Stop hook 无限续跑。

## 全栈业务交付：从六种生成模式走到业务闭环

沿用 biz-delivery-loop 作为 PACE 特化、quantum-codegen 的 page/module/db/unit/security/e2e、quantum-data 的运行期只读能力。Convention Pack 决定项目栈，runtime-env 决定如何启动和验证，统一合同决定什么时候完成。
建议按业务垂直切片交付，例如“员工提交申请 → 审批人通过/驳回 → 列表状态更新 → 审计可核对”。每个切片贯穿页面、API、数据库、权限与测试，能真实演示后再继续下一切片，避免先堆完所有页面再补后端。
流程为：业务规则与角色 → 可运行 UI demo → 冻结接口/错误/权限合同 → DB 与后端 + 前端并行 → FE/BE/DB 联跑 → 正常/拒绝/越权/失败路径验证 → 清理 → 一次独立 review → 交付。UI demo 与前后端并行已有基础，新增重点是合同变更传播、整合验证与切片级验收。
保留用户原先要求的“表设计文档 + DDL SQL”分离输出；在实际涉及数据库迁移时覆盖已有数据兼容、迁移前后验证和回滚边界。验收用代表性测试数据与角色，runtime-env 提供启动、探活、teardown，复用现有脚本。
保留业务侧必要决策 checkpoint。用户已经确认的样式、schema 或发布范围不重复询问；需求改变或新不可逆影响才重新决策。技术检查自动推进，生产发布仍依用户授权。
交付报告按“需求/业务规则 → 相关产物 → 测试/运行证据 → 当前状态/遗留问题”串联。模型与用量只取平台实际可得数据，缺失标 unavailable；复用证据引用生成摘要，不手写多份平行报告。
建议引入“规则变更影响提示”：接口或数据合同变化后，指出受影响的 mock、消费者、权限测试与 E2E，只重验受影响部分；用现有引用/依赖和测试能力实现，不先建知识图谱。

## 版本节奏与验收

| 阶段 | 交付切片 | 可观察验收 |
|---|---|---|
| 9.9.9 | 全链一致性：合同位置、polish 顺序、roadmap、全栈 review、模板、平台语法；处理已知异常和退役残留 | 对本轮确认矛盾有回归；小改动不被可选产物阻塞；关键 gate 仍成立 |
| 9.10 A | 共源与平台适配、可重建发行、受管迁移 | 同源码重建一致；安装无 Athena 重复入口；用户配置保留且可回滚 |
| 9.10 B | 复杂任务依赖、写集边界、整合与跨端恢复 | 双端各完成一个真实多模块任务；并行无覆盖；最终整合通过而非只看子任务绿灯 |
| 9.10 C | 全栈垂直切片与环境验证 | 在真实试验项目交付一个 FE/BE/DB/权限闭环；从需求能找到真实运行证据 |
| 9.10 D | 代表性行为评测并修正默认值 | 三类目标都有评测结果；质量不降，往返/重复工作与总耗时可对比 |

评测先覆盖 12 类：小文案、单点 bug、无 checklist 的 Feature、R/S 顺序、缺原生 review、审查后变化、并行写入、整合冲突、异常工具/失效证据、压缩与跨端恢复、全栈角色/异常流程、安装升级与回滚。静态 fixture 与真实模型任务分开，后者只在执行阶段开展。
比较时固定模型/effort、仓库起点、权限与任务；记录达标率、非必要用户往返、重复计划/审查/测试、整合返工、端到端耗时和可取得的官方用量。先跑代表样本，对有波动的场景再重复；不预先许诺降低百分比，也不以单次结果宣称收益。
保留规则溯源，但把每次真实失败转成有限回归案例；新增规则应有适用条件和删除依据。暂缓新遥测体系、第二调度器、向量记忆库、固定跨模型家族审查与“一律锁死复现测试”的新 hook。确定性安全/交付边界仍检查，异步 hook 仅做不阻断的辅助工作。
下一步实施需要 roadmap；本轮只交付提案。历史 validator 120/0/0 是上版记录，本轮未重跑发行全量验证或付费模型 A/B；上述确定问题来自当前源码和安装抽查。

## 来源与恢复指针

- 本地基础：两端 9.9.8 发行源码；.ai_state/architecture/athena-9.9.8.md；requirements/fullstack-delivery-pack.md；compound/2026-08-27-decision-retire-local-telemetry-collection.md；sprints/2026-08-27-athena-9-9-8/reviews/implementation-review.md。
- [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)：当前 GPT-6 指南提示冲突指令、自主推进、委派和适量验证；采用行为建议，不自动升级模型。
- [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)、[skills](https://learn.chatgpt.com/docs/build-skills)、[subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[hooks](https://learn.chatgpt.com/docs/hooks)：原生加载、独立任务协作与生命周期边界。
- [Claude Code best practices](https://code.claude.com/docs/en/best-practices)、[skills](https://code.claude.com/docs/en/skills)、[subagents](https://code.claude.com/docs/en/sub-agents)、[hooks](https://code.claude.com/docs/en/hooks)：简短入口、按需能力、隔离与事件语义。均于 2026-09-06 查阅，滚动文档需按本机版本验证。
- 索引溢出保留：本轮移出的最旧 route_history 原文为“2026-07-10 System: CC 9.9.1 redesign from CC 9.9.0 baseline, awaiting Fable5 review”；本文件由 latest_brainstorm 指向。
