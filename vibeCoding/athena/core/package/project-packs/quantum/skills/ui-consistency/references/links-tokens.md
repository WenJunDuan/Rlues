# links 令牌与组件速查

取证：2026-11-16；只读仓 `/Users/mi_manchi/workspace/quantum/quantum-links`，HEAD `e231ab723dfb11e6f406415ec05a2bd9153a8d0d`。以下路径相对该仓；数值是源码值，浏览器计算样式待验证。

## 入口与契约

| 来源 | 用途 |
|---|---|
| `apps/web/src/styles/index.css` | 实际全局入口，导入 `tailwindcss` 和 `tw-animate-css`；L1 映射、L2 结构、UI-15 材质、窗口外观与全局交互动效。 |
| `apps/web/src/themes/types.ts`、`serialize.ts`、`registry.ts`、`apply.ts` | 主题 schema / 序列化 / 注册 / 应用；核对新增主题能力时读。 |
| `apps/web/src/themes/terracotta.json`、`classical.json` | 当前主题 manifest；不是页面可复制的色值表。 |
| `.ai_state/decisions/2026-10-12-decision-theme-system.md` | 接受的主题契约及 10-13 修订：L0 `--ql-*` 公共主题，L1 Tailwind 内部映射，L2 字体 / 间距 / 字号结构。 |
| `apps/web/src/config/theme.ts`、`app/providers/theme-provider.tsx` | 当前 UI 档位与 DOM 状态；不能只按旧 ADR 推断默认值。 |

主题 manifest 只交经 schema 校验的数据与变体，不收任意 CSS。页面用 Tailwind 语义类或既有映射，不新增局部 `--ql-*` 覆盖。现有 shadcn 风格控件实现在 `components/ui`，内部复用 `radix-ui`；无需安装另一个组件库。

## 颜色和基础表面

| 角色 | 可用类 / 令牌 | 核对点 |
|---|---|---|
| 页面与正文 | `bg-background` → `--ql-bg`；`text-foreground` → `--ql-text` | 陶土浅色当前 `#FAF9F5` / `#141413`，深色 `#262623` / `#F1F0EC`；只是来源说明，不粘进页面。 |
| 次级面 / 浮起面 | `bg-surface`、`bg-surface-raised`、`bg-overlay`、`bg-paper` | surface 是层次，不是每个分组必须有底色。 |
| 次级文字 / 分隔 | `text-muted-foreground`、`border-divider`、`border-border`、`border-rule` | 次级文字映射 `--ql-text-muted`；分隔线与输入轮廓不是同一角色。 |
| 主操作 | `bg-accent-fill text-accent-foreground` | 默认 `Button` 已处理填充、hover 和前景；不是固定橙底白字。 |
| 深阶强调 | `bg-accent-700 text-accent-700-foreground`；900 同理 | 前景按实际底色配对；不能将填充前景套到所有色阶。 |
| 状态 / 危险 | `text-ok`、`text-warn`、`bg-warn-fill text-warn-fill-foreground` | 复用 `Button` 的 `warn` / `warn-outline` / `warn-ghost` / `warn-link`；必须有文字或图标语义。 |
| 焦点 | `ring-ring` / `--ql-ring` | 全局 `:focus-visible` 是 2px outline，按钮另有组件 ring；不因“细线风格”移除焦点。 |

ADR 10-13：主题填充前景在白与 `#141413` 中取对比更高者，文字 ≥4.5:1、图标 ≥3:1；classical 的前景策略有自身 manifest。陶土有 24 色，当前默认色为玉色 `#F0F8FF`。低饱和方向不授权撤掉用户主题或全局 Mesh 背景。

## UI-15 四档材质令牌体系与表面基建

全站浮出表面分为 L2 区域与 L3 弹出两层，统一受 `<html data-material="off|frost|clear|glass">` 四档（关 / 磨砂 / 高透 / 玻璃，默认 clear）控制。

