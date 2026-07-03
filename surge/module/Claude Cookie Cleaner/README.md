# Claude Cookie Cleaner

Surge iOS 模块。只在 Claude / Anthropic 的 login 或 logout URL 上清理 `sessionKey` 和 `routingHint`。

## 文件

- `claude-cookie-clean.sgmodule`: 手机导入的 Surge 模块
- `claude_cookie.js`: 模块调用的脚本
- `README.md`: 使用说明

## 发布到 GitHub

1. 新建一个公开 GitHub 仓库。
2. 上传这 3 个文件。
3. 打开 `claude-cookie-clean.sgmodule`，把 `YOUR_GITHUB_USERNAME/YOUR_REPO` 改成你的仓库路径。

修改后应类似：

```ini
script-path=https://raw.githubusercontent.com/<你的用户名>/<仓库名>/main/claude_cookie.js
```

## 手机安装

1. Surge iOS 打开 `首页 -> 模块 -> 安装模块`。
2. 粘贴模块 Raw 地址。

```text
https://raw.githubusercontent.com/<你的用户名>/<仓库名>/main/claude-cookie-clean.sgmodule
```

3. 启用模块。
4. 确认 Surge 的 MITM 已开启，CA 证书已安装并信任。
5. 打开 Claude 的登录或登出页面触发清理。
6. 清理完成后关闭模块。

## 触发范围

会触发：

```text
https://claude.ai/login
https://claude.ai/api/auth/logout
https://claude.com/.../login
https://anthropic.com/.../logout
```

不会触发：

```text
https://claude.ai/chat
https://example.com/login
https://claude.ai/blog/logout-help
```

## 说明

Surge 模块负责配置 MITM、HTTP Engine 和脚本触发规则；`claude_cookie.js` 负责实际处理 Cookie。

手机实际只需要安装一个 `.sgmodule` Raw URL。脚本会由模块通过 GitHub Raw 自动拉取。

参考：

- Surge Module: https://manual.nssurge.com/others/module.html
- Surge Scripting: https://manual.nssurge.com/scripting/common.html
- Surge MITM: https://manual.nssurge.com/http-processing/mitm.html
