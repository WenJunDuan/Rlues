## 修复配方

路径以 links `apps/web/src/` 为根；详细参数和已知差异见 [速查](links-tokens.md)；截图来源与取证限制见 [全站检查计划](audit-plan.md#截图与证据边界)。

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