### 1. 材质变量与四档表现（`styles/index.css`）

- **高透（`clear`，默认）**：
  - 区域玻璃：`--ql-material-region: var(--color-glass-region)`（浅 paper 34% / 深 40%）；顶边高光 `--ql-material-highlight: var(--color-glass-highlight)`。
  - 会话输入框实时模糊：`--ql-material-frost-blur: 14px`，`--ql-material-frost-saturate: 1.3`。
  - 浮层（regular）：`--ql-material-regular: color-mix(in srgb, var(--color-overlay) 75%, transparent)`（深色 87%），模糊 24px，饱和度 1.8。
  - 模态（thick）：`--ql-material-thick: var(--color-glass-panel)`（82% 基准），模糊 40px，饱和度 1.9。
- **关（`off`）**：
  - 去掉全站所有 `backdrop-filter`（含输入框 frost）；各层均为实底（区域 `var(--ql-paper)`，浮层 `var(--color-overlay)`，模态 `var(--ql-bg)` / 深色 `var(--ql-paper)`），无顶边高光。
- **磨砂（`frost`）**：
  - 区域纸底 58%（深 62%）；浮层 overlay 86%（深 90%）+ 40px 模糊；模态 94% + 40px 模糊。
- **玻璃（`glass`）**：
  - 区域纸底 28%（深 34%）+ 顶边高光；浮层 overlay 73%（深 85%）+ 32px 模糊 + 1.9 饱和 + 顶边高光；模态浅 73% / 深 81% + 40px 模糊。

### 2. Tailwind 材质实用类（`@utility`）

- `material-region`：L2 区域玻璃（顶栏、侧栏、右栏、输入框外框），带 1px 细边 + 顶边 1px 高光 + 4% 静态噪点。**除输入框外，任何材质档均不加 backdrop-filter**，避免动态背景逐帧离屏重绘导致掉帧。
- `material-frost`：会话输入框专用实时模糊，全站唯一常驻实时模糊。
- `material-bar`：吸底 / 吸顶操作条，底色随浮层档 `var(--ql-material-regular)`，不加 backdrop-filter。
- `material-regular`：L3 贴触发点浮层（菜单 / 下拉 / 选择 / 贴触发点卡片 / 通知），带 regular 模糊与饱和度。
- `material-thick`：L3 模态（dialog / alert-dialog / sheet / 设置 / 命令面板），带 thick 模糊与顶边高光。

### 3. 表面基建导出（`components/ui/surface.ts`）

全站浮出表面必须引用 `surface.ts` 集中常量，禁止页面私写底色、透明度或模糊：
- `POPUP_SURFACE`：`rounded-lg material-regular text-foreground shadow-popover`。用于贴触发点的浮层、下拉、右键菜单、通知与提示卡片。
- `MODAL_SURFACE`：`border-glass-edge material-thick shadow-modal`。用于居中弹窗（Dialog / AlertDialog）与侧滑抽屉（Sheet）。
- `CARD_SURFACE`：`rounded-block material-region text-foreground`。用于排在会话流内的审批卡、确认卡、任务卡、文件差异等，不模糊、不加投影。
- `COMPOSER_SURFACE`：`group/composer-box relative cursor-text rounded-composer material-region material-frost border-0 shadow-composer hover:not-focus-within:shadow-composer-hover focus-within:shadow-composer-focus`。
- `DROP_INDICATOR`：`pointer-events-none absolute inset-0 rounded-[inherit] ring-2 ring-inset ring-accent-600 opacity-0 transition-opacity duration-segment motion-reduce:transition-none data-[state=ready]:opacity-35 data-[state=over]:opacity-100`。文件拖入仅过渡透明度，不过渡阴影或模糊。

全站材质边界受 `apps/web/tests/guards/material-surfaces.test.ts` 静态白名单守卫。

## 布局与窗口外观令牌

### 1. 窗口与壳层属性

