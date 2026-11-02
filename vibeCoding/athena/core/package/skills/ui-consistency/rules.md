# quantum-links UI 一致性规则（已定稿）

UI-01–UI-12 已于 2026-10-28 定稿（UI-13 / UI-14 于 2026-10-31 补入）到 quantum-links `.claude/rules/ui-links.md`（项目内路径：`<quantum-links>/.claude/rules/ui-links.md`）。links 规则为现行权威；以下保留规则来源快照，不新建门禁。

参考分层（11-02）：本文件 UI-01..UI-14 最先；会话 / agent 交互行为再看 [open-claude-ui](references/open-claude-ui.md)；布局与视觉（间距、层级、材质、字体、元素）再看 [Apple design](references/apple-design.md)。UI-09 的滚动参考链接已换到 `2d56ab41`（该文件与 `c1f923ae` 逐字相同）。

适用：links 前端页面及其公共 UI。下面路径均相对 links 仓根。来源「用户 cc-9」指 2026-10-23 / 10-24 要求，由本次任务原文提供。P0 为主题 / 可操作性合同，P1 为页面一致性，P2 为细节；分级是本草案建议，不能将 P1/P2 当成可忽略项。旧页面命中时登记到第二阶段审查，不声称已修复。

## P0：合同与可操作性

- **UI-01：颜色消费语义令牌；不引入第二套主题。** 页面不得新增固定 hex、复制 `--cds-*` 或覆盖 `--ql-*` 来模仿外站。主按钮用 `Button`；accent-fill、accent-700、accent-900 分别配自己的 foreground。字族 / 字号 / 间距沿用结构令牌；明暗与极浅主题色下文字、图标保持可辨。
  来由：用户 cc-9；`.ai_state/decisions/2026-10-12-decision-theme-system.md`（含 10-13 前景修订）、`apps/web/src/themes/types.ts`、`apps/web/src/styles/index.css`、`apps/web/src/components/ui/button.tsx`。删除条件：新的主题 ADR 明确替代 L0/L1/L2 契约及前景配对方案。
- **UI-02：正文适配量 content 容器，不量 viewport。** 复用 `Page` / `ContentColumn`，不使用 `lg:` / `xl:` 决定正文宽度或多列能否放下；验收必须包含同视口侧栏开合。壳层、弹窗安全区、移动输入字号按其真实判据处理，不一刀禁用所有媒体查询。
  来由：`.claude/rules/project.md`「会话/布局宽度」「收起的侧栏占 1px」；`apps/web/src/components/patterns/page.tsx` 与 `apps/web/src/styles/index.css` 的容器令牌。删除条件：正文宽度不再受面板影响，且新布局契约有运行证据并替换原项目规则；否则保留。
- **UI-03：动效仅开启 / 关闭，不跟随系统。** 使用 `motion-safe` / `motion-reduce` 与 `useReducedMotion` / `reducedMotion`；禁止新增 `prefers-reduced-motion` 分支或第三档。界面“关闭”对应存储“减少”、DOM `data-motion="reduce"`，关闭后 CSS 动画 / 过渡、JS 平滑滚动都停止，业务流式数据继续。
  来由：用户 cc-9；`apps/web/src/config/theme.ts`、`apps/web/src/lib/hooks/use-reduced-motion.ts`、`apps/web/src/styles/index.css`。删除条件：用户明确更改动效策略，且存储迁移、首帧与 CSS / JS 一起更新并验证。
