---
name: architect-doc
description: 维护 .ai_state/architecture/ 长效架构档。Refactor/System 完成后需要更新架构档时触发。
---

# /architect-doc — 架构现状档维护 (v9.6.4 Sprint D 新)

## 触发时机

| 时机 | 强制度 | 责任 |
|---|---|---|
| System 路径 polish 完成、ship 前 | **强制** | 主 agent |
| Refactor 路径改动 ≥ 5 文件 | **强制** | 主 agent |
| 用户显式 `/architect-doc update {type}-{slug}` | 触发 | 主 agent |
| Feature 路径完成 (新增 endpoint / 新数据模型) | 可选 | 主 agent 判断 |
| athena-init 首次 | 创建 ARCHITECTURE.md 初版 | athena-init |

## delivery-gate 联动

Refactor / System (≥ 5 文件) + stage=ship 时, `delivery-gate` hook 检查:

1. 读 `_index.path` 和本 sprint 改动文件数 (从 evidence.yaml)
2. 若满足强制条件:
   - 检查 `architecture/ARCHITECTURE.md` mtime ≥ 本 sprint 开始时间
   - 检查改动涉及的子系统对应 `{type}-{slug}.md` mtime ≥ 本 sprint 开始时间
3. 不满足 → block + 提示 `/architect-doc update`

## 工作流

### 创建初始档 (athena-init 顺带)

athena-init 时, 主 agent:
1. 检测项目是否已有 `README.md` / `docs/architecture/` / `ARCHITECTURE.md`
2. 是 → 引导用户从中提取关键信息 → 写 `.ai_state/architecture/ARCHITECTURE.md` 初版
3. 否 → 询问用户基本架构问题 (用什么 DB / API 风格 / 部署方式) → 生成最简版

### 更新已有档

1. 主 agent 读当前 sprint 的 `design.md` + git diff
2. 判断改动涉及哪些子系统 (heuristic: 检测 `src/{module}/` 路径模式)
3. (可选) spawn 只读 `architect`，使用用户有效模型/effort，返回提案
4. 主 agent apply patch + 更新 mtime
5. 更新 `_index.pointers.latest_architecture_update`

### 新增子系统档

System 路径引入新子系统时:
1. 主 agent 询问用户 type (从枚举选):
   - `api` / `db` / `auth` / `cache` / `frontend` / `backend`
   - `infra` / `messaging` / `monitoring` / `cli` / `lib`
2. 创建 `architecture/{type}-{slug}.md` (从模板)
3. 更新 `ARCHITECTURE.md` 索引段

## 文件结构

```
.ai_state/architecture/
├── ARCHITECTURE.md         # 总入口 + 索引 (强制存在)
└── {type}-{slug}.md        # 子系统档 (按需创建)
```

例:
- `api-rest.md`
- `db-postgres.md`
- `auth-jwt.md`
- `cache-redis.md`
- `frontend-react.md`
- `infra-k8s.md`

## 不要做

- 不写演进历史 (那是 git log + `compound/decision-*.md`)
- 不写实现细节 (那是源码)
- 不重复 design.md (design 是某次 sprint 的设计, architecture 是当前现状)
- 不写未实现的设想 (那是 roadmap)

## 与 design.md / compound 的关系

```
design.md (sprint 一次性, 写"这次要改 X")
    ↓ polish 后、ship 前
architecture/{type}-{slug}.md (长效, 写"X 现在长这样")
    ↓ 重大决策同步
compound/decision-*.md (永久, 写"为什么这样选")
```

三者各司其职, 不冗余.

## archive 机制 (借 OpenSpec /opsx:archive)

已完成 sprint 按既有归档规则进入 `.ai_state/sprints/archive/{YYYY}/{slug}`，只在显式检索时读取。耐久 compound/decision 保留事实与有效状态，不能因季度轮换覆盖新决定；不新建第二归档树。

`architecture/` **不归档** (永远是现状).

## 模板

见 `~/.agents/skills/pace/templates/architecture/`
