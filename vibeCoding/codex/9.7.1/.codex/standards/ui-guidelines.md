---
effort: medium
attach_to_stages: [design, impl, review]
attach_to_subagents: [generator, reviewer, architect]
---

<important if="building or reviewing UI">
# UI Guidelines · 用户界面规范

> 适用于所有 frontend / UI / 用户交互层代码.
> 后端服务 / CLI 工具 / 库 → **不适用**, 跳过.

## 设计原则 (Stallman 三原则)

1. **直接可达**: 用户做常用操作不超过 2 次点击
2. **状态可见**: 任何 async 操作显示 loading / success / error 状态
3. **错误可解释**: 错误消息说明 "发生了什么 + 该怎么办", 不是 "Error 500"

## 信息架构

- 单页 → 单一职责. 一个页面 = 一个核心任务
- 关键信息 viewport 内可见, 不要折叠在 "more" 按钮里
- 复杂表单分步进行 (multi-step wizard), 不要一屏 30 个字段

## 视觉一致性

- 颜色: 用 design token (`--color-primary`, 不是 `#0099ff`)
- 间距: 用 8px 网格倍数 (4, 8, 16, 24, 32, 48)
- 字号: 限制在 5 个层级 (h1/h2/h3/body/caption)
- 圆角 / 阴影 / 边框: 项目统一一个规范, 不要每个组件自己定

## 可访问性 (a11y)

### P0 (硬性, 违反 = REWORK)
- 所有 button / link 必须有可读 label (无 label 的 icon button 必须有 `aria-label`)
- 所有 input 必须关联 label (`<label for=...>` 或 wrap)
- 颜色对比度: 普通文字 ≥ 4.5:1, 大字号 ≥ 3:1 (WCAG AA)
- 不靠颜色单独传达信息 (色盲友好)

### P1 (重要, 违反 = CONCERNS)
- 键盘导航完整 (所有交互元素可 Tab 到达)
- focus 状态明显 (`outline` 不能 `display: none`)
- 表单验证错误显示在字段附近, 不是 alert popup

## 状态处理

每个异步交互必须显式处理 4 个状态:
- `loading`: 显示 spinner / skeleton, 禁用提交按钮防重复
- `success`: 显式反馈 ("已保存" / "已发送")
- `error`: 显示原因 + 重试入口
- `empty`: 空数据状态有引导 ("还没有 X, 点击这里创建")

## 性能

- 首屏 LCP < 2.5s (P1)
- 交互响应 INP < 200ms (P1)
- 图片 lazy load, 大图用 `srcset` 响应式
- 不在主线程跑长任务 (> 50ms 用 web worker)

## 项目自定义

具体的 design token / 颜色值 / 字体 / 圆角值 应该在项目自己的 `design-tokens.json` 或同等文件定义.
本规范只定义**原则**, 不定义具体值.

## 例外

- 内部工具 / 后台管理界面可降低 a11y 要求 (但仍需满足键盘导航 + 颜色对比)
- 原型 / POC 不需要全部 a11y
- 第三方组件库 (Ant Design / shadcn) 的样式可保留, 不强制 token 化
</important>
