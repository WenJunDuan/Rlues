---
name: ui-consistency
description: 编写、修改或审查 quantum-links 前端页面时，按既有 shadcn、主题令牌与三档动效检查 UI 一致性，给出组件级修复配方。用于会话、目录、设置及业务页面；不替代功能验收，不为其他产品套用本规范。
---
# links UI 一致性

本技能已同步至 2026-11-16 基线。目标：沿用 links 的交互与主题，页面组织精简、理工、干练，减少重复文字和容器装饰。规则只约束 links 页面；本文的 Markdown 表格用于说明，不是产品页面模板。

## 使用顺序

1. 确定涉及的路由、页面状态和现有公共组件。先读 [links 令牌速查](references/links-tokens.md)，再定位当前 links 源码；速查已更新至 2026-11-16 基准，覆盖 UI-15 材质、窗口外观与动效基建。
2. 新页面对照技能目录的工具栏顺序和交互，使用已有 `Page` / `ContentColumn` / `ListToolbar` / `SettingsSection`。**技能页是局部参照，不是已通过本清单的样板**，其正文标题等仍需检查。
3. 对照下面清单给每项写「通过 / 违例 / 不适用 / 待验证」，附文件位置或运行证据；不适用写原因。只审代码时，截图、实际尺寸、滚动与键盘行为标待验证。
4. 改动涉及开合、按压、拖拽、滚动、浮层、轮询或订阅时，先读 [动效 / 手感 / 流畅度参考](references/motion-feel.md)，找到对应技术及其裁定，再逐项判 C17–C24；按 UI-13 用 `node tools/perf/frames.mjs` 在改前、改后各测一次，关闭档加 `--reduce`。C19 / C20 / C21 / C22 只审源码时标「运行待验证」或「计数待验证」。
5. 按 [rules 草案](rules.md) 的 P0 → P1 → P2 修复本次授权范围；跨页面审查按 [全站检查计划](references/audit-plan.md)。不要因审查一个页面就重做全站主题。

取舍：用户明确要求优先；links 组件与令牌决定实现。外部参考分层（11-02），冲突按序：① links 规则 UI-01..UI-15；② Claude-UI [open-claude-ui](references/open-claude-ui.md)（锁 `be395eb4`）管会话 / agent 交互行为与配方（Composer、消息流、滚动钉底、思考折叠、工具授权、状态指示），MIT 但自述逆向重建，只借思路不抄代码；③ [Apple design](references/apple-design.md)（HIG）管新页面与改版的布局、间距、层级、材质与分层阴影、色彩用法、字体层级及按钮 / 列表 / 侧栏 / 工具栏 / 弹窗 / popover。[SpaceX](references/spacex-style.md) 只给留白 / 少文字方向。动效、手感、流畅度另见 [motion-feel](references/motion-feel.md)（来源 open-claude-ui / cindy / PI-Desktop / DEEIX / pizza / Octop，各自锁定提交，逐条给出采纳 / 改造 / 拒绝）；它排在 ①② 之后，不覆盖 Apple 的布局判断。用户 11-02 要的分层阴影与玻璃材质只经主题令牌、只用于控件 / 浮层层。外部色值、尺寸、弹簧参数不直接变成 links 常量，不新增 UI 库或动效引擎。

## 可判定检查清单

