---
name: vibe-service
description: |
  服务分析命令。理解服务架构、业务逻辑、API 结构、运维信息。
  帮助快速了解陌生代码库。
---

# vibe-service Command

分析和理解服务架构。

## 使用方式

```bash
# 完整服务分析
vibe-service

# 分析特定模块
vibe-service src/auth/

# 仅架构分析
vibe-service --arch

# 仅 API 分析
vibe-service --api

# 仅业务逻辑分析
vibe-service --business
```

## 分析维度

### 1. 服务概览
```yaml
输出:
  - 技术栈识别 (框架、语言、数据库)
  - 目录结构说明
  - 依赖关系图
  - 入口点识别
```

### 2. 业务分析
```yaml
输出:
  - 核心业务流程
  - 领域模型
  - 业务规则
  - 数据流向
```

### 3. 架构分析
```yaml
输出:
  - 架构模式 (MVC/Clean/Hexagonal)
  - 模块划分
  - 依赖方向
  - 扩展点
```

### 4. API 分析
```yaml
输出:
  - 路由列表
  - 请求/响应结构
  - 认证方式
  - 错误处理
```

### 5. 运维分析
```yaml
输出:
  - 配置管理
  - 日志策略
  - 监控指标
  - 部署方式
```

## 执行流程

```
vibe-service
    │
    ├─→ 扫描项目结构                  # 1. 发现
    │   ├── package.json
    │   ├── 配置文件
    │   └── 源码目录
    │
    ├─→ service-analysis skill        # 2. 分析
    │   ├── 技术栈识别
    │   ├── 架构模式推断
    │   └── 业务逻辑提取
    │
    ├─→ knowledge-base skill          # 3. 知识库
    │   └── 检索项目文档
    │
    └─→ 生成服务报告                  # 4. 输出
        .ai_state/service-profile.md
```

## 输出报告

```markdown
# 📊 Service Analysis Report

## Overview
- **Name**: user-service
- **Type**: REST API
- **Stack**: Node.js + Express + PostgreSQL
- **Architecture**: Clean Architecture

## Directory Structure
```
src/
├── controllers/    # HTTP handlers
├── services/       # Business logic
├── repositories/   # Data access
├── models/         # Domain entities
├── middleware/     # Express middleware
└── utils/          # Helpers
```

## Tech Stack
| Category | Technology |
|:---|:---|
| Runtime | Node.js 20 |
| Framework | Express 4.x |
| Database | PostgreSQL 15 |
| ORM | Prisma |
| Auth | JWT + Passport |
| Validation | Zod |

## API Endpoints
| Method | Path | Description |
|:---|:---|:---|
| POST | /auth/login | User login |
| POST | /auth/register | User registration |
| GET | /users/:id | Get user by ID |
| PUT | /users/:id | Update user |

## Business Flows
1. **User Registration**
   ```
   Controller → Validation → Service → Repository → DB
   ```
2. **Authentication**
   ```
   Login → Verify → JWT → Response
   ```

## Key Insights
- Uses repository pattern for data access
- JWT tokens stored in httpOnly cookies
- Rate limiting on auth endpoints
- Soft delete for user data

## Recommendations
1. Add request logging middleware
2. Consider adding Redis for session cache
3. Add API versioning
```

## 与其他命令协作

```yaml
vibe-plan:
  - 规划前了解服务结构
  - 识别修改影响范围

vibe-dev:
  - 开发前快速上手
  - 理解代码组织

knowledge-base:
  - 补充项目文档
  - 更新技术决策
```
