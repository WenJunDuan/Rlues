# links 令牌与组件速查

取证：2026-10-24；只读仓 `/Users/mi_manchi/workspace/quantum/quantum-links`，HEAD `6c3810be7cc8c10d05138d279435702cd9b46cfa`。读取时该仓另有 `.ai_state` 未提交改动，未触碰。以下路径相对该仓；数值是源码值，浏览器计算样式待验证。

## 入口与契约

| 来源 | 用途 |
|---|---|
| `apps/web/src/styles/index.css` | 实际全局入口，导入 `tailwindcss` 和 `tw-animate-css`；L1 映射、L2 结构、全局交互样式。任务所给 `apps/web/src/index.css` 不存在。 |
| `apps/web/src/themes/types.ts`、`serialize.ts`、`registry.ts`、`apply.ts` | 主题 schema / 序列化 / 注册 / 应用；核对新增主题能力时读。 |
| `apps/web/src/themes/terracotta.json`、`classical.json` | 当前主题 manifest；不是页面可复制的色值表。 |
| `.ai_state/decisions/2026-10-12-decision-theme-system.md` | 接受的主题契约及 10-13 修订：L0 `--ql-*` 公共主题，L1 Tailwind 内部映射，L2 字体 / 间距 / 字号结构。 |
| `apps/web/src/config/theme.ts`、`app/providers/theme-provider.tsx` | 当前 UI 档位与 DOM 状态；不能只按旧 ADR 推断默认值。 |

主题 manifest 只交经 schema 校验的数据与变体，不收任意 CSS。页面用 Tailwind 语义类或既有映射，不新增局部 `--ql-*` 覆盖。现有 shadcn 风格控件实现在 `components/ui`，内部复用 `radix-ui`；无需安装另一个组件库。

## 颜色和表面

| 角色 | 可用类 / 令牌 | 核对点 |
|---|---|---|
| 页面与正文 | `bg-background` → `--ql-bg`；`text-foreground` → `--ql-text` | 陶土浅色当前 `#FAF9F5` / `#141413`，深色 `#262623` / `#F1F0EC`；只是来源说明，不粘进页面。 |
| 次级面 / 浮起面 | `bg-surface`、`bg-surface-raised`、`bg-overlay`、`bg-paper` | surface 是层次，不是每个分组必须有底色。 |
| 次级文字 / 分隔 | `text-muted-foreground`、`border-divider`、`border-border`、`border-rule` | 次级文字映射 `--ql-text-muted`；分隔线与输入轮廓不是同一角色。 |
| 主操作 | `bg-accent-fill text-accent-foreground` | 默认 `Button` 已处理填充、hover 和前景；不是固定橙底白字。 |
| 深阶强调 | `bg-accent-700 text-accent-700-foreground`；900 同理 | 前景按实际底色配对；不能将填充前景套到所有色阶。 |
| 状态 / 危险 | `text-ok`、`text-warn`、`bg-warn-fill text-warn-fill-foreground` | 复用 `Button` 的 `warn` / `warn-outline` / `warn-ghost` / `warn-link`；必须有文字或图标语义。 |
| 焦点 | `ring-ring` / `--ql-ring` | 全局 `:focus-visible` 是 2px outline，按钮另有组件 ring；不因“细线风格”移除焦点。 |

ADR 10-13：主题填充前景在白与 `#141413` 中取对比更高者，文字 ≥4.5:1、图标 ≥3:1；classical 的前景策略有自身 manifest。陶土有 24 色，当前默认色为玉色 `#F0F8FF`，浅色页面可能有已有渐变。cc-9 的低饱和方向不授权撤掉用户主题或全局 Mesh 背景。

## 字体、字号、空间

