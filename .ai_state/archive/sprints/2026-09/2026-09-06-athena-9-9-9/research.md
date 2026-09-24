---
doc_type: research
target_release: "9.9.9"
created: "2026-09-06"
status: evidence-collected
scope: "PACE + ai_state；单平台基础、多平台增强；真实执行环境"
---
# Research — Athena 9.9.9 harness 迭代

## 已确认的产品约束

- 用户要求版本统一为 9.9.9，三个目标全部进入本版：减少卡顿重复、复杂任务并行交付、全栈业务交付。
- Athena 的核心是 PACE 与 .ai_state。单平台完整运行是基础，多平台利用各自真实能力增强；不能因为没有另一家账号、CLI 或模型而阻塞基本工作。
- 本版正式发行对象仍为 CC / CX。Grok 是本次受邀研究者与可选协作端；不据此宣称已有 Grok-only Athena 发行包。
- 本轮授权研究、迭代文档及独立设计挑战；未授权实现、安装更新或发布。

## 当前代码与安装态事实

| 事实 | 来源 | 对本版的含义 |
|---|---|---|
| 当前两端发行最高 9.9.8，根提示词与安装态一致 | 两端发行目录和根文件字节比较；基线 HEAD aa0ae23 | 冻结旧版，从现行故障出发 |
| CC 2.1.236、CX 0.153.4 | 上轮本机 --version 实测 | 这是安装值，不是官方最新版本宣称 |
| PACE 的 Done Contract 已归 design.md，generator 仍指 checklist.yaml | 两端 agents/generator；pace/references/stages.md | 修复合同消费者，不能只更新根文件 |
| polish 触发仍为 review PASS 后；业务入口仍要求三件套 | polish/SKILL.md；biz-delivery-loop/SKILL.md | 统一 runtime-verify → polish → review |
| roadmap skill 仍按模块数触发 | roadmap/SKILL.md 对 PACE 路由 | 按可独立验收切片拆分；文件数只辅助判断风险 |
| CX stage 文档抄入 isolation: worktree | CX stages.md 对 AGENTS.md 与当前协作工具 | 工具语法只在对应平台说明中维护 |
| 新项目模板仍标 9.9.6；RELEASE 仍写 implementation in progress | pace/templates/_index.md；两端 RELEASE.md | 模板、迁移、发行状态纳入同次校验 |
| 自建 collector 仍在包中、默认 hook 配置未注册 | token-usage-collector.* 与原生 hook 配置 | 清理退役残留，不声称每轮仍在采集 |
| 安装态有同名 Athena skill 重复入口 | 抽查 ~/.agents/skills 与 ~/.codex/skills | 按受管归属迁移，保留用户修改与第三方 |
| VM 已配置且 SSH 可达 | 本轮只读注册核对和 SSH 观察，见 vm-design.md | 上版“无 VM 配置”的描述作废；可达不等于项目场景 ready |

已有全栈基础见 requirements/fullstack-delivery-pack.md：Convention Pack、runtime-env、biz-delivery-loop、quantum-codegen 六种 mode、quantum-data。新贡献应是合同一致、切片整合、真实环境结果与可恢复性；不把已有名称重新包装为新增能力。

## 一手资料与采纳边界

