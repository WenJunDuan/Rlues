---
doc_type: environment-design
target_release: "9.9.9"
created: "2026-09-06"
status: design-proposal
---
# VM / Runtime — 让运行证据独立于模型平台

## 目的与当前事实

VM 是 PACE runtime-verify 的实际执行环境，.ai_state 保存场景、运行结果与可复用范围。CC-only 或 CX-only 都能使用；多平台也能消费同一份有效证据。VM 不运行第二套 PACE，不保存项目真相的唯一副本。
本轮只读观察：~/.athena/vm.json 存在，权限 0600；已注册 dev，key 认证，purpose 为 runtime-verify/e2e/docker，预算 60 分钟。SSH 别名与注册的目标/账号匹配，BatchMode + StrictHostKeyChecking=yes 连接退出 0。
远端报告 Linux x86_64 / Red Hat Enterprise Linux 10.2；docker、python3、node、git 可执行文件存在。未启动或修改任何服务；未验证 Docker daemon、项目依赖、FE/BE/DB、资源限额或 hypervisor 快照。因此当前只能证明配置和传输可用。

## 三种执行环境

| 环境 | 能证明什么 | 不能据此推断什么 |
|---|---|---|
| 模型推理基础设施 | 厂商执行模型推理 | 用户能控制 OS、代码目录、重置状态或读取运行证据 |
| 厂商提供的工具执行环境 | 在该产品明确支持的工具/容器能力内完成执行 | 所有产品都具备 Linux 服务、Docker、SSH 或持久数据库 |
| 用户的 Athena VM | 已授权目标上可控制项目运行准备、测试和工件回传 | 仅 SSH 连通就等于任意项目环境 ready |

