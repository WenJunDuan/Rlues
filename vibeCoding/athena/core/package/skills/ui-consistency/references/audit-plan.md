# cc-9 第二阶段：全站 UI 一致性检查计划

状态：**计划，未执行运行审查**。2026-10-24 按 links HEAD `6c3810be7cc8c10d05138d279435702cd9b46cfa` 的路由、设置导航及组件文件只读整理。所有页面当前 UI 是否合格均为「待验证」，下表“要查”不是已发现的缺陷。路径以 links 仓根为基准；`src/` 简写指 `apps/web/src/`。

检查 ID 见 [SKILL 清单 C01–C16](../SKILL.md)，优先级见 [rules UI-01–UI-12](../rules.md)。执行者先核对当前路由与导航再检查，设置页键可能来自运行时接口，不能只按文件名判定页面可达。

## 公共场景与证据

| 场景 | 执行方法与通过条件 |
|---|---|
| A 基线 | 每页至少一个正常态；核对 C01–C09、C15、C16。标题唯一、无页面组织表格 / 嵌套卡片、工具栏同职责同顺序、数字等宽、颜色与圆角来自现有角色。 |
| B 容器与长内容 | 同一桌面视口（建议1440×900）切左栏 / 右栏开合；另测窄视口（建议390×844）。读实际 content 宽度，跨该页容器阈值前后各一点，不能只换 viewport 截图。长中文名、长路径和最大字体档下主操作仍可达。记录真实尺寸，建议值不是已测事实。 |
| C 状态 | 对有异步数据的页测首次空、筛选无匹配、加载、失败与恢复；无该能力标不适用并说明。请求中不闪“暂无”，失败不永久加载，空态一个主行动。 |
| D 主题与动效 | 每页看浅 / 深模式；共享控件在玉色等极浅色和较深色下检查前景。每种新增动效测开启 / 关闭；全局开关至少测一次两档 × OS 减少动态开 / 关，结果仅随应用档位。 |
| E 键盘与反馈 | Tab 走完主操作，检查 focus、菜单、弹窗关闭焦点、禁用 / 进行中 / 成功 / 失败；纯图标有名称。编辑 / 发送入口另测中文 IME。危险操作用可控测试数据，不执行真实删除或发消息。 |

每页跑 A、B、E 与适用的 C；D 的共用组件可引用同一份证据，页面自绘控件单独补证据，避免无意义地做全笛卡尔积。会话流、会务三栏、设置弹窗需单独测 D。运行浏览器沿用 links `.claude/rules/project.md` 的 Edge Dev 约定；本阶段没有启动 links。

## 主页面

