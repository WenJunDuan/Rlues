<!-- quantum-codegen playbook (前身独立 skill; 现为 quantum-codegen 的 mode 参考) -->

# quantum-codegen · mode=security

安全测试 skill。职责是在业务交付范围内验证静态安全清单和动态安全用例，重点覆盖认证、授权、数据域、
输入校验、敏感信息和依赖风险。本 skill **系统无关**：安全策略、路由、角色、数据权限、审计和命令来自
Convention Pack；运行环境只从 `runtime-env` 读取。

## 何时使用

- 新功能涉及用户输入、文件、权限、审批、数据域、外部接口或敏感数据。
- 需要在交付前提供安全测试证据。
- 需要验证依赖审计、静态 grep 和动态越权用例。

## 何时不使用

- 需要全面渗透测试、漏洞利用或扫描生产环境。
- 没有授权的目标、账号、角色或环境声明。
- 只需普通单测或 E2E；分别使用 `quantum-codegen` mode=unit 或 mode=e2e。

## 输入

1. 本次变更范围、接口/页面清单、角色矩阵和数据域规则。
2. Convention Pack：认证、授权、错误模型、审计、依赖审计和安全测试命令。
3. `runtime-env`：FE/BE/DB 启动、端口、探活 URL、teardown。
4. 安全检查清单和允许的测试账号声明；不得手写真实密码到 skill 文档。

## 工作流

1. 定位 Convention Pack。通用规则读 `references/security-test-contract.md`；若
   `scaffold_id=quantum` 或 pack 路径匹配 `quantum-front` / `quantum-backend`，再读
   `references/quantum-security-adapter.md`。
2. 运行 `python3 scripts/check_security_e2e_pack.py --frontend-pack <fe-pack> --backend-pack <be-pack> --profile security`。
   缺安全门禁、权限守卫或 runtime-env 时先停机补约定。
3. 读取 Convention Pack 与安全清单，限定测试范围。
4. 执行静态检查：硬编码密钥、危险日志、SQL/shell 拼接、权限注解、依赖审计。
5. 启动 `runtime-env` 声明的环境，执行动态用例：未登录、低权限、跨租户/跨数据域、非法输入。
6. 对每个问题记录复现步骤、影响、证据和修复建议；修复后重跑同一用例。
7. 输出安全测试报告；超出授权范围的问题转人工确认。

## 输出

- 静态检查命令与结果。
- 动态安全用例、账号角色、请求或页面步骤、预期与实际结果。
- 已修复问题、遗留风险、人工确认项。

## 铁律

- 默认 fail-closed；权限、数据域、输入校验不明确时不得放行。
- 不做未授权扫描，不攻击生产，不持久化真实凭证。
- 不猜账号、角色、端口或探活 URL；全部来自 Convention Pack 或 `runtime-env`。
- 安全报告只保留必要证据，脱敏 token、密码、个人敏感数据。

## PACE 集成

- design stage：确认安全验收标准和角色矩阵。
- runtime-verify stage：执行静态与动态安全测试。
- review stage：evaluator 把高风险问题作为 REWORK 输入。
- ship stage：交付报告列出安全结论和人工确认项。

## References

- `references/security-test-contract.md`: 安全测试 Convention Pack contract。
- `references/quantum-security-adapter.md`: quantum 前后端安全适配器。
- `scripts/check_security_e2e_pack.py`: security/e2e pack 与 runtime-env 完整性校验脚本。