- `data-chrome="float|dock"`（浮动 / 贴合布局，`config/chrome.ts`）：
  - 默认 `float`：`--ql-region-gap: 8px`、`--ql-region-radius: var(--ql-radius-lg)`（8px）、`--ql-side-panel-edge: 1px`。
  - `dock`（贴合）：`--ql-region-gap: 0px`、`--ql-region-radius: 0px`、`--ql-side-panel-edge: 0px`。区域玻璃紧贴窗口与彼此，外圈细边去掉，相邻区域只留发丝线，顶边高光取消。
- `data-window-material="system|app"`（桌面壳窗口材质）：
  - `system`：macOS vibrancy / Win11 Mica 透出；页面与 body 不铺底，壳层根铺半透明 `glass-window`，不挂 WebGL/色斑 mesh 背景。
  - `app`：不透明应用窗口，沿用分层玻璃与 mesh 背景。
- `data-window-controls="start|end"`（窗口控制按钮角）：
  - `start`：左上按钮区（macOS 红绿灯 / Linux 左置），侧栏头部下移让位，顶栏未停靠时让出左上。
  - `end`：右上叠加区（Windows / Linux 右置），顶栏横跨两列或右侧会话栏让出顶部。
- `data-window-active="false"`（窗口失焦）：
  - 桌面窗口失焦时主题默认按钮与 Logo 填充与文字成对降灰；网页版不挂该属性。

### 2. 角色列宽与正文阶梯（`components/patterns/page.tsx`）

`Page` 统一采用角色宽度（`type PageWidth = 'reading' | 'list' | 'workspace' | 'canvas' | 'prose' | 'form'`），`ContentColumn` 额外支持会话定值列：
- `list` / `workspace`：`w-full min-w-0`（全宽列表或工作台，无外层限宽）。
- `reading`：`mx-auto max-w-reading`（768px，单列阅读）。
- `canvas`：`ql-layout w-full min-w-0 h-full`（全屏画布）。
- `prose`：随 content 容器宽自适应阶梯（`max-w-col` 840px，容器到达 896 / 1024 / 1280px 时分别阶梯扩至 880 / 1040 / 1200px）。抽屉过渡期间由 `freezeWidthDuringPanelMove` 冻结终态宽度，长列表不逐帧重排。
- `form`：`mx-auto max-w-form`（720px，单列表单上限）。
- `chat-narrow`：`mx-auto max-w-chat-narrow`（800px）。
- `chat`：`mx-auto max-w-chat`（924px，默认标准宽度）。
- `chat-wide`：`mx-auto max-w-chat-wide`（1080px）。
- `CardGrid min="card"`：`grid-cols-[repeat(auto-fill,minmax(min(var(--spacing-card-min),100%),1fr))]`（280px）。
- `CardGrid min="tile"`：`grid-cols-[repeat(auto-fill,minmax(min(var(--spacing-tile-min),100%),1fr))]`（168px）。

### 3. 圆角与阴影

| 类 | 映射 | 陶土浅色继承值 |
|---|---|---|
| `rounded-sm/md/lg` | `--ql-radius-sm/md/lg` | 4 / 8 / 12px |
| `rounded-block` | `--ql-radius-md × 3` | 24px |
| `rounded-chip` | `--ql-radius-md × 2` | 16px |
| `rounded-composer` | `--ql-radius-md × 2.5` | 20px |
| `rounded-bubble` | `--ql-radius-md × 2.25` | 18px |
| `shadow-sm/md/lg` | 对应 `--ql-shadow-*` | 随主题变化，不在页面复制多层投影公式。 |
| `shadow-popover` | `--ql-shadow-popover`，回落 lg | 浮层投影；不在此基础上再叠装饰 ring。 |
| `shadow-modal` | `--ql-shadow-modal` | 居中模态与抽屉投影。 |
| `shadow-composer[-hover/-focus]` | 同名 `--ql-shadow-*` | 常态 / 悬停 / 聚焦三档，由 Composer 消费。 |

