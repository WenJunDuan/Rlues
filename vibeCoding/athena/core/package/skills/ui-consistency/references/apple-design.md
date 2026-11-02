# Apple design 层：布局与页面元素

来源：Apple Human Interface Guidelines（HIG）官方页的 Markdown 版（`https://developer.apple.com/design/human-interface-guidelines/<页>.md`），2026-11-02 读取。下表每行一条规则，写 HIG 原则 → links 落点；括号里是该页 Change log 最新日期。HIG 面向 Apple 原生平台，links 是 Web / Electron，**只取设计原则，不引入 Apple 平台依赖、SF 字体或 SF Symbols 资产**；pt 数值换算到 Web 不等价，均不直接变成 links 常量。

## 分工与冲突顺序

| 层 | 管什么 | 不管什么 |
|---|---|---|
| 1. links 项目规则 UI-01..UI-14（`<quantum-links>/.claude/rules/ui-links.md`） | 合同：令牌、两档动效、content 容器、标题、嵌套、图标档、帧测 | — |
| 2. Claude-UI（[open-claude-ui](open-claude-ui.md)） | 会话 / agent 交互行为与配方：Composer、输入法、消息流、滚动钉底、思考折叠、工具授权卡、状态指示 | 页面骨架、间距体系、材质 |
| 3. Apple design（本文） | 布局、间距、层级、材质与阴影、色彩用法、字体层级、按钮 / 列表 / 侧栏 / 工具栏 / 弹窗 / 浮层元素设计 | 会话交互细节 |

冲突时按 1 → 2 → 3。例：Apple 说跟随系统减少动态，links UI-03 只开 / 关两档 → 按 UI-03；会话区滚动行为按 Claude-UI，会话页留白与浮层层级按本文。

用户 11-02 明确要：**分层阴影与玻璃材质，经令牌实现**。这是对 UI-11「不新增大阴影 / 装饰外框」的方向补充：阴影与材质只能来自主题令牌、只用于有层级含义的面，不是放开页面私加。

## 布局与层级

