# Service Analysis Skill

## 概述
服务理解与分析技能，用于快速理解和加载服务上下文，包括服务概览、业务逻辑、架构分析和运维协议。

## 核心能力

### 1. 服务概览 (service-overview)
```yaml
分析内容:
  - 服务名称和定位
  - 核心功能列表
  - 技术栈信息
  - 依赖服务清单
  - 团队负责人

输出: 服务概览卡片
```

### 2. 业务逻辑 (service-business)
```yaml
分析内容:
  - 业务流程图
  - 核心用例
  - 数据模型
  - 业务规则
  - 边界条件

输出: 业务理解文档
```

### 3. 架构分析 (service-architecture)
```yaml
分析内容:
  - 系统架构图
  - 模块划分
  - 接口定义
  - 数据流向
  - 关键路径

输出: 架构分析报告
```

### 4. 运维协议 (service-ops)
```yaml
分析内容:
  - 部署流程
  - 配置管理
  - 监控告警
  - 故障处理
  - SLA 要求

输出: 运维手册摘要
```

## 服务上下文结构
```
.service-context/
├── index.md                 # 服务索引
├── {service-name}/
│   ├── overview.md          # 服务概览
│   ├── business.md          # 业务逻辑
│   ├── architecture.md      # 架构文档
│   ├── api.md               # API 文档
│   ├── data-model.md        # 数据模型
│   └── ops.md               # 运维协议
└── shared/
    ├── glossary.md          # 术语表
    └── conventions.md       # 约定俗成
```

## 服务概览卡片格式
```markdown
# 服务: {service-name}

## 基本信息
| 属性 | 值 |
|:---|:---|
| 名称 | user-service |
| 定位 | 用户管理核心服务 |
| 负责人 | @team-user |
| 技术栈 | Node.js + PostgreSQL |

## 核心功能
- 用户注册/登录
- 用户信息管理
- 权限控制

## 依赖服务
- auth-service: 认证服务
- notification-service: 通知服务

## 关键指标
- QPS: 10000
- 延迟 P99: <100ms
- 可用性: 99.9%
```

## 使用场景

### 1. 开发新功能前
```yaml
流程:
  1. /vibe-service load user-service
  2. 自动加载:
     - overview.md (了解服务定位)
     - business.md (理解业务逻辑)
     - architecture.md (了解现有架构)
  3. 输出服务上下文摘要

好处:
  - 避免重复询问服务背景
  - 快速进入开发状态
  - 减少理解偏差
```

### 2. 跨服务开发
```yaml
流程:
  1. /vibe-service load service-a service-b
  2. 加载两个服务的上下文
  3. 分析服务间交互
  4. 识别接口边界

输出:
  - 两个服务的概览
  - 交互接口列表
  - 数据流向图
```

### 3. 问题排查
```yaml
流程:
  1. /vibe-service analyze user-service
  2. 加载:
     - architecture.md (架构)
     - ops.md (运维协议)
  3. 提供排查建议

输出:
  - 相关组件列表
  - 常见问题及解决方案
  - 监控和日志位置
```

## 自动分析能力

### 从代码推断服务信息
```yaml
若无服务文档:
  1. 分析 package.json / pom.xml
  2. 扫描目录结构
  3. 识别主要模块
  4. 提取 API 路由
  5. 生成服务概览

分析点:
  - 依赖包 → 技术栈
  - src/ 结构 → 模块划分
  - routes/ → API 端点
  - models/ → 数据模型
```

### 生成服务文档建议
```yaml
若服务文档不完整:
  1. 识别缺失部分
  2. 从代码推断内容
  3. 生成文档草稿
  4. 建议用户完善
```

## MCP 集成
```javascript
// 搜索服务相关代码
sou_search({
  query: "user-service 的认证逻辑",
  scope: "src/",
  limit: 10
})

// 深度分析架构
sequential_thinking({
  problem: "分析 user-service 的架构",
  steps: [
    "识别主要模块",
    "分析依赖关系",
    "绘制架构图",
    "识别关键路径"
  ]
})

// 缓存服务上下文
memory_store({
  category: "service_context",
  title: "user-service 概览",
  content: "...",
  tags: ["service", "user"]
})
```

## 指令

### /vibe-service load
```bash
# 加载单个服务
/vibe-service load user-service

# 加载多个服务
/vibe-service load user-service auth-service

# 加载并分析
/vibe-service load user-service --analyze
```

### /vibe-service analyze
```bash
# 分析服务架构
/vibe-service analyze user-service

# 分析服务交互
/vibe-service analyze user-service --with auth-service
```

### /vibe-service init
```bash
# 初始化服务文档
/vibe-service init user-service

# 从代码生成文档
/vibe-service init user-service --from-code
```

## 配置
```yaml
# orchestrator.yaml
service_analysis:
  skill_path: skills/service-analysis/SKILL.md
  context_path: .service-context/
  auto_load: true
  cache_to_memory: true
  analyze_from_code: true
```

## 与其他 Skill 的关系
```yaml
knowledge-base:
  - 服务文档可作为知识库的一部分
  - 服务规范继承自知识库

experience:
  - 服务相关经验可关联到具体服务
  - 服务变更历史记录为经验

riper:
  - Research 阶段自动加载相关服务上下文
  - Execute 阶段参考服务架构约束
```