## 动效与指示器基建

### 1. 三档动效契约（UI-03）

- 存储：`减少 / 开启 / 高级` → DOM `<html data-motion="reduce|full|advanced">`。
- 界面展示：**「关闭 / 开启 / 高级」**。
- `关闭`：`styles/index.css` 全局重定义 `motion-reduce` 并对 `html[data-motion='reduce']` 强行禁用全部 CSS 动画、过渡与平滑滚动，业务流式数据正常到达。
- `开启`：启用 CSS 关键帧与 transition，进出场曲线读档位弹簧 `--motion-panel-ease`（card 弹簧）。
- `高级`：开启档动效 + 换过冲更强的 press 弹簧 + L3 弹出玻璃背景模糊在打开过渡中渐入（`@starting-style`）+ WebGL 背景（`MeshShader`，失败退回 CSS 色斑）。

### 2. 进出场与过渡集中常量（`components/ui/motion.ts`）

| 常量 | 定义 / 规格 | 用途 |
|---|---|---|
| `FLOAT_MOTION` | `animate-in fade-in-0 zoom-in-95 duration-card ease-(--motion-panel-ease) data-[side=...]:slide-in-from-... data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:duration-snap data-[state=closed]:ease-out-expo` | 贴触发点浮层（Popover, Select, Dropdown, ContextMenu, Tooltip）。入场弹簧，退场 snap 仅淡出。 |
| `MODAL_MOTION` | 缩放 98% + 淡入，duration-card；退场 snap + ease-out-expo 仅淡出 | 居中模态（Dialog, AlertDialog）。 |
| `SCRIM_MOTION` | 遮罩开场 base 淡入，退场 snap 淡出 | 模态遮罩。 |
| `SHEET_MOTION` | 抽屉平移，开场 duration-sheet + 档位弹簧，关场 base | 侧滑抽屉（Sheet）。 |
| `PANEL_TRANSITION` | `duration-(--motion-panel-duration) ease-(--motion-panel-ease) motion-reduce:transition-none` | 宽度与开合过渡。 |
| `SIDEBAR_PEEK_MOTION` | `transition-[translate,opacity] ${PANEL_TRANSITION}` | 侧栏悬停预览。 |
| `SIDE_PANEL_ENTER` / `SIDE_PANEL_EXIT` | `translate-x-0` / `translate-x-[calc(100%_+_var(--spacing-region))]` | 右侧会话栏平移进出。 |
| `ICON_SWAP_MOTION` | `animate-icon-swap`（缩放 60% + -60° 旋转淡入） | 状态图标切换。 |
| `ATTACHMENT_MOTION` | `animate-grow-in`，退场 snap 缩小淡出 | 附件 chip。 |
| `ATTACHMENT_LIST_MOTION` | `transition-[translate] duration-card ease-(--motion-panel-ease)` | 附件换行补位。 |
| `CHEVRON_MOTION` | `motion-safe:transition-transform motion-safe:duration-segment motion-safe:ease-(--motion-panel-ease)` | 展开 / 折叠箭头旋转。 |
| `TAB_ENTER_MOTION` | `animate-in fade-in-0 zoom-in-95 duration-card ease-(--motion-panel-ease)` | 侧栏标签 / 新标签页入口淡入缩放。 |
| `BROWSER_MARK_MS` | 465ms | agent 浏览器动作标记停留时长。 |
| `SPINNER_MOTION` | `motion-safe:animate-spin` | 旋转图标只转 HTML 宿主，关闭档静止。 |

### 3. 指示器与工具类