| 用途 | 当前类 / 源码值 | 使用边界 |
|---|---|---|
| 界面字族 | `font-sans`：Anthropic Sans → Geist → 中文系统字族 | 不在页面声明字体文件。 |
| 阅读正文 / 标题字族 | `font-serif`：Anthropic Serif → Source Serif 4 → 中文系统字族 | 中文不等于强制宋体；使用现有正文组件。 |
| 代码字族 | `font-mono`：JetBrains Maple Mono → Geist Mono → 系统等宽 | 当前实现已不同于旧 ADR 的 Anthropic Mono 首选，不能按旧文档改回。 |
| 数字 | `tabular-nums` | 这是数字等宽特性，不要求所有文字改 `font-mono`。 |
| 常见字号 | `text-app` 14px；`text-control` 13px；`text-card-title` 15px；`text-item-title` .90625rem；`text-meta` 11px；`text-note` 11.5px | 用语义档，不为单页新增 `text-[13.2px]`；辅助字号不能承担整段正文。 |
| 页面标题 | `text-page-title` 28px；`text-page-hero` 38px | 令牌存在不代表每页需要正文大标题；先按 C01 去重。 |
| 输入 / 正文行高 | `leading-field` 1.7；`leading-reading` 1.75；`leading-composer` 1.8 | 会话 / Markdown 另按现有正文消费者；不要全站统一成一个值。 |
| 页面边距 | `px-page-x` 36px；`pt-page-top` 34px；`pb-page-bottom` 40px | `Page` 负责，内层不要重复套。首页另有 `page-top-hero` 52px。 |
| 阅读列 | `max-w-col` 840px，随 content 阈值 896 / 1024 / 1280px 切到 880 / 1040 / 1200px | 封装在 `ContentColumn width="prose"`；页面不重写断点。 |
| 全宽 / 表单 | `max-w-page-max` 1600px；`max-w-form` 720px | 列表 `width="full"`；单列表单可内收至 form。 |
| 会话列 | `chat-narrow` 800px；`chat` 924px；`chat-wide` 1080px；自适应映射 `prose` | `CHAT_WIDTHS` 的当前默认是「标准」；max-width 是上限，可用空间不足时要收窄。 |
| 自适应网格 | `CardGrid min="card"` 280px，`min="tile"` 168px；gap-3.5 | 组件内部 auto-fill / minmax 量自身容器。 |
| 会务 / 侧栏布局 | `--container-split-at` 832px；`--container-room3-at` 1100px；`--spacing-rail` 288px | 读当前会务布局再决定是否沿用，阈值不是所有页面的固定配方。 |

### 圆角与阴影

| 类 | 映射 | 当前陶土浅色继承值 |
|---|---|---|
| `rounded-sm/md/lg` | `--ql-radius-sm/md/lg` | 4 / 8 / 12px |
| `rounded-block` | `--ql-radius-md × 3` | 24px |
| `rounded-chip` | `--ql-radius-md × 2` | 16px |
| `rounded-composer` | `--ql-radius-md × 2.5` | 20px |
| `rounded-bubble` | `--ql-radius-md × 2.25` | 18px |
| `shadow-sm/md/lg` | 对应 `--ql-shadow-*` | 随主题变化，不在页面复制多层投影公式。 |
| `shadow-popover` | `--ql-shadow-popover`，回落 lg | 已有浮层边缘与投影，勿再叠装饰 ring。 |
| `shadow-composer[-hover/-focus]` | 同名 `--ql-shadow-*`，回落 sm / md / md | 常态 / 悬停 / 聚焦三档；由现有 Composer 消费。 |

`styles/index.css` 有一段旧注释以 md=4 推导“默认 12px / 8px”；当前陶土 md=8，须按 manifest 与公式算，不能引用注释当实测。

## 动效与滚动

