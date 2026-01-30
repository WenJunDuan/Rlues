---
name: service-analysis
description: |
  Service understanding and analysis. Provides service overview, business
  analysis, architecture analysis, and operations analysis. Use when onboarding
  to a codebase or understanding service boundaries.
---

# Service Analysis Skill

## Analysis Types

### 1. Service Overview
```yaml
Output:
  - 服务名称和职责
  - 技术栈
  - 依赖关系
  - 部署方式
```

### 2. Business Analysis
```yaml
Output:
  - 业务流程
  - 核心功能
  - 用户角色
  - 数据流向
```

### 3. Architecture Analysis
```yaml
Output:
  - 系统架构图
  - 模块划分
  - API设计
  - 数据模型
```

### 4. Operations Analysis
```yaml
Output:
  - 监控指标
  - 日志策略
  - 告警规则
  - 运维流程
```

## Commands

```bash
/vibe-service overview      # 服务概览
/vibe-service business      # 业务分析
/vibe-service architecture  # 架构分析
/vibe-service operations    # 运维分析
/vibe-service full          # 完整分析
```

## Output Format

Generates `.ai_state/context/service-analysis.md` with comprehensive service documentation.