| 页面 / 入口 | 源码定位 | 特有检查（在公共场景之外） |
|---|---|---|
| 会话：`/chat`、`/chat/$chatId` | `src/routes/_shell/chat*.tsx`；`src/features/chat/`、`src/features/composer/` | C10–C14：新会话 / 历史 / 流式 / 停止 / 失败；长输入与附件、IME、无可用模型；上滚不抢视口、回到最新、末条消息不被输入框遮挡；会话四档宽度随侧栏收缩。 |
| 全部会话：`/sessions` | `src/routes/_shell/sessions.tsx`；侧栏见 `src/components/layout/` | 搜索无匹配、历史为空、长标题截断可还原；选中与 hover 可区分，键盘可到行尾菜单，日期 / 计数 tabular-nums；收起仍有双向开关。 |
| 技能目录：`/skills` | `src/features/catalog/skills/index.tsx`、`yours-list.tsx`、`discover-grid.tsx` | 我的 / 发现、搜索 / 厂商筛选、布局切换、安装中 / 失败 / 已安装；顶栏与 PageHeader 标题去重；无表格组织与空态虚线框；视图状态切换不丢筛选。作为工具栏对齐基准，先审再复用。 |
| 技能详情 / 新建 / 编辑：`/skills/$name`、`/skills/new`、`/skills/$name/edit` | `src/routes/_shell/skills_*.tsx` 指向的 catalog 页面 | 返回与页面名不重复、Markdown 内容与元数据层次分明；长技能名；保存失败保留文本；读写权限、安装 / 更新反馈；内容里的代码 / 表格保持局部滚动与语义。 |
| 伙伴目录 / 详情 / 新建 / 编辑：`/partners` 及其子页 | `src/routes/_shell/partners*.tsx`；`src/features/catalog/` | 工具栏对齐技能页；头像、名称、状态、动作的顺序和密度；无伙伴 / 无匹配 / 受限；配置长文本、保存 / 测试反馈，不为每个字段套卡片。 |
| 连接目录 / 详情 / 新建：`/connections` 及其子页 | `src/routes/_shell/connections*.tsx`；`src/features/catalog/` | 未配置 / 连接中 / 已连接 / 错误可辨；测试失败原因与恢复入口；长地址、密钥遮罩、禁用态；断开动作危险变体；不把凭据带入截图。 |
| 定时任务列表：`/schedules` | `src/features/schedules/list/index.tsx` | 启用 / 停用 / 正在运行，下一次时间、时区和计数不抖动；列表 / 筛选 / 空态及新增入口；不用多层边框表达状态。 |
| 定时任务详情 / 运行记录：`/schedules/$scheduleId`、`/schedules/runs/$runId` | `src/routes/_shell/schedules_*.tsx`；`src/features/schedules/detail/index.tsx` | 时间配置、保存结果、历史运行成功 / 失败 / 进行中；长输出、日志局部滚动、返回路径；重试与主按钮不歧义，执行中不可重复触发。 |
| 知识库总览：`/kb` | `src/features/knowledge/index.tsx`、`layout/index.tsx`、`layout/pending.tsx` | 文件树 / 列表 / 右侧内容按容器适配；库为空与无权限不同；总数 / 容量等宽；请求中骨架不误报空。 |
| 知识库详情：`/kb/$kbId`；旧授权入口 `/kb/access` | `src/features/knowledge/detail/index.tsx`、`components/kb-tree.tsx`；`src/routes/_shell/kb.access.tsx` | 上传 / 索引 / 失败 / 重试 / 待授权；长文件名与面包屑；预览局部滚动、空目录、移动 / 重命名焦点。旧入口源码是重定向，应审实际落地页，不凭空造独立页面。 |
| Mesh Link：`/mesh-link` | `src/features/connect/index.tsx`、`detail.tsx`、`thread.tsx`、`channel-dialog.tsx` | 通道 / 设备 / 线程的当前项与状态；无通道、离线、连接失败、重连；长设备名、地址及复制反馈；主从栏宽度随侧栏变化，发送行为只用受控数据。 |

## 设置各页

来源：`src/features/settings/nav.ts` 的 `SET_NAV`，`components/settings-dialog.tsx` 的分派和 `src/features/admin/nav.ts`。设置为弹窗内页面，不虚构 `/settings/*` 路由。公共检查：弹窗唯一标题、左导航 / 右正文滚动不互困、`SettingsSection` / `SettingsRow` 对齐、控件 label 关联；小视口与最大字体仍能保存和关闭。

以下组件路径均相对 `src/features/settings/components/`。