| ID | 通过条件 | 检查方式 |
|---|---|---|
| C01 标题 | 普通壳层页面的可见页面标题只在顶栏面包屑出现一次；正文无同名大标题、栏目眉题重复。设置弹窗或会务独立顶栏各有自己的唯一标题，不叠两套壳层标题。 | 核对 `top-bar.tsx`、`route-meta` 与页面；数可见页面标题。保留可访问名称 / 标题语义，不能只隐藏唯一标题。 |
| C02 正文宽度 | 使用 `Page`（角色宽度 `width="list" | "workspace" | "reading" | "canvas" | "prose" | "form"`）与 `ContentColumn`（含会话列 `chat-narrow | chat | chat-wide`）；正文与列布局量 content 容器，不靠 `lg:` / `xl:` 等 viewport 断点。相同视口下开合两侧栏仍容纳主操作，无整页水平溢出。 | 源码 + 测量 content 容器实宽；容器断点两侧各测一次。弹窗安全边距、移动输入字号可以量 viewport，不误判为正文断点。 |
| C03 页面组织 | 管理页面不用表格组织操作与内容；无表格套表格、带边框卡片塞入表格、卡片套卡片。优先无框列表 / 分组，目录网格只容纳真正独立条目。 | 查 `table` / `DataTable` / `Card` 的用途和嵌套，不以组件名直接定罪。用户文稿、Markdown、文件预览中的数据表属于内容，不改其数据语义。 |
| C04 留白与密度 | 页边距来自 `Page`，分组采用统一组件间距；相邻同类行左右边缘一致，无重复外框 padding。窄容器先换行、收次要操作，不靠缩字号挤入。 | 比较页面、工具栏、分组的首尾边界；长中文名称及最大字体档无遮挡。 |
| C05 文字 | 无重复页面说明、无把内部实现当产品文案；按钮用动作名。空态至多一条原因及一个主行动，必要说明保留；错误必须给恢复入口。 | 检查可见文案；去掉一句后若不影响选择与操作则删。权限、删除后果、字段格式不能为“少文字”省略。 |
| C06 字体与数字 | 界面 / 正文 / 代码分别消费现有字体角色；数字展示一律 `tabular-nums`，可继承至计数、用量、时长、日期、进度；不用 `font-mono` 代替等宽数字判据。 | 看 class 与 computed `font-variant-numeric`；计数从 9 → 10、计时更新不挤动邻近按钮。用户原文与编辑器内容不逐字加工。 |
| C07 色彩 | 背景、文字、分隔、强调、危险态都读语义令牌；不新增页面 hex / 随意中性色。accent 填充搭配对应 foreground，状态有文字或图形，不只靠颜色。 | 明 / 暗 + 极浅 / 较深主题色；文字与图标对比度按主题 ADR 的 4.5:1 / 3:1 检查。 |
| C08 几何与阴影 | 圆角用 `rounded-sm/md/lg/block/chip/composer/bubble` 等已有角色；分组不加大阴影，阴影档按层级取 `shadow-*` 令牌（静置 → 悬停 → 浮层）；浮出面统一消费 UI-15 四档材质令牌与 `components/ui/surface.ts`（`POPUP_SURFACE` / `MODAL_SURFACE` / `CARD_SURFACE` / `COMPOSER_SURFACE` / `DROP_INDICATOR`），页面不写私有 `backdrop-blur-*` 与魔法透明度，L2 区域面（`material-region`）任何档都不加 backdrop-filter（仅输入框叠 `material-frost`）。没有为装饰同时堆 border、ring 和 shadow 外轮廓。 | 对照令牌及组件；焦点环不算装饰轮廓，不能删。不要全站强制直角。 |
| C09 图标 | 全局细描边 1.5、统一尺寸档与颜色（UI-14）；动作图标沿用 `lucide-react` / 现有品牌组件；同一工具栏同档大小。纯图标按钮有可访问名称，键盘聚焦可见；不以 emoji 代替系统动作图标。 | DOM / 可访问树 + Tab；正文行内图标优先 `icon-inline`，不逐页写负 margin。 |
| C10 输入与按钮 | 用现有 `Input` / `Textarea` / `Button` 或 `features/composer`；静置、hover、focus、disabled、提交中、失败都有明确状态。中文候选确认不会发送，Shift+Enter 换行；提交中不重复触发。 | 输入法实测、空输入、长输入、失败重试；输入不会因撑高遮住发送按钮。业务专用快捷键按页面合同保留。 |
| C11 侧栏 | 展开 / 收起均有入口，当前项可辨，长名称不挤掉行尾操作；键盘能访问 hover 操作。沿用 shell 的折叠契约，不假设收起宽度为 0。 | 同视口切换，键盘聚焦 / 长标题 / 多条历史；本地规则记载流内收起态占 1px，改契约前须实测。 |
| C12 消息流 | 助手正文无需另套整块卡片；流式更新时用户上滚不被抢回底部；有回到最新入口，输入区和末条消息不互相遮挡。失败可重试、复制有结果反馈。 | 长会话流式生成中上滚、返回最新、停止、重试；代码块局部横向滚动不带动整页。 |
| C13 空与加载 | 首次无数据、筛选无结果、加载、错误是不同状态。用 `EmptyState` / `Skeleton`，不在请求未结束时显示“暂无”；关闭动效后仍有静态状态文字。防白屏：分页 / 切页签等局部异步数据（`useSuspenseQuery`）必须包裹本地局部 `<Suspense>` 或配置 `placeholderData`（如 `keepPreviousData`），禁止让翻页或筛选挂起整个路由壳层；代码分割懒加载组件必须使用 `retryableLazy`，避免单次网络瞬断或 chunk 404 导致整页崩溃。 | 四种状态分别检查；加载完成主操作位置无明显跳变，失败不会永久转圈；断网模拟与重试验证。 |
| C14 动效 | 流畅优先（UI-13：只过渡合成属性、过渡期不逐帧重排、帧测 ≤2 / 20ms）；界面三档「关闭 / 开启 / 高级」（UI-03），不跟随系统。CSS 走现有 `motion-safe` / `motion-reduce`，JS 走 `useReducedMotion` / `reducedMotion`；关闭后无动画、过渡、平滑滚动，结果仍可见；高级只多一层 WebGL 背景。流式与高帧率稳定：remark/rehype 插件、`hasFile` 判定、`Composer` 回调在 rAF 流式更新时必须保持稳定身份，避免 `<Streamdown>` 块 memoization 和 `React.memo(Composer)` 逐帧失效；KaTeX 等重度解析须设容量上限缓存。退场动效打磨：确认弹窗与抽屉在 `MODAL_MOTION` / `SHEET_MOTION` 退场期间必须保留目标显示数据，关闭瞬间释放遮罩指针事件（`data-[state=closed]:pointer-events-none`），避免退场期阻塞下层点击或内容闪白卸载。 | 三档 × 系统减少动态开 / 关；新增效果只回应状态或操作，不新增整页循环装饰。流式数据仍正常到达。 |
| C15 滚动 | 不新增 6px 自绘滚动条或页面级滚动条补丁。沿用现有滚动容器；滚轮、触控与键盘可到最后一项，无多层滚动困住用户。 | 查看 CSS 和 `ScrollArea` 用法；隐藏轨道不等于禁用滚动，不能用 `overflow-hidden` 代替。 |
| C16 交互反馈 | Tab 顺序可用、焦点不被裁切；浮层关闭后焦点返回入口；保存 / 复制 / 安装 / 连接反馈与实际结果一致，错误保留输入与恢复动作。 | 键盘完整走一次主操作；模拟失败；菜单内操作不误触整行导航。 |
| C17–C24 手感与流畅度 | 按压、开合、拖拽、滚动锚定、浮层身份、单一在途读取、隐藏即停、循环动效宿主，逐项条件见 [motion-feel 检查项](references/motion-feel.md#检查项-c17c24)。 | 同该节「检查方式」列；只审源码时 C19–C22 标运行 / 计数待验证。 |

## 修复配方

路径以 links `apps/web/src/` 为根；详细参数和已知差异见 [速查](references/links-tokens.md)；截图来源与取证限制见 [全站检查计划](references/audit-plan.md#截图与证据边界)。

| 违例 | 优先修复 |
|---|---|
| 顶栏与正文重复标题 | 查 `components/layout/top-bar.tsx` 与 `route-meta` 的当前页名称；正文 `PageHeader` 可省 `title`，保留 actions / back。若顶栏缺当前页名称，先补其显示与语义，不能直接删掉唯一标题。`TopSlotTarget` 已在 `components/layout/top-bar.tsx` 启用（通过 `MutationObserver` + `data-filled` 跟踪挂载状态与内容，空时不占位），页面可通过该插槽向顶栏注入页头内容。 |
| 每页手写 `max-w`、侧栏开后正文被挤 | 复用 `components/patterns/page.tsx`：`Page` 统一采用角色宽度（`width="list" | "workspace" | "reading" | "canvas" | "prose" | "form"`），单列表单内层收至 `max-w-form`；会话按 `config/theme.ts` 的 `CHAT_WIDTHS`（`chat-narrow` | `chat` | `chat-wide`）自适应，不要锁死固定 px。 |
| 表格承载设置、框中框 | 设置改 `SettingsSection` + `SettingsRow`；详情改同文件 `Section`；目录用现有列表或 `CardGrid`。迁移保留筛选、排序、选择与分页能力，不能只删容器丢功能。 |
| 搜索、筛选、布局开关各页乱序 | 用 `ListToolbar` 的 `view / search / filters / layout / actions` 槽，搜索用 `CatalogSearch`，单选视图用 `ToggleGroup type="single"`；不要复制一套分段滑块。 |
| 硬编码颜色、白字落在极浅色按钮上 | 换 `bg-background/surface/surface-raised`、`text-foreground/muted-foreground`、`border-divider`；主操作交给 `Button`，其默认变体已配 `bg-accent-fill text-accent-foreground`。700 / 900 底分别用其 foreground，不混配。 |
| 按钮 / 弹窗 / Composer 外观不一 | 复用 `components/ui/button.tsx`、`dialog.tsx`、`popover.tsx` 和 `features/composer/composer.tsx`；浮出面统一消费 `components/ui/surface.ts`（`POPUP_SURFACE` / `MODAL_SURFACE` / `CARD_SURFACE` / `COMPOSER_SURFACE`）；读取 `shadow-popover`、`shadow-composer[-hover/-focus]`，不搬外站 `--cds-*`。危险入口用现有 `warn-*` 变体。 |
| 空态虚线框与无框页面冲突 | 复用 `EmptyState` 的语义及 action，当前组件默认虚线边框可用 `className="border-0 rounded-none"` 覆盖；不要在表格单元内再套它的默认框。 |
| 加载时只有动画、关闭动效后消失 | `Skeleton` 保留静态占位，旁边给简短状态；JS 动效读取 `lib/hooks/use-reduced-motion.ts`。不要增加系统媒体查询分支。 |
| 字号、圆角来自外站像素 | 用 `text-app/control/item-title/meta` 与角色圆角；数字加 `tabular-nums`。按计算值核对主题，不依据旧注释中的“默认 12px”。 |
| 分页或切页签导致整页白屏挂起 | 页面内带分页 / 筛选的 `useSuspenseQuery` 必须包裹本地局部 `<Suspense fallback={<Skeleton />}>`，或在 query options 配置 `placeholderData: keepPreviousData`，避免局部翻页冒泡挂起顶层路由壳层；路由及弹窗代码分割懒加载组件统一使用 `retryableLazy` 承接。 |
| 流式输出逐帧掉帧、输入卡顿 | 消息渲染中 remark/rehype 插件配置与 `hasFile` 判定使用 `useMemo` 保持稳定引用，避免流式 rAF 逐帧重建导致 `<Streamdown>` 块 memoization 失效；`Composer` 交互回调使用 `useCallback`；KaTeX 解析使用有界缓存；非当前消息通过 `React.memo` 阻断重绘。 |
| 弹窗与抽屉退场闪白或阻塞指针 | 二次确认弹窗与侧滑抽屉在退场动画（`MODAL_MOTION` / `SHEET_MOTION`）期间缓存目标展示数据（不随 `open=false` 立即置空）；自绘遮罩挂载 `data-[state=closed]:pointer-events-none`，退场动画期间立即释放指针事件，恢复下层可交互。 |
| 流式消息跳动、输入法误发送 | 先查 `features/chat/` 的滚动与消息组件、`features/composer/keys.ts`；补状态和行为回归，不另引 open-claude-ui 的滚动 Hook 或整套 Composer。 |