| 一手来源 | 原文支持的事实 | Athena 采用的本地设计判断 |
|---|---|---|
| [Anthropic Managed Agents](https://www.anthropic.com/engineering/managed-agents) | session、harness、执行 sandbox 可以分离；旧模型所需补偿可能随模型演进失效 | PACE / .ai_state / runner 分责；不复制其托管服务或事件基础设施 |
| [Long-running harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | 跨会话增量交付需要可恢复产物与实际功能验证 | 用现有索引、Git 和当前 sprint 形成最短恢复材料 |
| [Long-running app harness](https://www.anthropic.com/engineering/harness-design-long-running-apps) | 独立评估、可验证合同与实际浏览器体验有价值，额外循环也有成本 | 保留一次独立 review，增强业务验收；不照搬固定三角色与多轮评分 |
| [Infrastructure noise](https://www.anthropic.com/engineering/infrastructure-noise) | 环境资源与执行限制会影响agent评测 | 固定并报告可控制环境条件，区分基础设施失败与模型/规则失败 |
| [Agent evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | 应区分过程记录与环境最终状态，并选择合适评估器 | 以实际产物、数据库状态和测试判断完成，模型判断用于适当的定性部分 |
| [Codex environments](https://learn.chatgpt.com/docs/environments/cloud-environment) | 云任务有容器、代码版本、setup、缓存和网络配置 | 只有可满足项目运行合同且能回传证据的环境才算等价 runner |
| [Codex hooks](https://learn.chatgpt.com/docs/hooks) | 异步 hook 不能阻断、批准或改写触发操作；后台完成不自动开启新 turn | 可选提示可异步，红区事实仍同步检查；续接不靠猜测后台通知 |
| [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) | 独立工作适合委派；并行写入有协调成本 | 切片依赖、互斥写集、主 agent 整合责任优先于 agent 数量 |
| [Grok Code Execution](https://docs.x.ai/developers/tools/code-execution) | 提供受限的 Python 执行环境 | 不推断其支持 SSH、Docker daemon、长期 FE/BE/DB 服务 |
| [Grok Build enterprise](https://docs.x.ai/build/enterprise) | Build 的工具执行发生在用户本地环境，模型推理走远端服务 | 区分 CLI 执行位置、托管工具环境与模型推理基础设施 |
| [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model) | 当前指南强调处理冲突指令、自主推进和适量验证 | 调整行为合同，保留用户模型选择，不按厂商名字固定职责 |

上述页面本轮已打开原文。官方滚动文档不等于本机已支持；承重行为必须在实施时对 exact platform/version/入口重验。API 参数与平台特性若未有直接证据，不进入强制执行路径。

## 建议引入的增量

1. **恢复契约**：_index 指向当前目标、Done Contract、代码状态和剩余动作；在中断、交接或重要纠偏时更新现有 session-log，不生成完整会话副本。
2. **证据有效范围**：为既有验证结果绑定代码内容、验收版本和非敏感环境摘要；改变相关条件后使证据失效，避免复用旧绿灯。
3. **能力选择**：先用当前平台完成任务；可用且有益时才委派另一平台。所需可选能力缺失不等于缺少必要交付证据。
4. **可复现 runner**：复用 local + 已有 SSH VM，通过同一 runtime-env 准备、运行、采集、清理；不新增通用执行服务。
5. **整合验收**：任务图复用 items.yaml 的 blocked_by，工件依赖与写集放原 design/派工消息，最终测试在整合后的代码上执行。
6. **垂直业务验收**：把角色、动作、状态变化、权限和审计联为一个可演示切片，报告从同一份 evidence 引用生成。
7. **行为回归与消融**：增加真实任务、故障场景与单/多平台矩阵；删除旧规则前后比较质量与返工，避免只测字符串存在。

## 本版不引入

- 第二工作流、调度守护进程、全量事件溯源数据库、向量记忆库、自建 token telemetry。
- 强制跨平台/跨模型家族评审、固定 best-of-N、多轮 evaluator、全局 VM 必需。
- 通用云 VM 驱动市场、没有 hypervisor API 却宣称可快照、全量共源编译框架。
- 没有真实调用方的配置开关。先完善 PACE 与 state 的现有消费者，再决定是否抽公共实现。

## 独立输入状态

原生只读 architect 已提供 VM/单平台/切片建议；主 agent 将其“VM 未 doctor”描述按本轮 SSH 证据修正，并采纳 configured、transport available、scenario ready 分离。
Grok 1.0.13 / grok-4.6 两次联网研究调用中途 cancelled；第三次基于主agent提供的一手证据摘要返回最终观点（end_turn）。结果与采纳/修正见 grok-research.md；联网原文核验由主agent完成，不冒充Grok已完成搜索。
