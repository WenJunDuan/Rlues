<!-- quantum-codegen playbook (前身独立 skill; 现为 quantum-codegen 的 mode 参考) -->

# quantum-codegen · mode=e2e

全栈交付专用 Playwright 封装。职责是把需求、契约和运行环境声明转成可复跑 E2E 测试与证据。
本 skill **系统无关**：浏览器操作复用既有 `playwright` skill；应用命令、端口、账号、URL 全部来自
Convention Pack 或 `runtime-env`，不复制 Playwright 官方细节。

## 何时使用

- FE、BE、DB 已能按 `runtime-env` 启动，需要验证真实业务流。
- 需要把关键用户路径、权限路径和错误路径写成可复跑 E2E。
- 需要截图、trace、视频或测试报告进入 `runtime-verify` 和交付报告。

## 何时不使用

- 只需单元级行为验证；使用 `quantum-codegen` mode=unit。
- 运行环境、测试账号或探活 URL 未声明。
- 需要学习 Playwright API 细节；调用既有 `playwright` skill 或官方文档。

## 输入

1. 需求验收标准、关键页面、API 契约和数据准备要求。
2. Convention Pack：E2E 目录、选择器约定、账号/角色声明、数据隔离和测试命令。
3. `runtime-env`：FE/BE/DB 命令、端口、探活 URL、teardown。

## 工作流

1. 定位 Convention Pack。通用规则读 `references/e2e-convention-pack.md`；若
   `scaffold_id=quantum` 或 pack 路径匹配 `quantum-front` / `quantum-backend`，再读
   `references/quantum-e2e-adapter.md`。
2. 运行 `python3 scripts/check_security_e2e_pack.py --frontend-pack <fe-pack> --backend-pack <be-pack> --profile e2e`。
   缺 runtime-env、页面挂载或测试报告约定时先停机补约定。
3. 读取 `runtime-env`，按声明顺序启动 DB、BE、FE，并等待探活 URL 成功。
4. 读取 Convention Pack，确认 E2E 文件位置、选择器约定和测试数据策略。
5. 使用既有 `playwright` skill 编写可复跑测试；测试来源必须是需求和契约。
6. 执行 E2E 命令，保存截图、trace、视频或报告路径；失败则读证据、修复、重跑。
7. 执行 teardown，释放端口、进程、容器或临时数据。
8. 把结果写入 `runtime-verify` 证据和交付报告输入。

## 输出

- 可复跑的 Playwright E2E 测试文件。
- 启停命令、探活结果、测试结果、截图/trace/报告路径。
- 覆盖需求清单和剩余未覆盖原因。

## 铁律

- 不猜环境；没有 `runtime-env` 不启动服务。
- 不复制 Playwright 官方细节；浏览器调试和 API 用法交给既有 `playwright` skill。
- E2E 必须可复跑，禁止只做一次性手工点击。
- 测试数据必须可隔离、可清理，不污染共享环境。

## PACE 集成

- runtime-verify stage：启动全栈环境，执行 E2E，保存证据。
- review stage：spec-compliance 核对 E2E 是否覆盖原始需求和契约。
- ship stage：交付报告引用 E2E 结果和人工未确认项。

## References

- `references/e2e-convention-pack.md`: E2E Convention Pack contract。
- `references/quantum-e2e-adapter.md`: quantum 前后端 E2E 适配器。
- `scripts/check_security_e2e_pack.py`: security/e2e pack 与 runtime-env 完整性校验脚本。