- **UI-04：精简外观不能删掉操作反馈和键盘路径。** 图标按钮有名称，focus-visible 可见；输入法确认不发送；浮层关闭恢复焦点；请求失败保留输入与重试路径；关闭动效仍显示状态。使用现有 shadcn / Radix 包装，不以静态 div 模拟可交互控件。
  来由：用户 cc-9 的 Apple design 方向；[Apple Layout](https://developer.apple.com/design/human-interface-guidelines/layout)、[Apple Motion](https://developer.apple.com/design/human-interface-guidelines/motion)；`apps/web/src/components/ui/`、`apps/web/src/features/composer/keys.ts`。删除条件：本条由覆盖同等行为的统一可访问性 / 交互规则替代；不能因“更极简”删除。

## P1：页面一致性

- **UI-05：普通壳层页面标题只在顶栏面包屑出现一次。** 正文不再重复同名大标题、眉题和栏目说明；保留可访问标题语义。顶栏缺名称时先补名称再去重。设置弹窗、会务独立顶栏各自只留一个页面标题，不能叠加壳层同名标题。
  来由：用户 cc-9 给定的可判定检查项；`apps/web/src/components/layout/top-bar.tsx` 与 `apps/web/src/components/patterns/page.tsx`。`features/catalog/skills/index.tsx` 当前仍传 `PageHeader title="技能"`，仅作为待检查现状，不是豁免。删除条件：用户明确采用双层标题导航，并有相应信息架构设计替代。
- **UI-06：页面组织不用表格，不出现表格套表格、带边框卡片嵌表格或卡片套卡片。** 设置用 `SettingsSection` / `SettingsRow`，详情用 `Section`，目录用无框列表或独立条目的网格。旧管理表格迁移必须保留必要筛选 / 排序 / 批量操作；内容中的 Markdown 数据表、文件预览不是页面组织容器，不改变其语义。
  来由：用户 cc-9「不要表格 / 带边框卡片嵌在表格里」；`apps/web/src/components/patterns/settings-section.tsx`、`apps/web/src/components/patterns/page.tsx`。删除条件：用户对具体业务比较场景明确接受表格；仅删或收窄该场景限制，嵌套装饰禁令不随之失效。
- **UI-07：目录页复用技能页的工具栏职责，不复制整页外观。** `ListToolbar` 顺序为视图、搜索、筛选、布局、主操作；不存在的能力不占空位。单选用 `ToggleGroup type="single"`，无新增一套滑块。页面间距由 `Page` 承担，窄容器先重排再精简次要操作，不缩字挤内容。
  来由：用户 cc-9「新页面对齐技能页」；`apps/web/src/features/catalog/skills/index.tsx`、`apps/web/src/components/patterns/list-toolbar.tsx`、`apps/web/src/components/ui/toggle-group.tsx`。删除条件：共同目录骨架被新组件替代，所有消费者已迁移。
- **UI-08：数字展示一律 tabular-nums；字体和字号用现有角色。** 日期、时长、计数、容量、用量、进度允许从外层继承等宽数字。代码按 `font-mono`，界面不为“科技感”全改等宽；不改写用户文本 / 编辑器内容。
  来由：用户 cc-9 的等宽数字方向；`apps/web/src/styles/index.css` 字体角色、`apps/web/src/components/layout/top-bar.tsx` 的时钟。删除条件：数字排版已由统一基础样式覆盖且所有展示组件有验证，或用户明确更改数字策略。
- **UI-09：不新增 6px 滚动条，不用隐藏内容冒充隐藏轨道。** 保留滚动容器的滚轮 / 触控 / 键盘能力；使用已有 `ScrollArea` 时不把轨道重写成 6px。长会话上滚查看历史时不被流式输出强拉回底部，应有回到最新入口。
  来由：用户 cc-9；`apps/web/src/styles/index.css` 全局隐藏原生轨道、`apps/web/src/components/ui/scroll-area.tsx` 自绘轨道；[open-claude-ui 滚动参考](https://github.com/Caho1/open-claude-ui/blob/2d56ab417f888e8c77f5d5090f53c1f65a05ab0b/code-examples/useClaudeScrollPinning.ts)。删除条件：用户批准新滚动策略并完成各输入方式验证；消息滚动行为由等效规则接管。
- **UI-10：无数据、无匹配、加载、失败分别呈现。** `EmptyState` 简短说明原因和下一步，`Skeleton` 只表示等待；不能请求未结束就显示“暂无”，不能错误时无限转圈。无框页面的空态覆盖默认虚线外框。文案不重复标题，不展示无助于选择的实现细节；必要权限、风险说明保留。
  来由：用户 cc-9 的少文字要求；`apps/web/src/components/patterns/empty-state.tsx`、`apps/web/src/components/ui/skeleton.tsx`、`apps/web/src/features/catalog/skills/index.tsx` 的差异空态。删除条件：统一异步状态组件已完整承担这些分支，规则由其合同替代。

## P2：视觉与动效细节

- **UI-11：层级先靠对齐、留白、文字强弱与细分隔，不新增装饰外框和大阴影。** 结构圆角、浮层和 Composer 投影取已有令牌；“硬朗几何”不等于把输入框、气泡、按钮全改直角。保留焦点环与必要危险提示。
  来由：用户 cc-9 的 SpaceX 方向；[Apple Layout](https://developer.apple.com/design/human-interface-guidelines/layout)；`apps/web/src/styles/index.css`、`apps/web/src/themes/terracotta.json`。SpaceX 的具体像素与动效未实测，不能据此强推新常量。删除条件：用户批准新的视觉方向与令牌体系，并替换本条用途。
- **UI-12：动作图标沿用现有图标体系与尺寸档，动效只解释状态或回应操作。** 先用 `lucide-react` / 既有品牌组件和 `icon-inline`，不逐页加 emoji、私有 SVG 尺寸或负边距；不新添循环背景、逐行入场、弹簧引擎。已存在的全局背景 / 助手动效按现有开关检查，不以本条擅删。
  来由：用户 cc-9 的克制动效与保留已有体系；[Apple Motion](https://developer.apple.com/design/human-interface-guidelines/motion)；`apps/web/src/components/ui/button.tsx`、`apps/web/src/styles/index.css`。删除条件：统一图标 / 动效系统已替代并承担上述约束，或用户为特定场景明确改变表现策略。
- **UI-13：动效要流畅。** 只过渡 transform / opacity，过渡期间不逐帧重排 / 重渲染（尺寸观察合帧、过渡结束结算一次；非破坏性菜单非模态）；进出场引用统一动效常量，页面层不写时长 / 曲线魔法值；以帧测（每次交互掉帧中位数 ≤2、p95 ≤20ms）为准，改前后各测。来由：用户 2026-10-31（参照 Antigravity，全局）。links 权威文本见 `.claude/rules/ui-links.md` UI-13。
- **UI-14：图标统一细描边、尺寸档与颜色。** 全局描边 1.5（选中 2），自绘动作图标同值；尺寸档 size-4 / 3.5 / icon-inline / 5 / 6 / 10；默认 muted、悬停选中 foreground、危险 warn；页面层不写私有尺寸与局部描边。来由同上，links 权威文本见 UI-14。

## 证据要求

每项发现带规则 ID、页面状态、文件位置、期望 / 实际、修复组件。运行证据须含视口与 content 实宽、侧栏状态、主题、动效档；仅查源码写「运行待验证」。本草案的优先级不替代既有项目门禁。外站研究、截图来源及逐页计划见 Athena 的 `core/package/skills/ui-consistency/references/`。