| 规则 | 出处 | links 落点 |
|---|---|---|
| 按重要性排序：最重要的放上方、起始侧 | [Layout](https://developer.apple.com/design/human-interface-guidelines/layout)（2026-09-09） | 主操作、关键状态在 `ListToolbar` / 页首；低频动作进菜单 |
| 对齐便于扫读，用缩进表达层级 | Layout | 同组行左右边缘一致（C04）；子项缩进用既有组件，不手写负边距 |
| 用留白、容器形状或分隔线表达分组 | Layout | 先留白与 `divider`，再 `SettingsSection` / `Section`；不加装饰框（UI-06、UI-11） |
| 渐进展示：内容与选项过多时用披露收起 | Layout | `disclosure-chevron` / `grid-collapse`；高级项默认收起 |
| 控件与内容分层：控件浮在内容之上，用材质而非实色底区分 | Layout、[Materials](https://developer.apple.com/design/human-interface-guidelines/materials)（2025-09-09） | 顶栏、吸底 Composer、浮层用材质令牌（见下节）；正文不用 |
| 布局按可用空间（size class）决定，不按设备类型 / 方向 | Layout | 即 UI-02：量 content 容器（`Page` / `ContentColumn` 的容器断点），不用 `lg:` / `xl:` |
| 空间变化时功能不变，只增减可见量 | Layout | 窄容器先重排、把次要操作收进菜单，不删功能（UI-07） |
| 适配文字放大：层级保持、截断最少 | Layout、[Typography](https://developer.apple.com/design/human-interface-guidelines/typography)（2025-12-16） | 最大字体档 + 长中文名逐页测；行尾时间戳 / 图标不挤掉正文 |
| 先测最大与最小两种布局 | Layout | 运行证据：同视口侧栏开 / 合 × 最窄 / 最宽 content |
| macOS：关键控件和信息不放窗口底边 | Layout | 侧栏底部只放次要入口；主操作不只放底栏 |
| 带边框元素周围约 12pt、无边框约 24pt 留白 | [Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)（2025-06-09） | 按 links 间距令牌取近档，不新增常量；点击区不相互贴边 |
| macOS 控件默认 28×28pt、最小 20×20pt | Accessibility | links `Button` 图标档 `icon-lg` 32px / `icon` 28px / `icon-sm` 24px；24px 只用于紧凑工具行，点击区待逐页实测 |

## 深度、材质与阴影

| 规则 | 出处 | links 落点 |
|---|---|---|
| 材质分开前景（文字、控件）与背景（内容） | [Materials](https://developer.apple.com/design/human-interface-guidelines/materials) | 材质只给「浮在内容之上」的层：顶栏、吸底条 / Composer 壳、popover、菜单、sheet |
| Liquid Glass 不进内容层 | Materials | 消息、卡片、列表行、设置分组不加玻璃 |
| 玻璃克制使用；自定义控件尤其少用 | Materials | 一屏内同时可见的玻璃面 ≤ 导航 + 一个浮层 |
| 透明（clear）玻璃只用在视觉丰富背景上；其余用常规（regular） | Materials | 默认用较厚（低透明）档；只有 mesh 背景上的壳层可用较薄档 |
| 按语义选材质，不按它呈现的颜色选 | Materials | 令牌按用途命名（如 `material-bar` / `material-popover`），不按“毛玻璃白”命名 |
| 厚材质对比好、薄材质保留上下文 | Materials | 有细字的面（菜单、popover）用厚档；仅装饰性的壳可薄 |
| 材质上的文字用“活力色”保证可读 | Materials | Web 无 vibrancy：材质面上的文字 / 图标只用 `foreground` / `muted-foreground`，并在明 / 暗 / 极浅主题测 4.5:1 / 3:1 |
| 暗色下前台浮层从 base 升到 elevated 背景 | [Dark Mode](https://developer.apple.com/design/human-interface-guidelines/dark-mode)（2024-08-06） | 暗色层级靠 `background` → `surface` → `surface-raised` 提亮，阴影在暗色里弱，不能单靠阴影分层 |
| 用滚动边缘效果而非实色底把控件抬到内容之上 | Layout | 顶栏 / 吸底条与内容交界用边缘渐隐或细分隔，不加实色横条；实现前帧测（UI-13） |
| 在“减少透明度”“增强对比度”下仍可读 | Dark Mode | 每个材质令牌必须有不透明回落值；系统偏好联动与否由用户裁定，**待验证**（links 现无此开关） |

分层阴影（用户 11-02）：一层阴影 = 远处大半径低不透明柔影 + 近处小半径接触影，层级越高偏移与半径越大。links 现有 `--ql-shadow-sm/md/lg/popover/composer*` 已是两层结构（`apps/web/src/themes/terracotta.json`）。规则：

- 阴影档按层级分配：静置面 0 或 `sm` → 悬停 / 可拖 `md` → 浮层 `popover` / `lg`；同一面不叠 border + ring + shadow 三重外轮廓（C08）。
- 只过渡 transform / opacity；需要阴影变化时用伪元素预渲染两档阴影再淡入，不过渡 `box-shadow`（UI-13）。
- 玻璃材质令牌**尚未存在**：现状是 5 处页面直接写 `backdrop-blur-xl`（`features/chat/components/approval-card.tsx`、`followup-suggestions.tsx`、`message-outputs.tsx`、`features/scenes/step-page/action.tsx`、`features/settings/components/harness-admin-panel.tsx`），`styles/index.css` 在 mesh 动画时统一关掉 `backdrop-blur`。落地需新增主题令牌（建议 `--ql-material-{bar,popover,sheet}`：底色 + 透明度 + 模糊半径 + 不透明回落），经 `themes/types.ts` 校验，再把页面私有 `backdrop-blur-*` 迁到令牌；属 UI-01 范围内的令牌扩展，需主题 ADR 修订，**待实现**。
- `backdrop-filter` 每帧重算下层，动态背景下保持现有 `[data-mesh]` 关闭策略；新材质面上线前用 `node tools/perf/frames.mjs` 帧测。

## 色彩

| 规则 | 出处 | links 落点 |
|---|---|---|
| 同一颜色不表达两种含义（如品牌色既当强调又当状态） | [Color](https://developer.apple.com/design/human-interface-guidelines/color)（2025-12-16） | accent 只给主操作 / 选中；状态用 `warn` 等语义令牌 |
| 颜色须在明、暗、增强对比下都成立 | Color | 明 / 暗 × 极浅 / 较深主题色逐一测（C07） |
| 不硬编码系统色值，不改写语义色含义 | Color | 即 UI-01：只读 `--ql-*` 语义令牌，页面不写 hex |
| 不只靠颜色传达信息 | Color、Accessibility | 状态配图标或文字 |
| 玻璃上与按钮标签上的颜色克制，只给真正需要强调的元素 | Color、[Toolbars](https://developer.apple.com/design/human-interface-guidelines/toolbars)（2025-12-16） | 工具栏图标默认单色 `muted-foreground`，仅一个主操作着色（UI-14） |
| 对比度至少 4.5:1（小字） | Dark Mode | 与主题 ADR 的 4.5:1 / 3:1 一致 |
| 不提供应用内独立明暗设置（跟随系统） | Dark Mode | **冲突，按 links**：links 已有主题与明暗选择，属既有产品决定，不据此删除 |

## 字体与图标

| 规则 | 出处 | links 落点 |
|---|---|---|
| 用字重、字号、颜色表达层级，放大后层级不变 | Typography | 只用 `text-app/control/item-title/meta` 等角色 + `foreground`/`muted` 两级（UI-08） |
| 字体家族尽量少 | Typography | 界面 / 阅读 / 代码三个角色，不再加 |
| 避免 Ultralight / Thin / Light 字重 | Typography | 正文 ≥ Regular；细字只出现在大号展示数字 |
| macOS 基准：Body 13pt、Title 3 15pt、Title 1 22pt、Large Title 26pt | Typography | 只作相对比例参考；links 字号以主题结构令牌为准 |
| 图标与相邻文字字重匹配（SF Symbols 九档字重对应字体字重） | [SF Symbols](https://developer.apple.com/design/human-interface-guidelines/sf-symbols)（2025-07-28） | 即 UI-14：lucide 描边 1.5（选中 2），尺寸档 `size-4` / `3.5` / `icon-inline` / `5` / `6` / `10` |
| 用分层（hierarchical）渲染表达深度，变量色只表达变化 | SF Symbols | 图标主次靠 `foreground` / `muted`，不用多色 |
| 符号动效克制、目的明确；自定义图标给替代文本 | SF Symbols | 图标按钮必有 `aria-label`（UI-04）；不逐页加图标动画（UI-12） |
| 熟悉动作用熟悉图标；短文字比图标清楚时用文字 | [Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons)（2025-12-16） | 「编辑」「完成」类用文字；工具栏同组不混排文字按钮与图标按钮（Toolbars） |

## 页面元素

| 元素 | 规则 | 出处 | links 落点 |
|---|---|---|---|
| 按钮 | 视图里最可能的动作用醒目样式，只一个 | Buttons | `Button` 默认变体；同组其余 `ghost` / `outline` |
| 按钮 | 用样式而非尺寸区分首选项 | Buttons | 同组按钮同 `size` |
| 按钮 | 自定义按钮必须有按下态 | Buttons | 走 `Button` 的 active / focus-visible；不用 div 模拟（UI-04） |
| 按钮 | 破坏性动作不做主按钮 | Buttons | 危险用 `warn` 变体 + `confirm-dialog` |
| 按钮 | 不能即时完成的动作在按钮内显示进行中 | Buttons | 提交中禁用重复触发并显示状态（C10） |
| 按钮 | 打开新视图 / 窗口的按钮标题加省略号 | Buttons | 中文文案按需加「…」，**待用户确认**是否采纳 |
| 列表 / 表格 | 文本优先用列表呈现；行文字简短 | [Lists and tables](https://developer.apple.com/design/human-interface-guidelines/lists-and-tables)（2023-06-21） | `DataTable` 素表或无框列表（UI-06） |
| 列表 / 表格 | 选中要有反馈；窄宽时保住可读 | Lists and tables | 选中态 + 截断加 tooltip；列可隐藏 |
| 列表 / 表格 | 多列表格列头用名词短语；有价值时点列头排序 | Lists and tables | `DataTable` 列头；排序沿用现有能力 |
| 列表 / 表格 | 层级数据用大纲视图，不用平表 | Lists and tables | 用 `file-tree` / 披露行，不表格套表格 |
| 侧栏 | 可隐藏；窗口变窄可自动收起 | [Sidebars](https://developer.apple.com/design/human-interface-guidelines/sidebars)（2026-06-08） | 沿用壳层开合，收起仍占 1px（C11） |
| 侧栏 | 至多两级层级，用简短组名 | Sidebars | 分组标题短；更深层级进内容区 |
| 侧栏 | 用熟悉图标；图标颜色要有明确用途 | Sidebars | lucide `size-4`，默认 muted，选中 foreground |
| 侧栏 | 关键信息 / 操作不放侧栏底部 | Sidebars | 底部只放账户 / 设置入口 |
| 侧栏 | 内容可延伸到浮动侧栏下方 | Sidebars | 仅当侧栏改为材质浮层时考虑，**待设计** |
| 工具栏 | 克制选项避免拥挤；按宽度定义哪些项收进「更多」 | Toolbars | `ListToolbar` 窄容器收次要项（UI-07） |
| 工具栏 | 分组按功能和频率，至多 3 组 | Toolbars | 视图 / 搜索筛选 / 主操作三段 |
| 工具栏 | 只一个主操作，放末端 | Toolbars | `ListToolbar` 的 actions 槽在末尾 |
| 工具栏 | 少用自定义背景与着色控件；优先无边框系统图标 | Toolbars | 工具栏图标按钮 `ghost`，不加圆形描边 |
| 工具栏 | 标题简短（<15 字符），不用应用名作标题 | Toolbars | 顶栏面包屑名称短（UI-05） |
| Sheet / 弹窗 | 只用于短暂、偶发、重要的任务；复杂长流程换整页 | [Sheets](https://developer.apple.com/design/human-interface-guidelines/sheets)（2026-03-24） | `Dialog` 放确认与短表单；长流程走路由页 |
| Sheet / 弹窗 | 同时只一个；关闭回到父视图 | Sheets | 不弹窗叠弹窗；关闭恢复焦点（UI-04） |
| Sheet / 弹窗 | 有「完成」必有「取消」 | Sheets | 表单弹窗底部取消 + 主操作 |
| Sheet / 弹窗 | 需反复输入并观察结果时用非模态面板 | Sheets | 用侧面板 / `modal={false}`（UI-13） |
| Popover | 只承载少量信息或功能，大小刚好 | [Popovers](https://developer.apple.com/design/human-interface-guidelines/popovers) | `popover` 内容短；复杂内容进面板 |
| Popover | 同时只一个，不层叠，不在其上再盖视图 | Popovers | 不 popover 套 popover |
| Popover | 非模态 popover 意外关闭时保存已输入内容 | Popovers | 关闭不丢草稿（C16） |
| Popover | 警告不用 popover | Popovers | 警告走 `confirm-dialog` / 行内提示 |
| Popover | 尺寸变化要平滑过渡 | Popovers | 只动 transform / opacity，或 `grid-collapse`（UI-13） |

## 动效（只取不冲突部分）

| 规则 | 出处 | links 落点 |
|---|---|---|
| 动效有目的，不为动而动 | [Motion](https://developer.apple.com/design/human-interface-guidelines/motion)（2025-09-09） | UI-12：只解释状态或回应操作 |
| 动效可选，不作为唯一信息通道 | Motion | 关闭档仍显示状态（UI-03 / UI-04） |
| 反馈动效简短、准确；高频交互少加动效 | Motion | 用 `components/ui/motion.ts` 常量；列表行 hover 不加位移 |
| 不让人等动画结束才能操作 | Motion | 过渡期间可继续点击 / 输入 |
| 跟随系统“减少动态” | Motion、Accessibility | **冲突，按 UI-03**：只开 / 关两档，不加 `prefers-reduced-motion` 分支 |

## 待验证

- HIG pt 数值到 Web px 的对应（DPR、缩放）未实测；表中尺寸只作下限参考。
- 玻璃材质在 Edge Dev 下的帧率、在极浅主题色上的文字对比度未测；令牌落地后补帧测与对比度证据。
- 「减少透明度」是否联动、按钮省略号文案是否采纳，等用户裁定。
