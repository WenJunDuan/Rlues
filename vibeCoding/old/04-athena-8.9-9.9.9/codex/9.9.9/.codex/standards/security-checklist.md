---
effort: medium
attach_to_stages: [impl, review]
attach_to_subagents: [generator, reviewer]
---

<important if="writing or reviewing code that handles user input, secrets, network, files">
# Security Checklist · 安全自查清单

> impl + review 强制注入.
> 违反任一 P0 = REWORK; 任一 P1 = CONCERNS.

## 密钥与凭证 (P0)

- ❌ 硬编码 API key / DB password / token 在源码中
- ❌ 把密钥写入 git history (即使后续删除, history 仍可恢复)
- ❌ 在 console.log / print / 日志中输出密钥
- ✓ 用 env var (`process.env.API_KEY`) 或 secret manager (Vault / AWS Secrets Manager)
- ✓ `.env` 文件在 `.gitignore`, 提供 `.env.example` 占位
- ✓ 客户端代码 (browser-side JS) 永远不放服务端密钥 (它会暴露)

## 用户输入验证 (P0)

- ❌ 用户输入直接拼 SQL / shell 命令 / 文件路径
- ❌ HTML 注入 (没有 escape 就 innerHTML)
- ❌ 信任客户端发来的 ID / role / 价格 (服务端必须重新验证)
- ✓ 使用 parameterized query / prepared statement
- ✓ 使用 ORM 而非原始 SQL 拼接
- ✓ 输入 schema 验证 (zod / pydantic / joi)
- ✓ 文件路径校验 (拒绝 `../` 路径穿越)

## 命令注入防护 (P0)

```typescript
// ❌ 危险
const { exec } = require('child_process');
exec(`ls ${userInput}`);  // userInput="; rm -rf /" 就完了

// ✓ 安全 (用数组形式, 不进 shell)
const { execFile } = require('child_process');
execFile('ls', [userInput]);
```

```python
# ❌ 危险
import subprocess
subprocess.run(f"ls {user_input}", shell=True)

# ✓ 安全
subprocess.run(["ls", user_input])  # 默认 shell=False
```

## 权限检查 (P0)

- ❌ 路由只检查"用户已登录", 不检查"用户有权操作此资源"
- ❌ 用户 ID 来自请求 body / query (应该来自 session / JWT)
- ✓ 每个 mutation 端点先 authn (是谁) 再 authz (能做什么)
- ✓ 资源级权限 (用户 A 不能修改用户 B 的数据)
- ✓ admin 接口和普通接口分离, 不共用路由前缀

## CSRF / XSS / CORS (P1)

- CSRF: state-changing 请求带 CSRF token, 或仅接受 same-origin
- XSS: 用框架的自动 escape (React JSX 默认安全, Vue v-html 危险)
- CORS: `Access-Control-Allow-Origin` 不要 `*` (除非真公开 API), 用白名单

## 网络与依赖 (P1)

- HTTPS 必须 (生产环境不允许 http://)
- 依赖锁定: `package-lock.json` / `poetry.lock` / `requirements.txt` 必须提交
- 定期 `npm audit` / `pip-audit` / `safety check`
- 弃用 / CVE 包必须升级或替换

## 错误处理 (P1)

- ❌ 把 stack trace / SQL 错误 / 内部路径直接返回给客户端
- ✓ 返回脱敏错误 ("操作失败, 请稍后重试"), 详情写到服务端日志
- ✓ 日志中也不要记 raw password / token / 用户敏感数据

## 文件操作 (P1)

- 上传文件: 校验 MIME type + 文件大小 + 扩展名白名单
- 上传文件存储路径不要含用户控制部分 (用 UUID 重命名)
- 解压 zip / tar 防 zip slip (`../` 路径穿越)

## polish stage 额外扫描

polish_worker 在 review 后再扫一遍:
1. grep `console.log.*password|token|secret` → 删
2. grep `process.env\.[A-Z_]+` 是否有兜底 (`|| throw`)
3. 上传依赖是否锁定 (`package-lock.json` 存在且最新)

## 例外

- 测试代码 / fixture 中的 fake credentials 可接受 (但必须明显是 fake, 例如 "test-fake-key-xxx")
- demo / 文档示例可用 `<YOUR_TOKEN>` 占位
- 内网工具 / CLI 工具的安全要求可适当放宽 (但仍需输入验证)
</important>
