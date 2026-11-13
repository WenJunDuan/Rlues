# open-claude-ui：可迁移的 UI 细节

来源：[Caho1/open-claude-ui](https://github.com/Caho1/open-claude-ui)（main）。2026-10-24 首读锁定 `c1f923ae`；2026-11-02 锁 `2d56ab41`；2026-11-13 重新同步，现锁定 `be395eb4b783cad3148fd9a4ef7641a3d198dd52`（2026-11-06，PR #32 合入，领先 `2d56ab41` 11 个提交，即上游 HEAD）。源码经本地克隆与 GitHub compare API 读取，没有安装或运行。下表引用的 code-examples 与 v1 / v4.29.0 文档在两锁之间逐字相同，链接统一换成新 sha。

边界（不变）：

- 许可证 MIT，但仓库自述为对 Claude 桌面端的「逆向分析」重建（REA 工具拆 ASAR），部分 CSS 注明「官方原文逐字移植」。**只借思路，不复制代码 / CSS / 色值**；它不是 Anthropic 官方规范。
- 作者的“生产级”“运行时实证”“物理常数已验证”等声明未独立复验，不能当作 links 验收证据。
- links 约束优先：不引入 framer-motion / 弹簧引擎（弹簧只用 links 自己的 CSS `linear()` 令牌，UI-12）；动效为关闭 / 开启 / 高级三档，**不加 `prefers-reduced-motion` 分支**（UI-03）；只过渡合成属性（UI-13）。动效 / 手感 / 流畅度的跨仓对照另见 [motion-feel](motion-feel.md)。

下表区分「该仓源码 / 文档事实」与「links 采纳建议」。源码与旧说明不同的数值分别记录，不拼成一套所谓官方参数。

| 维度 | 已核对的参考细节及出处 | links 的取舍 |
|---|---|---|
| 布局 | [ContainerResponsiveBar](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/ContainerResponsiveBar.tsx) 按命名容器调整工具栏：较窄时隐去次要文字，主动作保留；[v1 设计章节（历史快照）](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/docs/v1/01-设计哲学与设计令牌体系.md) 描述侧栏、中心聊天列、浮层的层级。 | 采纳“量可用容器”的方法；仍用 links 的 ContentColumn，不搬其 320/384/480/576 阈值或侧栏尺寸。 |
| 间距 | [ChatComposer](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/ChatComposer.tsx) 外层 px-4，壳内 .875rem padding、gap-y-2，工具组 gap-1.5；附件和工具栏与正文分区。 | 抄分组关系，不复制像素；links 外层 Page、内部组件已有间距。 |
| 字号 / 字体 | 同一 ChatComposer 的正文 15px、工具文字 text-xs，消息组件正文也为 15px；[v1 设计章节 §1.5（历史快照）](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/docs/v1/01-设计哲学与设计令牌体系.md) 区分界面、阅读、代码角色及 tabular-nums。 | 采纳角色与数字对齐；链接到 links 字体槽和 text-* 角色，不导入专有字体，不照搬其光学缩放。 |
| 色彩层级 | [cds-theme.css](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/cds-theme.css) 用 surface-0…3 区分底层到浮层；浅色依次为 #f9f9f7、#fcfcfb、白、白，深色为 #0b0b0b、#151515、#1a1a19、#20201f（11-02 未变）。11-02 新增：文字色改走 neutral 阶（浅 #0b0b0b / #52514e / #898781）；`accent` 角色为**蓝**（#184f95），`brand` 陶土只给 Claude 发起的动作（发送 / 生成），二者不可互换；焦点环改蓝。 | 采纳微差表面、强调稀少、「角色不混用」；实际颜色只从 links `--ql-*` 来，不引入蓝色 accent 或改 links 焦点色（UI-01）。浅色同值表面并非靠色差就能完全区分。 |
| 圆角 / 密度 | 11-02：Composer 由 20px 改为 `calc(.75rem * --cds-rem-scale)`=12px（`data-density="comfortable"` 14px），Dialog 仍 16px；整套尺寸（圆角、控件高、图标、pad / gap）改为 `N * --cds-rem-scale` 随密度缩放。[CdsButton](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/CdsButton.tsx) 尺寸阶梯 20/24/28/32/40px，内边距改为 6/8/8/12px。旧版 v1 说明写的气泡 18px 已是历史值。 | 不宣称参考有固定圆角；links 用角色圆角，当前陶土 composer20 / bubble18 是 links 自身公式结果，不跟改 12px。采纳「尺寸随一个密度系数缩放」的思路，落地需 links 令牌 ADR，不直接加。 |
| 阴影与边缘 | 同一 CSS 提供多档投影、Composer 常态 / hover / focus。11-02：`shadow-popover` 改为纯两层投影（去掉内描边，浅 0 8px 24px 12% + 0 2px 6px 8%）；sm/md/lg 偏移层随暗色走 gray-900；暗色 shadow-color 0.24。「单闭合边框」：卡片内次级按钮不带边框。 | 采纳「两层投影 = 远处柔影 + 近处接触影」与按层级分配；links 已有 `shadow-sm/md/lg/popover/composer*`，在 links 令牌里调，不搬数值，勿叠一份 border 和 glow。分层阴影的 Apple 侧落点见 [apple-design](apple-design.md#深度材质与阴影)。 |
| 图标 | v1 §1.5（历史快照）讨论行内垂直对齐、图标尺寸档；[ChatComposer](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/ChatComposer.tsx) 发送 SVG 有 aria-label，但工具项也使用 emoji / 文字符号。 | 采纳尺寸 / 对齐 / 名称原则，不照搬示例 emoji；links 用 Lucide 和 icon-inline。 |
| 动效 | [ThinkingAccordion](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/ThinkingAccordion.tsx) 与消息示例用 grid 行高展开；[ClaudeMotionPresets](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/ClaudeMotionPresets.ts) 提供不同交互用途的弹簧配置。 | 采纳“反馈随动作”的区分，复用 links grid-collapse / tw-animate-css；本阶段不引入弹簧库、音效或环境发光。 |
| 输入框 | [ChatComposer](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/ChatComposer.tsx) 输入区最小3rem、最大24rem，field-sizing 自适应；空文本且无附件时禁发送；composition、isComposing、229 防止候选确认误发，Shift+Enter 留换行。 | 采纳行为检查；links 现有 Composer 接管实现，保留自己的模型、附件、权限状态。该示例的 hover/focus 实际效果仍需运行验证。 |
| 侧栏 | [DraggableSessionList](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/DraggableSessionList.tsx) 分固定 / 最近会话，具选中态、重排指示与 Alt+上下键；PointerMove 中有4px拖动阈值。 | 只对 links 已有拖拽能力检查误触 / 键盘路径；不据此新增拖拽功能或强制4px阈值。 |
| 消息流 | [ChatMessageBubbles](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/ChatMessageBubbles.tsx) 区分用户气泡和无框助手正文，操作组支持 hover / focus-within；[useClaudeScrollPinning](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/useClaudeScrollPinning.ts) 含150ms输入冷却、40px底部容差和离底120px返回入口。 | 采纳“不抢滚动”和可找回最新消息，不把这些阈值定为 links 硬规则；示例没有证明长流式场景的运行正确性。 |
| 空态 | 已读设计章节列出问候语显示字号，示例 Composer 提供输入占位。检查的上述核心组件未形成统一的“首次空 / 无匹配 / 无权限 / 失败”页面状态规范。 | 空态结论有限，完整首屏 / 空态视觉待验证；links 用自己的 EmptyState 与技能页差异文案，不编造参考页截图。 |
| 加载态 | [StatusIndicators](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/StatusIndicators.tsx) 有状态点、思考点、扫光骨架和文字 label。11-02：骨架统一为 2s linear 105° 扫光（旧 1.8s / 90° 作废）；`data-motion=wave`（逐块延迟 90ms）与 `lockstep`（同步 1→0.6→1 呼吸，密集列表）两档；`data-hold` 三态延迟揭示；新增不定进度条 `cds-progress-sweep`（1.6s，只动 transform）。 | 采纳「密集列表同步呼吸、大块内容扫光」「延迟揭示避免闪骨架」「不定进度只动 transform」三条思路，沿用 links Skeleton / 助手标记；关闭动效时用 links `data-motion="reduce"`，不照抄其 `prefers-reduced-motion` 双层守卫。6px 状态点不是 6px 滚动条。 |
| 附件增删（11-02 新） | [AttachmentCard](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/AttachmentCard.tsx) 用 `document.startViewTransition` 包裹附件增删 / 重排，每卡 `view-transition-name`，`@starting-style` 入场；CSS 注明为客户端原文移植。 | 只借「增删重排用共享元素过渡、不支持时同步更新」的思路；不复制其 CSS。若 links 采用 View Transitions，关闭档必须跳过过渡直接更新，且仅动合成属性，先帧测（UI-13）。 |
| 窗口失焦（11-02 新） | 4.29.0 增量：`data-window-active=false` 时 brand / primary 填充去色为灰。 | Electron 多窗口机制，links Web / 桌面壳不采纳；仅作「非活动态降强调」参考。 |
| 滚动渐隐（11-02 新） | AGENTS.md 注：客户端改用 `@property` + `animation-timeline: scroll()` 驱动滚动边缘渐隐，7 段遮罩只作无此能力引擎的回退。 | 思路可参考；links 现无此需求，引入前查 Edge Dev 支持并帧测，待验证。 |
| 字重角色（11-02 新） | 4.4212.0：`font-medium` / `font-semibold` 先读控件 / 标题角色字重变量，再回落字面字重。 | 与 links「消费角色不写字面值」一致；links 字重角色是否需要单列，待令牌 ADR。 |
| 几何跟随（11-13 新） | [v4.16336.0 第七篇](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/docs/v4.16336.0/07-动效物理学与逐帧验证.md) 的元素选择高亮分三层过渡：几何 180ms `cubic-bezier(.16,1,.3,1)` 零过冲；绘制 200ms ease-out；退场 160ms 淡出，180ms 后移除。只有已存在的框才插值（`animate && !fresh`），新框直接落位；复用同一 DOM 节点换 key 实现 morph；减少动效时 `transition:none` 并直接移除。519 帧实测与曲线吻合（作者自测，未复验）。 | 采纳「指示物零过冲」「新元素不飞入」「先淡出后移除」，映射见 [motion-feel](motion-feel.md) B1–B4。官方这里用 left/top/width/height 过渡，links 仍按 UI-13 只动 transform；180 / 160ms 不进 links 常量。 |
| 弹簧调用点更正 | AGENTS.md：`SPRING_GENTLE`（380/18）在客户端没有调用点，是项目自补的预设；`600/30` 与 `1200/80/.1` 的调用点在 2.42304.2 已迁移（麦克风 / 语音条、file_viewer 宽度）；客户端共有 14 组弹簧。 | 不按预设名推断用途；links 弹簧沿用自己的 `--ease-spring-*`。 |
| hover 意图（11-13 新） | [第五篇 §5.7](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/docs/v4.16336.0/05-元素选择、组件名与上下文注入.md)：首次 hover 600ms 打开，离开留 200ms 宽限；本轮交互打开过一次后，切换零延迟（预热锁）；右键「钉住」后 hover 不再关闭；浮层定位完成前 `opacity:0` + `pointer-events:none`。 | 采纳行为（motion-feel C7 / C8）；Radix `delayDuration` / `skipDelayDuration` 已经覆盖，不搬毫秒数。 |
| 拖放（11-13 新） | 同篇 §5.8–5.11：dragenter / dragleave 用 Set 计数，捕获阶段在 dragend / drop / pointerdown 时兜底清空；DROPPED 态停 500ms 让退场播完；整条拖放链路只用 CSS transition / keyframes，不用弹簧；附件 View Transitions 先做能力检测，root group 时长设 0；多 chip 错峰 `50 + min(n-1,8)×30ms`。 | 采纳状态机与兜底清理（motion-feel C9）；View Transitions 归为改造（B5）；错峰入场按 UI-12 拒绝（B6）。 |
| 拖拽与工具条（11-13 新） | 第七篇 §7.6：浮窗拖拽 4px 死区、边界内缩 8px、角吸附 40px，松手 250ms ease-out 回弹（WAAPI）；工具条用 ResizeObserver 在 full → compact → minimal 三档间降级。 | 死区与回弹走 links `--ease-spring-drag`（motion-feel C3）；工具条降档 links 已有 `use-toolbar-layout`。 |
| 交互反馈 | 消息示例含发送失败重试、复制结果短暂反馈；[McpToolDecisionCard](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/code-examples/McpToolDecisionCard.tsx) 提供工具执行和授权的不同状态。 | 采纳可辨状态和恢复动作，保留 links 真实状态机。示例里的模拟数据 / 回调不证明生产可靠性。 |

## 同步记录

| 日期 | 锁定提交 | 变化（相对上一锁定） |
|---|---|---|
| 2026-10-24 | `c1f923ae` | 首读。 |
| 2026-11-02 | `2d56ab41`（2026-11-01） | 20 个提交。基线从 v2（`docs/v2/`，已标 historical）换到 Claude Desktop 3.6556.2 取证 + 4.29.0 / 4.4212.0 增量（[`docs/v4.29.0-4.4212.0/`](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/docs/v4.29.0-4.4212.0/README.md)，作者称为唯一现行基线；v1 / v2 保留为历史快照）。代码只改了 `cds-theme.css`（+525/−49）、`CdsButton.tsx`、`AttachmentCard.tsx`、`tailwind.config.js`；本文引用的 ChatComposer、useClaudeScrollPinning、ContainerResponsiveBar、ThinkingAccordion、ClaudeMotionPresets、DraggableSessionList、ChatMessageBubbles、StatusIndicators、McpToolDecisionCard 与旧锁逐字相同，只换链接 sha。数值修正：文字色、accent 蓝 / brand 陶土分角色、焦点环蓝、popover 两层纯投影、composer 圆角 12/14、尺寸随 `--cds-rem-scale`、按钮内边距 6/8/8/12、骨架 2s/105°/wave+lockstep、进度扫光、附件 View Transitions、窗口失焦去色、字重角色。README 把「逆向取证」改称「分析」，许可证仍 MIT。 |
| 2026-11-13 | `be395eb4`（2026-11-06，上游 HEAD） | 11 个提交，全是文档：新增当前卷 `docs/v4.16336.0/`（Side Browser，8 篇 + 合并版），新增 `code-examples/ElementInspectHighlight.ts` 并在 `src/index.ts` 导出；AGENTS.md 新增 §7 版本卷约定（每个客户端版本一卷，`check:tokens` 门禁）和「未经用户同意不开 PR」。旧锁引用的 code-examples、v1、v4.29.0 文档无变化。本次吸收：几何跟随三层过渡、hover 意图状态机、拖放状态机、拖放链路动效、拖拽死区与回弹，均进入 [motion-feel](motion-feel.md)。 |

## 截图来源与待验证项

| 参考入口 | 应观察的画面 | 本阶段证据 |
|---|---|---|
| [仓内 Storybook](https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/docs/claude-components-storybook.html) | 明暗组件、Composer、消息、浮层、加载 | 文件存在、部分源码已读；未运行、未截图。不能把 raw HTML 当完整产品截图。 |
| [项目公开演示站](https://openclaudeui.com)（仓 README 链接） | 页面全貌、空态及实际交互 | 仅核对入口，画面待验证。 |
| 用户后续提供的参考图 | 用户指定布局和密度 | 尚未提供；收到后记录出处 / 日期 / 状态，比较后修订建议，不反向改写已有来源事实。 |

下一阶段若取图，以 Edge Dev 在明确视口下记录 light/dark、空/加载/消息、hover/focus 状态。测得的参数只说明该版本重建站，不称为 Claude 官方参数。第三方逆向对比准确性、不同 DPR 字重与发丝线、连续动画节奏均为待验证。
