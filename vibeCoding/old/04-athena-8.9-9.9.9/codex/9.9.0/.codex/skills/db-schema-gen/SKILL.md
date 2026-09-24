---
name: db-schema-gen
description: >-
  Use when a business feature needs database design artifacts in an existing
  scaffold. Reads the project's Convention Pack for naming, audit fields,
  tenancy, data-permission, migration, and validation rules, then produces two
  linked artifacts: a semantic table-design document and executable DDL SQL.
  It does not guess database engines, schemas, or migration commands.
---

# db-schema-gen

数据库 schema 生成 skill。职责是为业务功能产出两个分离但互相引用的产物：表设计文档和可执行
DDL SQL。本 skill **系统无关**：数据库类型、命名、审计字段、租户/数据权限、迁移方式、校验命令全部
来自 Convention Pack；执行环境只从 `runtime-env` 读取。

## 何时使用

- 新业务需要新增或调整表、字段、索引、约束、字典或初始化数据。
- 需要在后端代码生成前冻结数据库语义和 DDL。
- 需要 schema 评审 checkpoint 的机器可读证据。

## 何时不使用

- 只是读取线上数据；使用 `project-data-reader`。
- 目标项目没有声明数据库 Convention Pack 或 migration 规范。
- 需要直接改生产库；本 skill 只生成与验证交付物，不执行生产变更。

## 输入

1. 需求条目、领域实体、字段语义、权限归属和数据生命周期。
2. 数据库 Convention Pack：命名、类型映射、审计字段、软删、租户、索引、迁移、校验命令。
3. `runtime-env`：DB 启动命令、端口、探活 URL、teardown；可选本地 migration 验证命令。

## 工作流

1. 定位 Convention Pack。通用约定读 `references/backend-db-convention-pack.md`；若
   `scaffold_id=quantum-backend` 或目标 pack 路径匹配 `quantum-backend/docs/ai/convention-pack`，
   再读 `references/quantum-backend-adapter.md`。
2. 运行 `python3 scripts/check_backend_pack.py <convention-pack-dir> --profile db`，缺必需文件/模板先停机补约定。
3. 读取 Convention Pack，确定数据库方言、迁移目录、命名规则和安全默认项。
4. 产出表设计文档：业务语义、字段、类型、约束、索引、权限归属、数据域、兼容性说明。
5. 产出 DDL SQL：建表、索引、约束、注释、初始化数据或 migration 片段。
6. 互相引用两个产物，保持表名、字段名、索引名逐项一致。
7. 按 Convention Pack 或 `runtime-env` 声明运行 DDL 语法、migration 或本地 DB 验证。
8. 验证失败则修正文档与 SQL，重跑直到通过或标记 blocked。

## 输出

- `表设计.md`：面向评审的语义文档。
- `DDL.sql` 或项目声明的 migration 文件：可执行结构变更。
- schema 验证命令、结果、失败修复记录。

## 铁律

- 表设计文档和 DDL 必须分离，不能只交其中一个。
- 不猜数据库方言、默认字段、租户字段或权限字段。
- DDL 不得包含生产连接信息、真实密码或不可回滚的生产操作。
- 任何安全/数据域豁免必须显式写入设计文档并等待人工 checkpoint。

## PACE 集成

- design stage：冻结表语义和 schema 评审材料。
- impl stage：生成本地可验证的 DDL 或 migration。
- runtime-verify stage：按声明环境验证 schema 可执行。
- review stage：spec-compliance 核对需求字段、权限归属和 DDL 一致性。

## References

- `references/backend-db-convention-pack.md`: 后端 DB Convention Pack contract。
- `references/quantum-backend-adapter.md`: quantum-backend 的 DB 适配器。
- `scripts/check_backend_pack.py`: 后端 pack 结构和模板完整性校验脚本。