依据：[Grok Python 执行](https://docs.x.ai/developers/tools/code-execution)、[Build 本地执行](https://docs.x.ai/build/enterprise)、[Codex 云环境](https://learn.chatgpt.com/docs/environments/cloud-environment)、[Anthropic session/harness/sandbox 分离](https://www.anthropic.com/engineering/managed-agents)。这里描述可观察工具能力，不推测厂商内部“思考是否依靠 VM”。

## 责任划分

- PACE 决定本次需要验证的场景、required/advisory、重试或返工目标，继续拥有唯一阶段状态。
- runtime-env 描述项目 FE/BE/DB 的准备、启动、探活、测试、数据初始化、teardown；与已存在合同兼容。
- athena-vm 解析受管目标、做 doctor、经 SSH 执行已授权验证、回传结果。SSH 别名只标识连接目标。
- .ai_state 的当前 sprint 保存代码/契约/环境引用、命令结果和覆盖缺口；凭证仍留在现有私有配置。
- 当前主 agent 是状态与整合证据的唯一写者。其他平台/agent 返回结果，不并发修改同一索引。

## 可用性分开判断

配置存在、传输可达、场景准备就绪是三种不同事实。建议 doctor 输出带 checked_at 的配置/传输结果；场景 ready 由 runtime-env 的探活和前置检查产生。不要用一个长期 vm_available=true 代替全部判断。
可重建能力快照可以落 .runtime；运行摘要持久化在 runtime-verify.md/evidence.yaml。只有真正需要该环境时重验必要条件，不在每轮会话重复 SSH。
VM advisory 缺失可记录未覆盖，继续已满足的本地验证。design 明确 required 的 OS/native/破坏性场景缺失则该场景不可交付；不能用模型评分或“本机也通过”替代。
Athena 9.9.9 发行自身需要在本机及这台 Linux VM 验证所承诺的 local/SSH 路径；这项发行验证要求不等于所有使用者的所有任务都必须有 VM。

## 一次运行的协议

1. **选择场景**：从 Done Contract 取验收目标与 required/advisory，记录实际 runner；没有 VM 的项目按本地可满足的合同运行。
2. **确定输入**：生成下述唯一输入清单并同步受控工件，远端逐项校验通过才执行；不能只 git pull 默认分支或发送整个工作目录。
3. **准备环境**：读取项目 runtime-env 与锁文件，核对 OS/架构、运行时、依赖和所需服务。仅创建本 run 拥有的目录、测试数据及进程/容器。
4. **执行场景**：运行断言并采集标准输出/错误、退出码和工件。SSH 失败、命令失败、断言失败分别记录，未知结果不能变成成功。
5. **回传证据**：绑定源内容、Done Contract 和非敏感环境摘要；证据保留输出位置/摘要和校验值，普通模型无须手写整套字段。
6. **清理与恢复**：执行 runtime-env teardown，只清理本 run 拥有的资源；超时/中断进入同一清理路径。清理失败保留资源标识与可执行处理项。
7. **继续 PACE**：失败按归因回到对应 impl/design 或环境准备；通过后进入必要清理和独立 review，而非另起 VM 工作流。

这是一份协议与实现目标，不是假定已有 prepare()/execute()/reset() SDK。先复用本机 shell、SSH 和现有脚本，只有具体 Docker 场景需要时调用 Docker。

### 工作树输入清单

发送端在当前 sprint 的运行工件中保存 manifest：基线 commit、受控 diff 校验值、排序后的相对路径/类型/权限/内容 SHA-256（含删除项）、显式允许的未追踪文件，以及 manifest 自身校验值。快照反映工作区最终内容，包含已暂存与未暂存变更；submodule 固定实际版本，未支持的对象明确拒绝。
默认只收集受管代码与显式允许的未追踪文件；ignored 文件、凭证目录、私钥、实际 .env 和命中的秘密内容排除，受跟踪文件也不能豁免。被排除对象若是运行必需输入则阻塞准备，报告路径/原因，不输出或散列秘密值；不声称规则能发现所有未知秘密。
显式检查路径穿越、绝对路径和越出快照根的 symlink；不传 .git 历史、宿主配置或未经筛选的 git bundle。使用已筛选的物化文件/增量，不把秘密放进 diff 或任何待传工件。
远端新建本 run 目录，按 manifest 核对文件集合、类型、权限、删除和内容哈希，拒绝遗漏、额外代码或任一差异。源工作区在打包期间变化则重新生成；接收端通过后将 manifest hash 绑定运行证据，执行前不能悄悄替换输入。
运行所需秘密经既有授权的环境注入途径单独提供，不随代码快照、日志或证据哈希传递。依赖安装和测试生成的运行文件发生在校验后，由 runtime-env 定义；源代码变化使原输入绑定失效。

## “快照与回放”的实际含义

第一版回放单元是代码版本/工作树工件 + runtime-env/锁文件 + 测试数据种子 + 断言 + 结果引用。基础设施支持且已授权时可额外使用容器镜像或 VM 快照；没有对应能力时明确未支持。
项目状态应能在 runner 消失后恢复：证据先回传，环境用配方重建。不要让唯一的设计、代码增量或结果留在临时 VM；不在能力缺失时承诺 bit-for-bit 复现。
同一有效代码/契约/环境上的结果可以由 CC 与 CX 共同消费；只有验证的是平台 hook 本身时，才需要分别执行对应平台路径。

## 验收与故障案例

| 情形 | 期望 |
|---|---|
| 有配置但 SSH 不通 | 标记传输失败；advisory 记录缺口，required 场景停止 |
| SSH 通但 Docker daemon/项目探活失败 | 场景未 ready；不进入 E2E，也不改写成代码测试通过 |
| 工作区存在未提交文件 | 同步和核对包含它们的输入；核对不符不接受结果 |
| ignored/.env、越界路径、远端额外代码 | 拒绝非受控输入；不输出秘密；必需输入被排除则准备失败 |
| 本地代码或 Done Contract 已变化 | 受影响证据失效，执行必要复验 |
| 端口/数据目录被占用 | 按项目约定处理；不修改或删除其他任务资源 |
| SSH 中断/执行超时 | 结果为未知或失败，保留 run 资源标识并处理清理；不无界重试 |
| 同一证据由另一平台接收 | 校验内容与适用范围，复用有效结果，不按厂商重复跑 |
| 用户没有 VM | 无 required VM 场景时本地闭环完整；不强迫配置或购买 |
| 项目明确要求 RHEL 行为 | 在合格 RHEL 环境真实验证；其他 OS 的通过不能替代 |

## 变更落点

两端 athena-vm playbook、athena-runtime-verify、biz-delivery-loop/runtime-env-contract；相应 evidence collector 与 delivery gate 消费必要的输入绑定；validate-athena-9.9.9 的 local/SSH/异常 fixture。
不新增明文凭证、VM 管理后台、自动生产部署或全局 VM 依赖；用户 SSH 和运行权限保持原有配置。本轮只有上述只读观察，实施与项目实跑均待后续授权。
