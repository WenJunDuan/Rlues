---
paths:
  - "**/*.{ts,tsx,js,jsx,mjs,cjs,py,go,rs,java,kt,rb,php,cs,swift,sql,sh}"
  - "**/*.{yaml,yml,toml,json}"
  - "**/.env*"
---

# Security

## P0
- 密钥不进源码、git 历史、日志；用环境变量或 secret manager；`.env` 进 `.gitignore`，提供 `.env.example`；客户端代码不放服务端密钥。
- 用户输入不拼 SQL、shell、路径、HTML：参数化查询、schema 校验（zod / pydantic）、拒绝 `../`、输出转义。
- 子进程用数组参数（`execFile(cmd, [arg])`、`subprocess.run([...])`），不用字符串 + shell。
- 服务端重验客户端给的 ID / role / 价格；用户 ID 取自 session / token，不取自 body。
- 每个写接口先 authn 再 authz，做到资源级；admin 路由与普通路由分开。

## P1
- CSRF token 或仅同源；XSS 靠框架转义（`v-html` / `dangerouslySetInnerHTML` 要审）；CORS 白名单，不用 `*`。
- 生产只 HTTPS；锁文件提交；定期 audit，CVE 依赖升级或替换。
- 对外错误脱敏，详情进服务端日志；日志不记密码、token、敏感个人数据。
- 上传：校验 MIME、大小、扩展名；存储名用 UUID；解压防 zip slip。

## 例外
测试 fixture 的假凭证要一眼可辨（`test-fake-key-…`）；文档示例用 `<YOUR_TOKEN>`。
