# Decision — quantum skill 合并 7→2 (9.9.2, design §13 / AC13)

## 结论
用户批准: 7 个 fullstack-delivery 公开 skill 合并为 2 个 hub, 留在 9.9.2, 不恢复旧 skill。
- scaffold-page-gen / scaffold-module-gen / db-schema-gen / unit-test-gen / security-test / playwright-e2e → **quantum-codegen** (mode=page|module|db|unit|security|e2e)
- project-data-reader → **quantum-data**

## 授权与范围
- pass1 判定此项为 EXTRA (无权威 design 依据); 用户 2026-07-13 拍板保留, 补 design §13 附录 + AC13 收编为正式合同, 命名亦经用户确认 (checklist I8)。
- skill 数 31→26 每端; CX config.toml 注册改为仅两 hub。

## 兼容/迁移政策 (详见 design §13.2)
- 旧 7 名**退役不设别名**; 历史注记 ("前身")/CHANGELOG 历史/迁移指令可提旧名, 活跃路由与调用面不可。
- 升级由 AI 引导迁移 (design §7.2 / AI-MIGRATION-GUIDE.md 场景二) 负责: 删用户 HOME 旧 7 skill 目录、装新 2、改 CX 注册。
- `.ai_state` 旧数据与 Convention Pack / Capability Manifest 契约 schema 不变。

## 测试矩阵 (design §13.3)
残留扫描 (validator) · 4 个 pack 校验脚本 · 6 个 F 系历史回归 (vibeCoding/scripts, 修 ROOT=repo 根后可执行; 3 个依赖外部 workspace/quantum fixture 属环境依赖, 如缺须上报不静默跳) · delivery-loop 调用面 marker · CX 注册精确两 hub。

## 取舍
- 合并收益: 热路径 hub + 渐进披露 playbook, 降低 skill 面积与注册漂移; 代价: 旧名硬断 (无别名), 由迁移指南消化。
- pass1 曾指 playbook 内残留旧名调用 → rework 已改为 mode 路由 (双端 references/ 0 残留)。