| 页名 / 页键 | 定位 | 特有检查 |
|---|---|---|
| 账号 `account` | `account-page.tsx`、`account-login-methods.tsx` | 头像与身份层次、登录方式列表、修改密码 / 头像弹窗、只读 / 保存 / 失败反馈；凭据与个人信息脱敏。 |
| 用量 `usage` | `usage-page.tsx`、`usage-kpis.tsx`、`usage-trends.tsx`、`usage-sessions.tsx` | 指标、金额、token、时间 tabular-nums；筛选和单位一致；零用量 / 加载 / 错误区分；图表色有文字说明；现有表格替代时保留比较和排序能力。 |
| 通用 `general` | `settings-dialog.tsx` 的 `SettingsRowsPage` + 设置数据 | 标签与控件关联，长说明不挤控件；本地 / 受管理设置不可混淆；保存中 / 失败与实际设置一致。 |
| 个性化 `assistant` | `assistant-page.tsx` | 长输入、偏好开关、保存失败保留草稿；说明只解释真实影响，去重复介绍。 |
| 快捷键 `shortcuts` | `SettingsRowsPage` / `RowControl` | 键帽对齐、长组合键、焦点与捕获状态；快捷键不可因表格改列表丢失名称对应关系。 |
| 模型与内核 `model` | `model-page.tsx`、`providers-section.tsx`、`model-row.tsx`、`harness-sheet.tsx` | 提供商与模型分组、添加 / 测试 / 不可用状态；字段过长；默认模型与配置入口可辨；原 model-table / 多层卡片列为 C03 检查点；内核 sheet 与重启确认焦点。 |
| 记忆 `memory` | `memory-page.tsx`、`memory-graph.tsx` | 空记忆、列表 / 图、搜索与删除反馈；图不以颜色单独表达关系，关闭动效可读；图区域不撑宽弹窗。 |
| 知识库与向量 `knowledge` | `knowledge-page.tsx`、`knowledge-embedding-section.tsx`、`knowledge-index-section.tsx` | 模型选择、未配置、索引中 / 错误、重建动作；进度静态可辨，危险操作保留影响说明；与 `/kb` 业务浏览区别清晰。 |
| 回顾 `reflect` | `reflect-page.tsx` | 空历史 / 进行中 / 失败，周期与时间展示，触发操作防重；折叠内容关闭动效后仍可见。 |
| 工作空间 `workspace` | `workspace-page.tsx`、`workspace-switch.tsx`、`local-folder-usage-section.tsx` | 长路径 / 名称、容量、工作区切换 / 不可用；本地目录与云存储分组，切换过程状态明确。 |
| 扩展与插件 `ext` | `ext-page.tsx`、`tool-plugins-tab.tsx`、`mcp-tab.tsx`、`skill-catalog-page.tsx` | 各页签加载 / 无匹配 / 安装 / 升级 / 失败；权限裁剪后导航一致；技能目录旧页键归到技能页签，不审不存在的独立设置页；详情不重复套框。 |
| 伙伴与连接 `partners-connections` | `partners-connections-page.tsx` | 部署管理可见性、受限状态和深链回落；与目录页复用同一状态词和操作顺序。 |
| Computer Use `computer` | `computer-use-page.tsx`、`desktop-dependencies-section.tsx` | 依赖未就绪 / 可用 / 失败，设备与权限说明；动作有实际反馈，技术细节只在帮助决策时出现。 |
| Browser Use `browser` | `agent-use-pages.tsx` | 浏览器连接 / 断开 / 未安装 / 错误，状态与主动作清晰；长名称与路径不撑布局。 |
| 安全与权限 `security` | `security-page.tsx` | 开关说明不可省掉后果；受管理禁用态、申请与保存结果、权限不足；危险入口用正确变体。 |
| 归档会话 `archive` | `archive-page.tsx` | 空归档 / 搜索无匹配、长标题、恢复与删除反馈；日期等宽，菜单不误触行导航。 |
| 数据管理 `data` | `data-page.tsx` | 导入 / 导出 / 备份 / 清理的可用与进行中状态；进度、文件大小等宽；失败可恢复，确认提示保留作用范围。 |
| 主题（独立弹窗） | `theme-dialog.tsx` | 24色明暗前景、字体档 / 会话宽度、选中色卡 focus；动效只两档，CSS / JS 同步；不受 OS 减少动态影响，刷新后不闪回旧档。 |
| 账号子弹窗 / 扩展配置 | `password-dialog.tsx`、`avatar-dialog.tsx`、`mcp-key-dialog.tsx`、`ext-detail.tsx` | 统一标题 / 主次动作；校验就地显示，关闭后焦点回触发器；敏感字段不进截图；嵌套弹窗无键盘陷阱。 |

管理页同属设置，按实际部署权限进入，不通过提权来获得截图：

| 页名 / 页键 | 定位 | 特有检查 |
|---|---|---|
| 单位 `admin-units` | `src/features/admin/`（由 AdminBody 分派） | 层级缩进、长单位名、导入结果与字段错误；改列表后仍能看出父子关系。 |
| 用户 `admin-users` | 同上 | 名称 / 角色 / 状态层次，筛选、选择、导入 / 编辑反馈；禁止截图暴露真实人员信息。 |
| 角色 `admin-roles` | 同上 | 角色详情、权限组、只读 / 编辑差异；无多层框，不仅以颜色表达勾选。 |
| 统一分配 `admin-assign` | 同上 | 选择人数等宽、分配对象与后果可见；批量操作保持确认 / 失败恢复；去表格不丢选择上下文。 |
| 审计 `admin-audit` | 同上 | 时间 / 主体 / 动作 / 资源可扫读，长字段有展开；筛选、分页、导出反馈保留，敏感记录脱敏。 |

## 会务

来源：`src/routes/_shell/meetings.index.tsx`、`meetings.$meetingId.tsx`，实现 `src/plugins/meeting/`；也可能经场景进入。`MeetingPage` 当前为 fill 形态且自带会务顶栏，不能硬套普通 flow 页宽或再加正文 PageHeader。读取时另有会务 sprint 文档改动，执行前重新确认当前实现。

