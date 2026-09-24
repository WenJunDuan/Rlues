---
type: db
slug: postgres
last_updated: ""
triggered_by_sprint: ""
---

# DB: Postgres

## 角色

主数据存储, 包括用户 / 业务实体 / 审计日志.

## 接口

### 对外提供

- 应用层通过 ORM (e.g. SQLAlchemy / Prisma) 访问
- 读副本走 read-only 连接

### 对外依赖

- (无外部, 是底层)

## 数据模型

[关键 schema / ER 图]

## 关键流程

- 主-从复制
- 备份: 每日全量 + 持续 WAL
- 高可用: failover via {tool}

## 配置项

- `DATABASE_URL=postgres://...`
- `DB_POOL_SIZE=20`
- `DB_READ_REPLICA_URL=...`

## 约束与例外

- 不支持: 全文搜索 (用 ElasticSearch 子系统)
- 限制: 单表 ≤ 100M 行 (超出分表)

## 演进历史 (引用 compound/)

- {date}: 选 Postgres 不用 MongoDB → `compound/decision-postgres-vs-mongo.md`
