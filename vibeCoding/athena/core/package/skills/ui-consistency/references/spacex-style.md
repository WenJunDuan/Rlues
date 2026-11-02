# SpaceX 布局方向与 Apple 交互取舍

日期：2026-10-24。目标站：[SpaceX 官网](https://www.spacex.com)。本阶段仅取得部分官方页面的搜索索引文本：主站正文抓取为空，curl 请求返回 HTTP 403；浏览器工具没有可用 browser，调用 Edge Dev 被工具拒绝（`Computer Use was not approved to use Microsoft Edge Dev`），因此未取得视觉截图、computed CSS 或动效测量。不绕过该限制，不将历史印象写成今天实测。

## 可确认事实与设计建议

| 项 | 证据层级 | 对 links 的可执行建议 |
|---|---|---|
| 精简内容块 | 官方 [Mission 页面](https://www.spacex.com/about/mission) 的索引文本以短主题标题、简短说明、行动入口分段；这是文本结构证据，不是空间测量。 | 每组只承担一个任务；正文不重复顶栏标题，主操作直接给动作名；长解释移到确有需求的说明或详情。 |
| 工程数据结构 | 官方子域 [Falcon 9 页面](https://new.spacex.com/vehicles/falcon-9) 的索引含 Overview 与高度、直径、质量等标签 / 数值 / 单位；可确认信息组织，不能确认字体特性。 | 数字 `tabular-nums`，单位位置统一，状态与数据先于长介绍。等宽数字是用户要求，**不是本次测得的 SpaceX CSS**。其参数表不能成为 links 管理页面用表格的理由。 |
| 大留白、硬朗几何、单色 / 低饱和 | 用户 cc-9 明确指定；本次未取得官网截图，本站是否及如何实现这些视觉属性待验证。 | 用 Page 边距、无框分组、整齐边缘、现有细分隔建立结构；不新添装饰色；不为了“硬朗”覆盖按钮 / Composer 角色圆角。 |
| 少文字 | 用户方向 + Mission 文本层级启发，不等于官网所有页面都字少。 | 去掉重复导语、营销话术；状态、字段约束、权限及删除后果保留。一个空态一条原因、一个主行动。 |
| 克制动效 | 用户要求；官网时长、曲线、视频 / 滚动转场均未测量。 | links 沿用已有短反馈和两档开关；新页面不新增自动播放背景或逐行入场，不用猜测的 SpaceX 动效参数。 |

这是把用户指定的 SpaceX 方向转译成应用界面的方案，**不是对官网每个视觉参数的事实断言**。不把航天站营销首屏、视频大图、全屏段落照搬进会话或设置；也不以单色方向替换用户可选主题。

## Apple design：采用已核实的原则

已读 Apple 官方 [Layout](https://developer.apple.com/design/human-interface-guidelines/layout) 的 [Markdown 版本](https://developer.apple.com/design/human-interface-guidelines/layout.md)，以及 [Motion](https://developer.apple.com/design/human-interface-guidelines/motion) 的 [Markdown 版本](https://developer.apple.com/design/human-interface-guidelines/motion.md)。这些是原则来源，不给 links 增加 Apple 平台依赖。

| 官方原则摘要 | links 的检查落点 |
|---|---|
| 按重要性安排内容，用对齐、缩进、空间及分隔表达关系；渐进展示减少初始负担 | 主操作和关键状态可发现；设置用无框分组，低频动作进现有菜单，名称不能消失到只能猜图标。 |
| 布局适应窗口、文本尺寸与内容长度 | 同视口侧栏开合、最大字体、长中文名称都测；容器可用宽度优先。 |
| 动效服务反馈，简短、可选，不作为唯一信息通道；不阻塞后续操作 | 用现有 Button / ToggleGroup / 折叠状态；关闭后仍可辨运行与成功 / 失败。 |

10-24 只取上述原则。11-02 起 Apple 层扩为完整的布局与元素规则，见 [apple-design](apple-design.md)；用户要求的分层阴影与玻璃材质经令牌引入，SF Symbols 资产、新手势、系统动效策略仍不进入 links；动效仍按用户要求独立两档，主题字体仍按 links 当前源码。

## 截图来源与待验证项

| 待取证来源 | 画面 / 行为 | 记录要求 |
|---|---|---|
| `https://www.spacex.com` | 首屏、往下一个内容段、导航展开、主行动 hover / focus | 访问日期、完整 URL、视口 / DPR；区分视频帧与静态背景。不得使用搜索缩略图替代站点实测。 |
| `https://www.spacex.com/about/mission`、`https://new.spacex.com/vehicles/falcon-9` | 标题 / 数据 / 分隔 / 行动的实际层级 | 若重定向，记录最终 URL；测量字号、间距、圆角、边框与数字特性后再给具体参数。 |
| 用户参考图 | 用户认同的留白、几何、信息密度 | 尚未提供；应注明用户提供和原出处是否已知，不标成官网现行版本。 |

本阶段无截图附件。以上待验证影响参考精度，不妨碍依据用户明确方向和已核对 links 源码编写可执行草案；不能在第二阶段声称“SpaceX 像素一致”已验收。