| 页面 / 状态入口 | 定位 | 特有检查 |
|---|---|---|
| 会务首页 / 会议列表 `/meetings` | `list-page.tsx`、`meetings-tab.tsx`、`app.tsx` | 会议状态、日期 / 场次、筛选、空列表和新建入口；独立顶栏与壳层标题不重复；记录条目不做表格套卡片。 |
| 新建会议 | `new-meeting.tsx` | 字段分组、日期时间、人员选择、校验 / 保存；小容器动作可达，失败保留输入。 |
| 会前准备 `/meetings/$meetingId` 默认入口 | `detail-page.tsx`、`prep.tsx`、`add-topic.tsx` | 议题、参会人、材料、状态及动作顺序；名称长 / 无议题 / 无材料 / 受限；分组间距和上传反馈；进入会中不会重复提交。 |
| 议题详情 / 材料 | `topic-detail.tsx` | 正文与辅助栏按实宽重排；长文、预览、状态提示、返回路径；材料用局部滚动，正文无多层边框。 |
| 会中 | `live.tsx`、`live-layout.ts`、`live-doc.tsx`、`live-dialogs.tsx` | 议程 / 主内容 / 秘书栏的两栏三栏阈值按 content 测；计时数字、活动议题、输入 / 记录 / 生成状态；关闭动效不丢反馈；不因流式更新抢滚动或遮住主操作。 |
| 会后 / 结果入口 | `app.tsx` 的实际分派，具体状态入口待运行确认 | 核对是否存在独立会后视图；有则查结果 / 纪要 / 导出 / 待办，没有则登记实际归属，不能凭空补功能。 |
| 插件停用 / 无效会议 ID | `meeting-page.tsx`、`detail-page.tsx`、`app.tsx` | 停用态可读且无重复壳层；源码注释称无效ID回首页，运行核对实际回落 / 提示与返回入口。 |
| 会务设置 | `settings.tsx`（经插件配置进入） | 同设置分组规范；配置状态、禁用和保存反馈，少文字但不丢作用范围。 |

## 全站覆盖补充

为避免把“全站”缩成上述页面，再核对 `src/routes/` 的这些入口；本阶段只计划，不扩大成重设计任务：

| 页面组 | 入口 / 定位 | 要查 |
|---|---|---|
| 工作台 / 项目 | `/`、`/projects`、`/projects/$projectId` | 首页问候不当重复页面标题；项目视图、工具栏、空态、列表 / 网格密度与数字；详情各页签同一正文边界。 |
| 场景 | `/scenes`、新建、`$sceneId` 详情 / 编辑、stage 新建 / 详情 / 编辑、instance 及 step 页面（对应 `src/routes/_shell/scenes*.tsx`） | 顶栏 PIN 与面包屑关系、返回链、每级唯一标题、表单、运行进度、长输出与失败状态；不重复壳层。 |
| 插件动态页面 | `/p/$packId/$` | 加载 / 停用 / 不可达，宿主与插件的字体 / 令牌 / 滚动一致；只审本次可达插件页面并列清单，不假设所有插件都已覆盖。 |
| 登录 / 首次配置 / 授权 | `/login`、`/setup`、`/license`、`/oauth/callback` | 独立页面唯一标题；输入、校验、忙碌 / 错误 / 返回；不为符合顶栏规则凭空添加壳层。 |
| 错误 / 未匹配路径 | 401 / 403 / 404 / 500 / 503 与 `_shell/$.tsx` | 号码 tabular-nums；一条原因 + 恢复入口、无多层卡片；无权限不冒充空数据。 |

## 顺序、登记与完成判据

1. 先查公共壳层、令牌、标题与工具栏，拿技能目录做已验证样例；公共组件问题只登记一次，关联受影响页面。
2. 查会话 / 目录 / 定时任务 / 知识库 / Mesh Link，再逐个设置页与会务，最后核对补充路由。优先处理 rules P0，其次 P1 / P2。
3. 每项记录：`页面/页键 | 状态 | C-ID / UI-ID | 优先级 | 实际/期望 | 文件:行 | 复现步骤 | 截图或日志 | 修复组件 | 复验结果`。状态仅「通过 / 违例 / 不适用（理由） / 待验证（缺什么）」；不能用“看起来不错”结项。
4. 页面签收需要公共场景证据及表中适用特有行为证据；未取得数据 / 权限 / 环境的项保留待验证，不计通过。改公共组件后复验关联页面，不在每页重复实现。
5. 产品修改在后续授权范围内进行，按改动选择 links 已有 guard / 组件 / 运行测试；截图证明视觉，交互记录证明行为，不能互相替代。第一阶段仅运行 plugins 的 `node --test tests/`，不以其成功宣称 links 全站合格。
