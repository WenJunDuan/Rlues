---
name: ui-consistency
description: 编写、修改或审查 quantum-links 前端页面时，按既有 shadcn、主题令牌与三档动效检查 UI 一致性，给出组件级修复配方。用于会话、目录、设置及业务页面；不替代功能验收，不为其他产品套用本规范。
---
# links UI 一致性

本技能已同步至 2026-11-16 基线。目标：沿用 links 的交互与主题，页面组织精简、理工、干练，减少重复文字和容器装饰。规则只约束 links 页面；本文的 Markdown 表格用于说明，不是产品页面模板。

## 使用顺序

1. 确定涉及的路由、页面状态和现有公共组件。先读 [links 令牌速查](references/links-tokens.md)，再定位当前 links 源码；速查已更新至 2026-11-16 基准，覆盖 UI-15 材质、窗口外观与动效基建。
2. 新页面对照技能目录的工具栏顺序和交互，使用已有 `Page` / `ContentColumn` / `ListToolbar` / `SettingsSection`。**技能页是局部参照，不是已通过本清单的样板**，其正文标题等仍需检查。
3. 对照 [C01–C24 清单](references/checklist.md)给每项写「通过 / 违例 / 不适用 / 待验证」，附文件位置或运行证据；不适用写原因。只审代码时，截图、实际尺寸、滚动与键盘行为标待验证。
4. 改动涉及开合、按压、拖拽、滚动、浮层、轮询或订阅时，先读 [动效 / 手感 / 流畅度参考](references/motion-feel.md)，找到对应技术及其裁定，再逐项判 C17–C24；按 UI-13 用 `node tools/perf/frames.mjs` 在改前、改后各测一次，关闭档加 `--reduce`。C19 / C20 / C21 / C22 只审源码时标「运行待验证」或「计数待验证」。
5. 按 [修复配方](references/recipes.md) 与 [rules 草案](rules.md) 的 P0 → P1 → P2 修复本次授权范围；跨页面审查按 [全站检查计划](references/audit-plan.md)。不要因审查一个页面就重做全站主题。

取舍：用户明确要求优先；links 组件与令牌决定实现。外部参考分层（11-02），冲突按序：① links 规则 UI-01..UI-15；② Claude-UI [open-claude-ui](references/open-claude-ui.md)（锁 `be395eb4`）管会话 / agent 交互行为与配方（Composer、消息流、滚动钉底、思考折叠、工具授权、状态指示），MIT 但自述逆向重建，只借思路不抄代码；③ [Apple design](references/apple-design.md)（HIG）管新页面与改版的布局、间距、层级、材质与分层阴影、色彩用法、字体层级及按钮 / 列表 / 侧栏 / 工具栏 / 弹窗 / popover。[SpaceX](references/spacex-style.md) 只给留白 / 少文字方向。动效、手感、流畅度另见 [motion-feel](references/motion-feel.md)（来源 open-claude-ui / cindy / PI-Desktop / DEEIX / pizza / Octop，各自锁定提交，逐条给出采纳 / 改造 / 拒绝）；它排在 ①② 之后，不覆盖 Apple 的布局判断。用户 11-02 要的分层阴影与玻璃材质只经主题令牌、只用于控件 / 浮层层。外部色值、尺寸、弹簧参数不直接变成 links 常量，不新增 UI 库或动效引擎。


清单与修复配方分别见 [checklist](references/checklist.md)、[recipes](references/recipes.md)。
