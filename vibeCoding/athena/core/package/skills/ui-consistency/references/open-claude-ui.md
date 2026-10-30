# open-claude-ui：可迁移的 UI 细节

来源：[Caho1/open-claude-ui](https://github.com/Caho1/open-claude-ui)。2026-10-24 读取公开仓库，锁定 commit `c1f923ae0051a871941b98a0e2e3183a545e6a85`；源码只下载到临时目录用于阅读，没有安装或运行。它是第三方重建项目，不是 Anthropic 官方规范。作者的“逆向还原”“生产级”“物理常数已验证”等声明未独立复验，不能当作本次验收证据。

下表区分「该仓源码 / 文档事实」与「links 采纳建议」。源码与旧说明不同的数值分别记录，不拼成一套所谓官方参数。

| 维度 | 已核对的参考细节及出处 | links 的取舍 |
|---|---|---|
| 布局 | [ContainerResponsiveBar](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/code-examples/ContainerResponsiveBar.tsx) 按命名容器调整工具栏：较窄时隐去次要文字，主动作保留；[v1 设计章节](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/docs/v1/01-设计哲学与设计令牌体系.md) 描述侧栏、中心聊天列、浮层的层级。 | 采纳“量可用容器”的方法；仍用 links 的 ContentColumn，不搬其 320/384/480/576 阈值或侧栏尺寸。 |
| 间距 | [ChatComposer](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/code-examples/ChatComposer.tsx) 外层 px-4，壳内 .875rem padding、gap-y-2，工具组 gap-1.5；附件和工具栏与正文分区。 | 抄分组关系，不复制像素；links 外层 Page、内部组件已有间距。 |
| 字号 / 字体 | 同一 ChatComposer 的正文 15px、工具文字 text-xs，消息组件正文也为 15px；[设计章节 §1.5](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/docs/v1/01-设计哲学与设计令牌体系.md) 区分界面、阅读、代码角色及 tabular-nums。 | 采纳角色与数字对齐；链接到 links 字体槽和 text-* 角色，不导入专有字体，不照搬其光学缩放。 |
| 色彩层级 | [cds-theme.css](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/code-examples/cds-theme.css) 用 surface-0…3 区分底层到浮层；浅色依次为 #f9f9f7、#fcfcfb、白、白，深色为 #0b0b0b、#151515、#1a1a19、#20201f；强调色与中性色分工。 | 采纳微差表面和强调稀少；实际颜色只从 links `--ql-*` 来。浅色同值表面并非靠色差就能完全区分。 |
| 圆角 | 同一 CSS 的 Composer=20px、Dialog=16px；v1 说明与消息示例写气泡18px，但当前 CSS 气泡令牌已用 radius + 缩放量公式。 | 不宣称全库气泡固定18px。links 使用角色圆角；当前陶土下 composer20 / bubble18 是其自身公式结果。 |
| 阴影与边缘 | 同一 CSS 提供多档投影、Composer 常态 / hover / focus 和浮层内外轮廓；v1 章节讨论不重复闭合边框。 | 采纳按层级分配投影；links 已有 shadow-popover / shadow-composer，勿叠一份 border 和 glow。 |
| 图标 | v1 §1.5 讨论行内垂直对齐、图标尺寸档；[ChatComposer](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/code-examples/ChatComposer.tsx) 发送 SVG 有 aria-label，但工具项也使用 emoji / 文字符号。 | 采纳尺寸 / 对齐 / 名称原则，不照搬示例 emoji；links 用 Lucide 和 icon-inline。 |
| 动效 | [ThinkingAccordion](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/code-examples/ThinkingAccordion.tsx) 与消息示例用 grid 行高展开；[ClaudeMotionPresets](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/code-examples/ClaudeMotionPresets.ts) 提供不同交互用途的弹簧配置。 | 采纳“反馈随动作”的区分，复用 links grid-collapse / tw-animate-css；本阶段不引入弹簧库、音效或环境发光。 |
| 输入框 | [ChatComposer](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/code-examples/ChatComposer.tsx) 输入区最小3rem、最大24rem，field-sizing 自适应；空文本且无附件时禁发送；composition、isComposing、229 防止候选确认误发，Shift+Enter 留换行。 | 采纳行为检查；links 现有 Composer 接管实现，保留自己的模型、附件、权限状态。该示例的 hover/focus 实际效果仍需运行验证。 |
| 侧栏 | [DraggableSessionList](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/code-examples/DraggableSessionList.tsx) 分固定 / 最近会话，具选中态、重排指示与 Alt+上下键；PointerMove 中有4px拖动阈值。 | 只对 links 已有拖拽能力检查误触 / 键盘路径；不据此新增拖拽功能或强制4px阈值。 |
| 消息流 | [ChatMessageBubbles](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/code-examples/ChatMessageBubbles.tsx) 区分用户气泡和无框助手正文，操作组支持 hover / focus-within；[useClaudeScrollPinning](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/code-examples/useClaudeScrollPinning.ts) 含150ms输入冷却、40px底部容差和离底120px返回入口。 | 采纳“不抢滚动”和可找回最新消息，不把这些阈值定为 links 硬规则；示例没有证明长流式场景的运行正确性。 |
| 空态 | 已读设计章节列出问候语显示字号，示例 Composer 提供输入占位。检查的上述核心组件未形成统一的“首次空 / 无匹配 / 无权限 / 失败”页面状态规范。 | 空态结论有限，完整首屏 / 空态视觉待验证；links 用自己的 EmptyState 与技能页差异文案，不编造参考页截图。 |
| 加载态 | [StatusIndicators](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/code-examples/StatusIndicators.tsx) 有状态点、思考点、扫光骨架和文字 label；仓内说明的周期存在版本差别。 | 采纳状态类型，沿用 links Skeleton / 助手标记及两档动效；这里的6px状态点不是6px滚动条。 |
| 交互反馈 | 消息示例含发送失败重试、复制结果短暂反馈；[McpToolDecisionCard](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/code-examples/McpToolDecisionCard.tsx) 提供工具执行和授权的不同状态。 | 采纳可辨状态和恢复动作，保留 links 真实状态机。示例里的模拟数据 / 回调不证明生产可靠性。 |

## 截图来源与待验证项

| 参考入口 | 应观察的画面 | 本阶段证据 |
|---|---|---|
| [仓内 Storybook](https://github.com/Caho1/open-claude-ui/blob/c1f923ae0051a871941b98a0e2e3183a545e6a85/docs/claude-components-storybook.html) | 明暗组件、Composer、消息、浮层、加载 | 文件存在、部分源码已读；未运行、未截图。不能把 raw HTML 当完整产品截图。 |
| [项目公开演示站](https://openclaudeui.com)（仓 README 链接） | 页面全貌、空态及实际交互 | 仅核对入口，画面待验证。 |
| 用户后续提供的参考图 | 用户指定布局和密度 | 尚未提供；收到后记录出处 / 日期 / 状态，比较后修订建议，不反向改写已有来源事实。 |

下一阶段若取图，以 Edge Dev 在明确视口下记录 light/dark、空/加载/消息、hover/focus 状态。测得的参数只说明该版本重建站，不称为 Claude 官方参数。第三方逆向对比准确性、不同 DPR 字重与发丝线、连续动画节奏均为待验证。