- `@utility animate-out`：配置 `animation-fill-mode: forwards` 与 `@keyframes exit-clean`，保持退场终态直到节点卸载，避免结束帧闪回。
- `SelectionSlider`（`components/ui/selection-slider.tsx`）：悬停 / 聚焦的中性滑块（侧栏导航、会话右栏磁贴 hover），仅平移跟踪到当前项，离开网格淡出隐藏。
- `TAB_INDICATOR`（`components/ui/tab-indicator.ts`）：选项卡下划线指示器，仅过渡 opacity / transform。
- `IconSwap`（`components/ui/icon-swap.tsx`）：状态图标平滑切换组件（复制对勾、播放/暂停、展开/收起、语音状态）。
- `MeshShader`（`components/layout/mesh-backdrop.tsx`, `mesh-shader.tsx`, `mesh-scenes.ts`）：
  - 高级动效档按需动态加载的灵动 WebGL 背景。
  - 包含 9 个场景：`['团', '一缕烟', '云', '快烟', '雨', '墨滴', '极光', '光斑', '浮尘']`，每 50 秒一轮（8 秒交叉淡化）。
  - 运行上限锁定在 15fps（`MESH_FPS = 15`，`setInterval` 驱动，不占满 rAF 渲染管线）。
  - 缓冲像素上限 960px（`BUFFER_MAX_WIDTH = 960`，DPR 恒按 1 缩放，节省 GPU 显存）。
  - 与 CSS 色斑采用 450ms 交叉淡化衔接（`MESH_HANDOFF_MS = 450`），就绪后画布淡入、色斑淡出，离开高级时画布淡出、色斑淡入，平滑无闪烁。

## 组件定位

均位于 `apps/web/src/`：

- 页面 / 栏宽 / 网格：`components/patterns/page.tsx` 的 `Page`、`PageHeader`、`TopSlotTarget`、`ContentColumn`、`CardGrid`；页内返回用 `BackLink`。
- 目录：`components/patterns/list-page.tsx`、`list-toolbar.tsx`、`catalog-search.tsx`、`list-layout-toggle.tsx`；参照 `features/catalog/skills/index.tsx`。
- 分组：`components/patterns/settings-section.tsx` 的 `SettingsSection`、`SettingsRow`、`Section`。
- 状态与容错：`components/patterns/empty-state.tsx`、`components/ui/skeleton.tsx`、`components/patterns/retryable-lazy.tsx`（`retryableLazy`）。
- 基础操作：`components/ui/button.tsx`、`input.tsx`、`textarea.tsx`、`toggle-group.tsx`、`dialog.tsx`、`popover.tsx`、`dropdown-menu.tsx`、`alert-dialog.tsx`、`sheet.tsx`。
- 表面与动效：`components/ui/surface.ts`、`components/ui/motion.ts`、`components/ui/selection-slider.tsx`、`components/ui/icon-swap.tsx`、`components/ui/tab-indicator.ts`。
- 会话：`features/composer/composer.tsx` / `keys.ts`、`features/chat/components/chat-message.tsx` / `message-toolbar.tsx` / `message-markdown.tsx`。

## 已知差异，不作为本阶段修复

| 文档 / 现状差异 | 本草案处理 |
|---|---|
| 主题 manifest 中 `terracotta.json` 仍保留历史字段 `prose.width = 752` | manifest 字段为历史遗留；实际正文与会话宽度已由 `CHAT_WIDTHS`（默认「标准」924px）与 `Page` 角色宽度接管，不依 752px 推断会话宽度。 |
| 旧 ADR 记载的三槽 Anthropic Mono 字体；当前代码代码字族首选 JetBrains Maple Mono | 记录差异，按当前代码复用；历史修订依据由主 agent 核对，不擅改 ADR。 |
| 技能页仍有正文 PageHeader；顶栏也有导航名称 / 当前页表达 | 标题计数运行待验证，按照 C01 审查，不能直接整页复制。 |

可复用的现有检查入口：`apps/web/tests/guards/theme-contract.test.ts`、`material-surfaces.test.ts`、`responsive.test.ts`、`typography-baseline.json`、`motion-baseline.json`、`apps/web/tests/themes/registry.test.ts`、`apps/web/tests/lib/hooks/use-reduced-motion.test.tsx`。