| 能力 | 既有实现 | 用法 |
|---|---|---|
| 两档开关 | `config/theme.ts`：`开启 → full`，存储 `减少 → reduce`，显示「关闭」 | 旧「跟随系统」归一为开启；颜色明暗的系统模式与动效是两回事。 |
| CSS 守卫 | `styles/index.css` 重定义 `motion-safe` / `motion-reduce`；`html[data-motion='reduce']` 下禁用 animation / transition（含伪元素） | 不自行读系统媒体查询。 |
| JS 守卫 | `lib/hooks/use-reduced-motion.ts` | `useReducedMotion()` 订阅，`reducedMotion()` 即时读取；平滑滚动和字形效果也要尊重。 |
| 时长 | `duration-fast/snap/base/sheet/slow` = 60 / 120 / 200 / 300 / 450ms；composer 220、segment 150ms | 只为新增同类效果选择既有角色；不机械重写成熟组件内已有时长。 |
| 交互效果 | `button-press`、`grid-collapse`、`scroll-fade`、`icon-inline`；`ToggleGroup` 的 `data-segment-slider` | 复用组件和工具类，不移植外站引擎。scroll-fade 有能力检测且关闭动效时取消遮罩。 |
| 原生轨道 | 全局 `scrollbar-width:none`、WebKit width/height 0 | 仍允许滚动；不加 6px 覆盖。 |
| 显式自绘轨道 | `components/ui/scroll-area.tsx` 默认 `w-2.5` / `h-2.5` | 自绘轨道与原生隐藏策略不同；是否使用由现有页面决定，不能宣称全站无轨道。 |

## 组件定位

均位于 `apps/web/src/`：

- 页面 / 栏宽 / 网格：`components/patterns/page.tsx` 的 `Page`、`PageHeader`、`ContentColumn`、`CardGrid`；页内返回用 `BackLink`。
- 目录：`components/patterns/list-page.tsx`、`list-toolbar.tsx`、`catalog-search.tsx`、`list-layout-toggle.tsx`；参照 `features/catalog/skills/index.tsx`。
- 分组：`components/patterns/settings-section.tsx` 的 `SettingsSection`、`SettingsRow`、`Section`。区块无闭合外框；`bare` 可避免内容自带分隔时叠线。现有 `progress` 支路有固定 `bg-lime-400`，不作为新增配色模板，登记检查。
- 状态：`components/patterns/empty-state.tsx`、`components/ui/skeleton.tsx`、`components/layout/toaster.tsx`。EmptyState 默认有虚线框，无框页面需要覆盖。
- 基础操作：`components/ui/button.tsx`、`input.tsx`、`textarea.tsx`、`toggle-group.tsx`、`dialog.tsx`、`popover.tsx`、`dropdown-menu.tsx`；不要用外部库中的同名组件替换。
- 会话：`features/composer/composer.tsx` / `keys.ts`、`features/chat/components/chat-message.tsx` / `message-toolbar.tsx`；先找既有状态再修视觉。

## 已知差异，不作为本阶段修复

| 文档 / 现状差异 | 本草案处理 |
|---|---|
| 旧 ADR：Claude 默认、752px「主题默认」；当前配置：默认「标准」924px，主题默认档已下线 | manifest 中 prose.width=752 仍存在；不能宣称它就是当前会话宽度。 |
| 旧 ADR：三槽 Anthropic；当前代码 font-mono 首选 JetBrains Maple Mono | 记录差异，按当前代码复用；历史修订依据由主 agent 核对，不擅改 ADR。 |
| 技能页仍有正文 PageHeader；顶栏也有导航名称 / 当前页表达 | 标题计数运行待验证，按照 C01 审查，不能直接整页复制。 |
| `TopSlotProvider` 当前只返回 children，`TopSlotTarget` 是空槽；top-bar 仍留历史注释 | 不建议不存在的顶栏注入 API。会务按其独立页面壳层检查。 |

可复用的现有检查入口：`apps/web/tests/guards/theme-contract.test.ts`、`responsive.test.ts`、`typography-baseline.json`、`motion-baseline.json`、`apps/web/tests/themes/registry.test.ts`、`apps/web/tests/lib/hooks/use-reduced-motion.test.tsx`。本阶段只确认文件存在与源码约束，未运行 links 测试，不声称这些测试覆盖 cc-9 全部规则。
