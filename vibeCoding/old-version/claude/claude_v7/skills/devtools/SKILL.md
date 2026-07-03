---
name: devtools
description: 浏览器调试测试，仅用户要求时使用
mcp_tool: chrome-devtools
---

# DevTools Skill (Chrome DevTools)

浏览器调试测试，**仅当用户明确要求时使用**。

## ⚠️ 重要

**默认不执行测试**。遵循铁律：除非用户明确要求，不测试、不编译、不运行。

## 使用场景

仅当用户说以下内容时触发：
- "帮我测试一下"
- "运行测试"
- "检查浏览器"
- "调试页面"

## 调用流程

```javascript
// 1. 连接浏览器
chrome_devtools.connect()

// 2. 执行操作
chrome_devtools.navigate("http://localhost:3000")
chrome_devtools.click("#submit-btn")
chrome_devtools.type("#email", "test@example.com")

// 3. 截图/检查
chrome_devtools.screenshot()
chrome_devtools.evaluate("document.title")

// 4. 收集结果
// 5. 寸止.feedback() 报告结果
```

## 常用操作

### 导航
```javascript
chrome_devtools.navigate("url")
chrome_devtools.reload()
chrome_devtools.back()
```

### 交互
```javascript
chrome_devtools.click("selector")
chrome_devtools.type("selector", "text")
chrome_devtools.select("selector", "value")
```

### 检查
```javascript
chrome_devtools.screenshot()
chrome_devtools.evaluate("js expression")
chrome_devtools.getHTML("selector")
```

### 网络
```javascript
chrome_devtools.getNetworkRequests()
chrome_devtools.waitForRequest("url pattern")
```

## 测试结果报告

测试完成后通过寸止报告：

```javascript
寸止.feedback({
  summary: "测试完成",
  results: [
    "✅ 登录流程正常",
    "✅ 表单验证正确",
    "❌ 提交按钮样式异常"
  ],
  screenshots: ["login-page.png", "error-state.png"]
})
```

## 降级方案

chrome-devtools不可用时 → 提供手动测试步骤指导
