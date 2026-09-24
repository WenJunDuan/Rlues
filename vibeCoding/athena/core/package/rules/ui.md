---
paths:
  - "**/*.{tsx,jsx,vue,svelte,html,css,scss}"
---

# UI（仅前端；后端 / CLI / 库跳过）

## P0 · 可访问性
- 按钮、链接有可读 label；纯图标按钮有 `aria-label`；input 关联 label。
- 对比度：正文 ≥4.5:1，大字 ≥3:1（WCAG AA）；不单靠颜色传达信息。

## P1
- 键盘可达全部交互元素；focus 可见，不 `outline: none`。
- 异步交互显式处理 loading / success / error / empty 四态；loading 时禁重复提交。
- 表单错误显示在字段旁；错误消息说明发生了什么、该怎么办。
- 颜色、间距、字号用项目 design token；间距 8px 网格；字号 ≤5 级。
- 首屏 LCP <2.5s，INP <200ms；大图 lazy + `srcset`；>50ms 任务移出主线程。
- 一页一个核心任务；长表单分步。

## 例外
内部工具保留键盘导航与对比度，其余可放宽；原型 / POC 不强制；第三方组件库样式可保留。
