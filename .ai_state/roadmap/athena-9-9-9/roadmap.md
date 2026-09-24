---
roadmap_slug: athena-9-9-9
created: 2026-09-06
trigger: user_explicit
target_release: "9.9.9"
estimated_total_complexity: L
status: superseded
superseded_by: "../athena-10-1/roadmap.md"
implementation_authorized: false
---
# Roadmap — Athena 9.9.9

## 目标与不变量

所有切片属于同一版本 9.9.9。PACE 与 .ai_state 是核心；CC-only/CX-only 基础闭环、多平台增强；效率、复杂并行、全栈交付三个目标全部覆盖。
本文件组织实施顺序，不复制设计义务。设计真相为 ../../sprints/2026-09-06-athena-9-9-9/design.md；VM 细则在同 sprint 的 vm-design.md。
本轮产出迭代文档，items 均 pending；不把文档完成记为功能完成。各切片实施按 PACE 留下必要验证、独立审查与回滚点。

## 六个可独立验收的切片

| # | slug | 交付内容 | 依赖 | 验收归属 |
|---|---|---|---|---|
| 1 | pace-contract-convergence | Done Contract、polish顺序、roadmap触发、业务一次review、CX语法与退役残留 | 无 | AC3/7 |
| 2 | state-recovery-and-evidence | 索引原子/边界、恢复摘要、输入绑定与证据失效 | 1 | AC4/5/6 |
| 3 | single-platform-and-parallel | 单端完整链、可选多端、写集/整合、能力选择与交接 | 1/2 | AC1/2/5/8/14 |
| 4 | vm-runtime-contract | local/SSH合同、配置/传输/场景分离、回传/teardown/回放 | 2 | AC9/10/14 |
| 5 | fullstack-business-slice | 现有skills贯通真实垂直业务切片，需求到证据 | 3/4 | AC11 |
| 6 | migration-and-behavior-evals | 单/双端迁移回滚、发行一致性、行为比较 | 1/2/3/4/5 | AC12/13/14 |

1 完成后先做 2；3 与 4 在接口明确、写集互斥时可并行；5 做真实整合；6 是完整发行收口。可提前准备 6 的基线与迁移 fixture，避免最后才发现没有对照。
依赖只用现有 items.yaml.blocked_by。主 agent 负责选择当前可执行项，不引入调度器、第二张任务表或平台专属状态。

## 单平台基线与协作增强

- 每个切片都先证明其所属平台独立运行；另一平台的缺失不能触发认证或流程门禁。
- 两端发行分别验收。平台协议/hook 的测试各自跑，应用业务结果按代码/合同/环境有效范围共享。
- 多平台场景是附加验收：一个主写者、明确工件交接、失败能转回可用本端能力、不接受缺失的审查或运行结果。
- Grok 缺失/中断不影响基础发行验收。Grok-only 完整发行不在本轮新增范围。

## VM 与真实试验场

本轮已确认 dev VM 的 SSH 可达与 RHEL10.2/x86_64，不能据此预先把任何项目场景标 ready。切片4实施时验证 Docker/依赖/项目探活及清理合同。
发行自身覆盖本机与注册 VM 的实际承诺能力；普通项目只有 design 声明 required 环境才依赖 VM。没有 VM 的用户仍可在本地满足本地合同。
切片5沿用现有 fullstack-delivery 的试验思路：选一个 Convention Pack/runtime-env 可用的真实业务项目，交付单个 FE/BE/DB/权限闭环。具体功能和项目入口在切片计划时从现场选择，文档阶段不编造运行结果。
开始前按 ../../sprints/2026-09-06-athena-9-9-9/execution-contracts.md 固定仓库/基线、入口、测试角色、种子/清理与四类路径断言；无合格目标时 AC11 阻塞，不用模拟结果替代。

## 发布与回滚

- 以9.9.8为不可变基线；新建9.9.9发行快照；不修改用户当前model/effort/provider/权限偏好。
- 迁移只改受管资产；旧平台选择格式可读；失败撤销本事务；不删除第三方或用户修改过的同名skill。
- 先完成 runtime-verify 与会改代码的 polish，再做一次最终独立 review；修复后只按实际变更定向复核。
- AC1–AC14 的真实结果齐备后更新 architecture 与最终发行状态；不把计划中的命令/测试当证据。

## 评测安排

基线准备从切片1前开始，固定单端模型/effort、任务、代码起点、权限与可控制环境条件；平台原生能力不同的两端分别比较自身旧版与新版。
任务矩阵、固定输入要求、采集来源与发布判定统一引用 ../../sprints/2026-09-06-athena-9-9-9/eval-plan.md；没有完成预注册和对应基线，不允许宣称效率收益。
重点记录达标率、非必要用户往返、重复工作、整合返工和总耗时；官方用量可得就记录，不可得不阻塞。环境失败单独归因，避免把资源差异误认为提示词收益。
删除/缩短规则先在代表任务上做对照；没有质量证据不继续扩大减法。全部切片本轮仍为计划。
