# 动效、手感与流畅度参考（motion-feel）

取证 2026-11-13。只读源码 / 文档（本地克隆 + GitHub raw / API），未安装、未运行任何参考仓。对应检查清单 C17–C24（[SKILL.md](../SKILL.md#可判定检查清单)）。

## 边界

- 先按 links 规则：UI-03 三档（关闭 = 存储「减少」/ `data-motion="reduce"`，开启 = `full`，高级 = `advanced`），UI-12 档位弹簧（`components/ui/motion.ts` 常量 + `styles/index.css` 的 `--ease-spring-*` `linear()`、`--motion-panel-ease`），UI-13 只过渡合成属性 + `observe-resize` 合帧 + `tools/perf/frames.mjs`（每次交互掉帧中位数 ≤2、p95 ≤20ms，`--reduce` 探针），UI-15 材质令牌。参考仓只提供思路。
- 参考仓的毫秒数、贝塞尔曲线和弹簧参数**不直接变成 links 常量**。要用时，先在现有时长档（fast 60 / snap 120 / segment 150 / base 200 / composer 220 / sheet 300 / press 360 / slow 450 / card 465ms）和现有曲线里找最近的一档；确实缺档时，写进 design 并帧测。
- 不新增 UI 库或动效库（framer-motion / motion / reanimated / canvas-confetti 之类）。参考仓写 `prefers-reduced-motion` 的地方，在 links 一律换成 `data-motion="reduce"` / `useReducedMotion()`，不加系统媒体查询分支。
- 裁定：**采纳** = 现有体系内可以直接照这个思路做；**改造** = 要换成 links 的令牌 / 档位 / 守卫，或要先帧测、先做试点；**拒绝** = 与 links 规则冲突或收益不够。

## 来源锁定

| 仓 | 锁定 | 本次读的内容 |
|---|---|---|
| open-claude-ui | `be395eb4`（11-06，上游 HEAD） | v4.16336.0 卷 05（hover 意图、拖放、View Transitions）、07（动效物理） |
| cindy | `ca5c0480`（11-13；上游已到 `fbb27143`，相关文件未复核） | engineering-conventions §7/§8、DESIGN §14.4、按钮按压 CSS、菜单高亮、globals.css 隐藏冻结段、Toast FLIP、mobile-render-performance、`dc0c6617` 抽屉修复 |
| PI-Desktop | `62a76875`（11-13） | reading anchor、history paging、`a86aa4e6` 侧栏记号、sessions.css、tokens.css、ADR 0149 |
| DEEIX-Chat | `a395739d`（10-31，本地克隆） | LoadingReveal、模型选择器形变 |
| pizza | `9ee7171d`（11-13，本地克隆） | Conversation 的 content-visibility 与定位修正 |
| Octop | `cd17e8d3`（11-11，本地克隆） | 侧栏宽度过渡（反例） |

## A. 质感：状态记号与静置面

| # | 技术 | 出处 | 用户得到 | links 映射 | 裁定 |
|---|---|---|---|---|---|
| A1 | 多个胶囊角标合成一个记号：6px 圆点 + 中性色数字；圆点颜色表达语义，数字保持正文对比度 | [PI a86aa4e6][pi-badge]、[sessions.css][pi-sessions] | 侧栏清爽，扫一眼就知道状态 | UI-11 / UI-14；颜色用 `text-ok` / `text-warn` 等语义令牌，数字 `tabular-nums`（UI-08） | **采纳**思路，像素与配色不照搬 |
| A2 | 运行中记号只播有限次（`animation-iteration-count: 2`），等待态静止 | [sessions.css][pi-sessions]（注释引 issue #1064） | 窗口空闲时不再持续出帧，笔记本不发热 | UI-13；`animate-quiet-dot` / `dot-pulse` 目前是 infinite | **改造**：用作状态记号时改成有限次或事件触发 |
| A3 | 事件驱动的呼吸：每有一次真实进展（文本或计数变化）播一次，没有进展时保持静止 | [cindy DESIGN §14.4][cindy-design] Red lines | 动起来就表示「正在产出」，不是装饰性心跳 | 流式状态条、`process-trace-steps`；用 key 重挂载触发 | **改造**，先在一个状态位试点 |
| A4 | 运行中的文案不做逐字扫光，只配一个小记号 | [PI ADR 0149][pi-adr149] | 长任务中文字一直清楚可读 | 思考 / 工具标签；与 C13 关闭档仍有静态文字一致 | **采纳** |
| A5 | 菜单只有一层高亮在行间滑动（transform + opacity）；鼠标在行间空隙时取最近一行；输入合帧到每帧一次 | [dropdown-menu-highlight.ts][cindy-menu] | 菜单悬停连续、不闪 | dropdown / context / select（`FLOAT_MOTION`、`POPUP_SURFACE`）；时长 snap，曲线 ease-out-expo；关闭档不滑；焦点仍归 Radix | **改造**：先试点一个菜单，改前后帧测 |
| A6 | 按压时只缩 `::before` 面层的 inset，热区和文字不动 | [cindy button.css][cindy-btn] | 按钮按下有实感，文字不抖 | links 已有 `active:scale-[.985]` + `button-press` + `icon-motion`（scale 是合成属性） | **拒绝**换实现：inset 不是合成属性；只吸收「热区不位移」这条检查 |
| A7 | 轻浮层退场比入场快，而且只淡出不缩放；模态关闭不倒放入场 | [cindy DESIGN §14.4][cindy-design] 原型表 | 关闭干脆，不会像被「吸走」 | `FLOAT_MOTION` / `MODAL_MOTION` 退场目前是 zoom-out + snap | **改造**：属于视觉改动，列为待用户确认项 |

## B. 效果与动画

| # | 技术 | 出处 | 用户得到 | links 映射 | 裁定 |
|---|---|---|---|---|---|
| B1 | 跟随几何的指示物（选框、滑块、选中条）用零过冲 expo 曲线，不用弹簧 | [ocu 07 §7.1/7.7][ocu-07] | 框始终贴合目标，不会看起来「没对准」 | UI-12 的弹簧只用于开合 / 回弹；ToggleGroup 滑块、设计包标注框、菜单高亮用 `ease-out-expo` | **采纳** |
| B2 | 新元素直接落位，已有元素才插值（`animate && !fresh`；或等两帧 rAF 后才开启过渡） | [ocu 07 §7.2][ocu-07]、[DEEIX morph][deeix-morph] | 首次打开时没有从左上角飞进来的残影 | 侧栏首开、段控滑块首挂、浮动工具条 | **采纳** |
| B3 | 复用同一个 DOM 节点、只换 key，让 transition 连续插值，代替淡出 + 淡入 | [ocu 07 §7.3][ocu-07] | 切换时是一段连贯的位移 | 页签指示条、选中高亮层 | **改造**：只用于单一指示物 |
| B4 | 退场先淡出，过 duration + 约 20ms 再移除节点；关闭档直接移除 | [ocu 07 §7.3–7.4][ocu-07] | 不残留、不闪断 | Radix Presence 已处理；手写的（`BROWSER_MARK_MS`、自绘标记）要自查 | **采纳** |
| B5 | 附件增删用 View Transitions：先做能力检测；`::view-transition-group(root)` 时长设 0；标签页隐藏或减少动效时直接更新 | [ocu 05 §5.11][ocu-05] | 附件补位连贯，整页不交叉淡化 | 已有 `ATTACHMENT_MOTION` / `ATTACHMENT_LIST_MOTION`；关闭档必须跳过 | **改造**：现有方案帧测不达标时再试点 |
| B6 | 多个 chip 错峰入场 `50 + min(n-1,8)×30ms` | [ocu 05 §5.11.3][ocu-05] | 一次放下多个文件时有节奏 | UI-12 禁止逐行入场 | **拒绝**；用户另行裁定后再说 |
| B7 | 骨架延迟揭示：加载超过阈值才出现占位，就绪后与正文交叉淡化 | [DEEIX LoadingReveal][deeix-reveal]、cindy §14.4（300ms 后静态占位） | 快请求不闪骨架；慢请求有过渡 | C13 / UI-10；`Skeleton` 加揭示阈值，只动 opacity | **采纳**；阈值取现有时长档，不搬 300 |
| B8 | 流式正文按词淡入（每词一个 span，消息级时间线） | [cindy DESIGN §14.4][cindy-design] stream-word fade | 正文是「浮现」出来的 | 每词一个 span 让长流 DOM 成倍增加，与帧测预算冲突 | **拒绝**（只在用户点名时再评估） |
| B9 | 列表重排用 FLIP；正在退场的项不参与位移 | [cindy ToastContainer][cindy-toast] | 置顶 / 取消置顶时行平移到新位置，不跳 | 侧栏会话置顶、看板列移动；只动 transform | **改造**：试点一处 |
| B10 | 侧栏宽度用 `width` 过渡 | [Octop Sidebar][octop-sidebar] | — | 违反 UI-13（links 用占位过渡 + 面板平移） | **拒绝** |

## C. 手感：按压、拖拽、跟手

| # | 技术 | 出处 | 用户得到 | links 映射 | 裁定 |
|---|---|---|---|---|---|
| C1 | 直接操作（拖分隔条、拖动跟随）不加缓动，跟手本身就是反馈 | [cindy DESIGN §14.4][cindy-design] Red lines | 指针和面板之间没有延迟 | split-divider、侧栏宽度、画布拖拽；links 已写明「拖动中不过渡宽高」 | **采纳**（检查项 C19） |
| C2 | 视觉位移和命中判定读同一个实时坐标；第一帧就用实时窗口几何，不等测量回调 | [cindy dc0c6617][cindy-drawer] | 抽屉跟手，第一帧尺寸就对 | Web 版做法：pointerdown 时缓存 rect；pointermove 只写 ref，每帧 rAF 写一次 CSS 变量或 transform；pointerup 再提交 store | **改造**（RN 写法不能照搬） |
| C3 | 4px 拖动死区；松手后用 250ms ease-out 回弹到落点（WAAPI），或按释放速度用弹簧 | [ocu 07 §7.6][ocu-07]、ocu AGENTS.md SPRING_SNAPPY | 点击不会误判成拖动；松手有落位感 | 回弹用现成的 `--ease-spring-drag`；死区写进组件常量，不改成全局令牌 | **改造** |
| C4 | 超出边界后带阻力拉伸（橡皮筋），松手回弹 | cindy DESIGN §14.4（mobile 图片查看器，系数 0.55） | 触屏拖到头时不是生硬地停住 | PWA 触屏抽屉 / 宽度拖拽；必须满足「触屏不抖」硬性验收 | **改造**，等移动端切片时再定 |
| C5 | 按下与松开之间按钮动作变了（例如发送↔停止），这次按压作废 | [cindy DESIGN §14.4][cindy-design] composer action | 不会误点到刚切换出来的动作 | Composer 发送 / 停止的 `IconSwap`；在 pointerdown 时记录动作身份 | **采纳** |
| C6 | 可反复切换的状态用 transition（能从当前值重新定向），不用 keyframes（会从头重播） | 同上（「CSS transitions retarget」） | 快速连点时动画不跳回起点 | `ICON_SWAP_MOTION` 是 keyframes，连点时自查 | **改造**，有问题再改 |
| C7 | hover 意图：首次停留 600ms 才打开，离开留 200ms 宽限；本轮交互打开过一次后，切到别的触发点零延迟；钉住后不随 hover 关闭 | [ocu 05 §5.7.1][ocu-05] | 鼠标扫过不刷屏；在相邻胶囊之间移动时切换流畅 | Tooltip / HoverCard 用 Radix 的 `delayDuration` + `skipDelayDuration`（就是预热锁）；数值取现有设置，不搬 600 / 200 | **采纳**行为 |
| C8 | 浮层定位完成前 `opacity:0` + `pointer-events:none` | [ocu 05 §5.7.2][ocu-05] | 浮层不会先闪在左上角 | 自绘浮层（partner-dock、canvas toolbar、引用卡）；Radix 已处理 | **采纳** |
| C9 | 拖放区：dragenter / dragleave 用 Set 计数；捕获阶段在 dragend / drop / pointerdown 时兜底清空；放下后成功态停 500ms，让退场播完 | [ocu 05 §5.9][ocu-05] | 拖放遮罩不会卡住不消失 | Composer / 文件面板的拖放遮罩 | **采纳** |

## D. 流畅度：渲染、滚动、读取

| # | 技术 | 出处 | 用户得到 | links 映射 | 裁定 |
|---|---|---|---|---|---|
| D1 | 阅读锚点记在可见的那个字符上（单个块内二分查找），不记消息顶部；块的身份用源码区间 + 文本校验 | [PI reading-anchor][pi-anchor] | 正在读的那行字不动 | `use-chat-scroll` / `use-follow-bottom` / `use-message-anchor`；侧栏开合、recap 收起、深链补页 | **改造** |
| D2 | 在绘制前修正滚动：React 提交后在 `useLayoutEffect` 里修；ResizeObserver 同时观察内容、滚动容器和每一行；连续 3 帧稳定才释放；分页读取同一时间只发一个，失败后不自动重试 | [PI history paging][pi-paging] | 补页、行高变化都不跳 | 同 D1；行高变化的来源有代码块展开、图片、`content-visibility` | **改造**（检查项 C20） |
| D3 | 长会话的行加 `content-visibility:auto` + `contain-intrinsic-size`；跳转后连续几帧修正位置 | [pizza Conversation][pizza-conv] | 长会话首屏和滚动更快 | links 流式中已关闭代码块的 c-v；整行启用必须与 D1/D2 一起上，用 240 条 fixture 帧测 | **改造** |
| D4 | 浮层身份稳定：常驻内容用 memo 包住；回调走一个稳定入口（ref 转发给当前拥有者）；用渲染计数做回归（外层刷新 1 → 0） | [cindy mobile perf][cindy-mrp]「任务列表」 | 拉出面板不卡；外层刷新不连带重渲整页列表 | 移动端 Sheet 里的会话列表、右侧面板、partner dock；用 React Profiler 或计数替身测 | **采纳**（检查项 C21） |
| D5 | 只订阅自己用到的那一片状态（宽度、字号分开订阅；启动门禁只看 hydrated） | 同上「尺寸变化只通知相关内容」 | 键盘弹起、侧栏开合时无关组件不重渲 | zustand selector、`observe-resize`；壳层布局 store 的消费者 | **采纳** |
| D6 | 内容相同的快照不重复发布（结构共享；比较全部字段） | 同上「相同快照不重复发布」 | 刷新后列表不重渲 | React Query 默认开着 `structuralSharing`；自建的 SSE store 要自查 | **采纳**检查 |
| D7 | 一次用户动作只取一次快照；同 key 的读取同一时间只发一个，共用结果 | [cindy §8.1][cindy-eng] | 翻页、切换不重复扫描、不重复请求 | React Query 对同 key 自动去重；非 RQ 的读取（harness 能力、SSE 补读）要自查 | **采纳**（检查项 C22） |
| D8 | 收到变化通知后的重读：先过滤无关通知 → 合并窗口 → 在途时只记一笔待刷新 → 失败不自己反复重读 → 最后一次变化一定读到 | [cindy §8.6][cindy-eng] | 事件风暴里界面不卡、不发热 | SSE 事件 → `invalidateQueries`；合并窗口写在代码里，不搬 250ms | **采纳** |
| D9 | 隐藏、离屏、卸载后停止读取和轮询；无限动画只用白名单 + `animation-play-state: paused` 冻结（不用 `animation:none`，否则会跳回起始帧）；桌面窗口关闭后台节流时，`visibilityState` 不可靠 | [cindy §8.3][cindy-eng]、[globals.css 冻结段][cindy-globals] | 后台不耗电，回到前台不跳帧 | `refetchIntervalInBackground` 默认 false；mesh 已经按 `data-paused` 冻结；其余 infinite（quiet-dot、skeleton-sweep、upload-*、spin）要接上；桌面壳要单独确认 | **采纳**（检查项 C23） |
| D10 | 常驻动画只挂在 HTML 包裹层的 transform / opacity 上，不挂在 SVG 上；图标旋转放在外层 span | [cindy §7][cindy-eng] | 不会每帧重绘、持续占用 CPU | `animate-spin` 现在直接加在 lucide svg 上（sonner、process-trace-steps、board-todo、steps-plan、harness-status、recheck） | **采纳**（检查项 C24） |
| D11 | 动效令牌是唯一来源，守卫禁止渲染层写死时长和曲线 | [cindy DESIGN §14.4][cindy-design] | 全站节奏一致 | links 已有 `motion-magic` 守卫 | 已具备，不新增 |

## 检查项 C17–C24

| ID | 通过条件 | 检查方式 |
|---|---|---|
| C17 按压反馈 | 按下后 ≤100ms 内（首个渲染帧）出现可见变化；只动 scale / opacity / 颜色；热区与文字不位移；关闭档仍有颜色或状态反馈。按下到松开之间按钮动作若已改变（发送↔停止），这次按压不触发新动作。 | `button-press` / `icon-motion` / `active:*` 源码；Performance 记录 pointerdown 后的首个样式变化帧；Composer 流式开始瞬间快速点击。 |
| C18 开合 | 浮层、模态、抽屉、侧栏的开合只过渡 transform / opacity（折叠用 `grid-collapse`）；退场时长 ≤ 入场；首次挂载直接落位，不从未测量的位置飞入；跟随几何的指示物不过冲。 | rg `transition-all`、`transition-\[(width|height|top|left)`；看 computed `transition-property`；`frames.mjs` 掉帧中位数 ≤2、p95 ≤20ms。 |
| C19 跟手拖拽 | 拖动中无缓动、无读写交错：rect 在 pointerdown 时缓存，pointermove 每帧最多写一次（rAF 合帧，写 ref / CSS 变量 / transform），pointerup 才提交 store 或持久化；视觉和命中判定读同一个坐标。 | Performance trace 中拖动段无 Forced reflow；每帧 React commit ≤1；帧测拖动场景。 |
| C20 滚动锚定 | 分页补历史、侧栏 / 右栏开合、折叠展开、流式结束后，正在阅读的文字屏幕位置偏移 ≤1px；贴底时保持贴底。修正发生在绘制前（`useLayoutEffect` / ResizeObserver 回调），不留到下一帧 rAF。 | 上滚阅读 → 开合侧栏 / 展开代码块 → 记录锚点字符 top 的差值；同视口内侧栏开合（UI-02）。 |
| C21 浮层身份稳定 | 浮层、抽屉、面板宿主的元素引用和回调在父级刷新时保持稳定；外层无关刷新时，浮层内列表重渲染 0 次；定位完成前不可见、不可点。 | React Profiler 或渲染计数用例（外层刷新、打开、关闭各记一次）；查自绘浮层的首帧。 |
| C22 单一在途读取 | 同一个 key 同时只有 1 个读取在途；通知风暴中，合并窗口内的读取次数不随通知数增长；在途时只记 1 笔待刷新；失败不自己反复重读；最后一次变化一定读到。 | 测试中计数 fetch / queryFn 调用；Network 面板记录突发事件下的请求数。 |
| C23 隐藏即停 | 标签页 / 窗口隐藏、面板折叠、离屏或卸载后：轮询 0 次，infinite 动画用 `animation-play-state: paused` 冻结（不用 `animation:none`），WebGL 停帧；恢复可见时最多补读 1 次。 | 在 hidden 状态下录 Performance：无帧、无请求；查 `refetchIntervalInBackground` 和自写定时器的可见性判断；桌面壳要另外确认窗口隐藏信号。 |
| C24 循环动效宿主 | 常驻 / 循环动画只放在 HTML 包裹层的 transform / opacity 上，不挂在 svg 上；状态记号只播有限次或由事件触发；关闭档下的静态形态仍能看出状态。 | rg `animate-spin` 等是否直接写在 lucide 组件上；Rendering 面板的 Paint flashing 检查有无每帧重绘。 |

## 用法

1. 改动涉及开合、按压、拖拽、滚动、浮层、轮询或订阅时，先在上表找对应技术，再按 C17–C24 判定。
2. 只看源码时，C17 / C19 / C20 标「运行待验证」。运行证据要写明 `frames.mjs` 的场景、轮数和掉帧数；用 `--reduce` 跑一次关闭档；改动前后各测一次。
3. 判为「改造」的技术，进 design 时写清楚对应 links 的哪个令牌 / 档位 / 组件，还有帧测或计数用例；不能在 design 里宣称「参考仓已证明」。

[ocu-05]: https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/docs/v4.16336.0/05-元素选择、组件名与上下文注入.md
[ocu-07]: https://github.com/Caho1/open-claude-ui/blob/be395eb4b783cad3148fd9a4ef7641a3d198dd52/docs/v4.16336.0/07-动效物理学与逐帧验证.md
[cindy-eng]: https://github.com/makecindy/cindy/blob/ca5c0480886921d2f46448aee197102e75b93e72/docs/dev-rules/engineering-conventions.md
[cindy-design]: https://github.com/makecindy/cindy/blob/ca5c0480886921d2f46448aee197102e75b93e72/docs/design-rules/DESIGN.md
[cindy-menu]: https://github.com/makecindy/cindy/blob/ca5c0480886921d2f46448aee197102e75b93e72/apps/desktop/src/renderer/components/ui/dropdown-menu-highlight.ts
[cindy-btn]: https://github.com/makecindy/cindy/blob/ca5c0480886921d2f46448aee197102e75b93e72/apps/desktop/src/renderer/components/ui/button.css
[cindy-globals]: https://github.com/makecindy/cindy/blob/ca5c0480886921d2f46448aee197102e75b93e72/apps/desktop/src/renderer/styles/globals.css
[cindy-toast]: https://github.com/makecindy/cindy/blob/ca5c0480886921d2f46448aee197102e75b93e72/apps/desktop/src/renderer/components/ui/toast/ToastContainer.tsx
[cindy-mrp]: https://github.com/makecindy/cindy/blob/ca5c0480886921d2f46448aee197102e75b93e72/apps/mobile/docs/mobile-render-performance.md
[cindy-drawer]: https://github.com/makecindy/cindy/commit/dc0c66172e9c4adc40a0b88c210282bd5aaef4ac
[pi-anchor]: https://github.com/vastsa/PI-Desktop/blob/62a76875e2de4a2b573f6bc48c79d0b31c920ff6/apps/desktop/src/lib/transcript-reading-anchor.ts
[pi-paging]: https://github.com/vastsa/PI-Desktop/blob/62a76875e2de4a2b573f6bc48c79d0b31c920ff6/apps/desktop/src/features/chat/transcript/hooks/useTranscriptHistoryPaging.ts
[pi-badge]: https://github.com/vastsa/PI-Desktop/commit/a86aa4e6922f7cd1e997259e835208cb667bb279
[pi-sessions]: https://github.com/vastsa/PI-Desktop/blob/62a76875e2de4a2b573f6bc48c79d0b31c920ff6/apps/desktop/src/styles/sessions.css
[pi-adr149]: https://github.com/vastsa/PI-Desktop/blob/62a76875e2de4a2b573f6bc48c79d0b31c920ff6/docs/adr/0149-calm-transcript-running-status-motion.md
[deeix-reveal]: https://github.com/DEEIX-AI/DEEIX-Chat/blob/a395739ddc4e74888960a608feb8b9307475177c/apps/web/shared/components/loading-reveal.tsx
[deeix-morph]: https://github.com/DEEIX-AI/DEEIX-Chat/blob/a395739ddc4e74888960a608feb8b9307475177c/apps/web/features/chat/components/sections/chat-model-picker-motion.tsx
[pizza-conv]: https://github.com/pizza-agent/pizza/blob/9ee7171d6be7b7788a19e8acb9389e6cc331abc4/apps/web/src/components/Conversation.tsx
[octop-sidebar]: https://github.com/TencentCloud/Octop/blob/cd17e8d3551a22e6757f11e030879420243c089f/dashboard/src/layouts/Sidebar.tsx
