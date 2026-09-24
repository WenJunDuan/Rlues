---
type: api
slug: rest
last_updated: ""
triggered_by_sprint: ""
---

# API: REST

## 角色

[本子系统在整个系统中的角色, 1-2 段]

## 接口

### 对外提供

- REST endpoints (列关键路径):
  - `POST /auth/login`
  - `GET /users/{id}`
  - ...

### 对外依赖

- Auth 子系统 (verify JWT)
- DB 子系统 (CRUD)
- Cache 子系统 (热数据)

## 数据模型

[关键数据结构, schema, mermaid ER 图]

## 关键流程

[本子系统的关键业务流, 一段或一图]

## 配置项

[环境变量 / 配置文件项]

- `API_PORT=8080`
- `JWT_SECRET=...`

## 约束与例外

- 不支持: ...
- 限制: ...

## 演进历史 (引用 compound/)

- {date}: 引入 RS256 → `compound/decision-jwt-rs256.md`
- {date}: 加 refresh token → `compound/decision-jwt-refresh.md`
