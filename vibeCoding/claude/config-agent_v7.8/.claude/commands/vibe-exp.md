---
name: vibe-exp
description: |
  经验库操作命令。查询、添加、更新经验记录。支持经验检索、
  模式匹配、标签过滤。
---

# vibe-exp Command

管理经验库。

## 使用方式

```bash
# 列出最近经验
vibe-exp list

# 搜索经验
vibe-exp search "JWT"

# 按标签过滤
vibe-exp list --tag=auth

# 查看详情
vibe-exp show exp-001

# 添加经验
vibe-exp add "经验标题"

# 删除经验
vibe-exp delete exp-001
```

## 经验库结构

```
.ai_state/experience/
├── index.md              # 经验索引
├── learned/              # 自动学习的经验
│   ├── exp-001-jwt-refresh.md
│   └── exp-002-n1-query.md
├── manual/               # 手动添加的经验
│   └── exp-101-deploy.md
└── tags/                 # 标签索引
    ├── auth.md
    ├── performance.md
    └── security.md
```

## 经验格式

```markdown
---
id: exp-001
title: JWT 刷新令牌实现
date: 2025-01-23
source: auto-learn
tags: [auth, jwt, security]
relevance: high
---

# JWT 刷新令牌实现

## 问题
用户需要长期保持登录，但 JWT 不宜设置过长有效期。

## 解决方案
采用双令牌机制：
- Access Token: 15分钟
- Refresh Token: 7天

## 代码示例
```typescript
function generateTokenPair(userId: string) {
  // ...
}
```

## 注意事项
- Refresh Token 存储在 httpOnly cookie
- 实现 Token 轮换
- 考虑 Token 黑名单

## 相关经验
- [exp-002] Cookie 安全设置
- [exp-003] Token 黑名单实现
```

## 命令详情

### list - 列出经验

```bash
# 默认列出最近 10 条
vibe-exp list

# 指定数量
vibe-exp list --limit=20

# 按标签过滤
vibe-exp list --tag=auth

# 按时间范围
vibe-exp list --since=2025-01-01

# 按来源过滤
vibe-exp list --source=auto-learn
```

输出：
```markdown
📚 Experience Library (15 total)

| ID | Title | Tags | Date |
|:---|:---|:---|:---|
| exp-001 | JWT 刷新令牌实现 | auth, jwt | 01-23 |
| exp-002 | N+1 查询优化 | performance | 01-22 |
| exp-003 | React Hydration Fix | react, ssr | 01-20 |
```

### search - 搜索经验

```bash
# 关键词搜索
vibe-exp search "认证"

# 多关键词
vibe-exp search "JWT refresh token"
```

### show - 查看详情

```bash
# 查看完整内容
vibe-exp show exp-001
```

### add - 添加经验

```bash
# 交互式添加
vibe-exp add

# 带标题添加
vibe-exp add "部署检查清单"

# 指定标签
vibe-exp add "部署检查清单" --tags=devops,deploy
```

## 自动检索

在以下场景自动检索经验：

```yaml
触发时机:
  - vibe-plan 开始时
  - vibe-dev 开始时
  - 遇到错误时
  - 进入新领域时

匹配规则:
  - 关键词匹配
  - 标签匹配
  - 相似度计算
```

## 与其他命令协作

```yaml
/learn:
  - 提取经验存入库
  - 自动打标签

vibe-plan:
  - 规划前检索相关经验
  - 避免重复踩坑

vibe-dev:
  - 开发时推荐经验
  - 代码参考
```
