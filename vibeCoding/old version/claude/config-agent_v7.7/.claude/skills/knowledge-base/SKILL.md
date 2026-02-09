# Knowledge Base Skill

## 概述
外部知识库读取技能，用于加载项目文档、开发规范、公司要求等外部知识，在开发流程中按需调取。

## 知识库类型

### 1. 项目文档
```yaml
路径: .knowledge/project/
内容:
  - 项目背景介绍
  - 业务领域说明
  - 系统架构文档
  - API 文档
  - 数据字典
```

### 2. 开发规范
```yaml
路径: .knowledge/standards/
内容:
  - 代码规范 (命名、格式、注释)
  - Git 提交规范
  - 代码审查标准
  - 测试规范
  - 文档规范
```

### 3. 公司要求
```yaml
路径: .knowledge/company/
内容:
  - 安全合规要求
  - 隐私保护规范
  - 性能标准
  - 可访问性要求
  - 国际化要求
```

### 4. 技术栈文档
```yaml
路径: .knowledge/tech/
内容:
  - 框架使用指南
  - 第三方库文档
  - 内部工具使用
  - 环境配置说明
```

## 知识库结构
```
.knowledge/
├── index.md                 # 知识库索引 (必需)
├── project/
│   ├── overview.md          # 项目概览
│   ├── architecture.md      # 系统架构
│   ├── api/                 # API 文档
│   └── data-dict.md         # 数据字典
├── standards/
│   ├── code-style.md        # 代码规范
│   ├── git-convention.md    # Git 规范
│   ├── review-checklist.md  # 审查清单
│   └── testing.md           # 测试规范
├── company/
│   ├── security.md          # 安全要求
│   ├── privacy.md           # 隐私规范
│   └── compliance.md        # 合规要求
└── tech/
    ├── framework.md         # 框架指南
    └── tools.md             # 工具使用
```

## 索引文件格式 (index.md)
```markdown
# 知识库索引

## 项目文档
| 文件 | 描述 | 关键词 |
|:---|:---|:---|
| project/overview.md | 项目概览 | 背景, 目标, 范围 |
| project/architecture.md | 系统架构 | 架构, 模块, 组件 |

## 开发规范
| 文件 | 描述 | 关键词 |
|:---|:---|:---|
| standards/code-style.md | 代码规范 | 命名, 格式, 风格 |
| standards/git-convention.md | Git规范 | 提交, 分支, 合并 |

## 公司要求
| 文件 | 描述 | 关键词 |
|:---|:---|:---|
| company/security.md | 安全要求 | 安全, 加密, 认证 |

## 技术栈
| 文件 | 描述 | 关键词 |
|:---|:---|:---|
| tech/framework.md | 框架指南 | React, Node, 框架 |
```

## 调用时机

### 自动调用
```yaml
需求分析阶段:
  - 加载 project/overview.md (理解项目背景)
  - 加载相关业务文档

方案设计阶段:
  - 加载 project/architecture.md (理解现有架构)
  - 加载 tech/*.md (技术栈约束)

开发实施阶段:
  - 加载 standards/code-style.md (代码规范)
  - 加载 company/security.md (安全要求)

代码审查阶段:
  - 加载 standards/review-checklist.md (审查清单)
```

### 手动调用
```bash
# 加载特定知识
/vibe-kb load project/architecture.md

# 搜索知识库
/vibe-kb search "认证相关"

# 列出所有知识
/vibe-kb list
```

## MCP 集成
```javascript
// 使用 sou 搜索知识库
sou_search({
  query: "用户认证相关规范",
  scope: ".knowledge/",
  limit: 5
})

// 使用 memory 缓存常用知识
memory_store({
  category: "knowledge_cache",
  title: "代码规范摘要",
  content: "...",
  tags: ["standards", "code-style"]
})
```

## 使用示例

### 需求分析时
```yaml
1. 读取 .knowledge/index.md
2. 根据需求关键词匹配相关文档
3. 加载匹配的文档到上下文
4. 结合知识库理解需求

示例输出:
  "根据项目架构文档，该功能应在 auth 模块实现..."
  "根据安全规范，密码必须使用 bcrypt 加密..."
```

### 代码编写时
```yaml
1. 自动加载代码规范
2. 检查公司安全要求
3. 参考技术栈文档

约束示例:
  - 命名使用 camelCase
  - 函数不超过 50 行
  - 必须有错误处理
  - 敏感数据必须加密
```

## 知识库维护

### 更新知识
```bash
# 添加新知识文档
创建文件 → 更新 index.md → 添加关键词

# 更新现有知识
修改文件 → 更新 index.md 中的描述/关键词
```

### 最佳实践
```yaml
结构清晰:
  - 按类型分目录
  - 文件名有意义
  - 必须有 index.md

内容规范:
  - 使用 Markdown 格式
  - 包含实际示例
  - 保持更新

关键词准确:
  - 便于检索匹配
  - 覆盖主要概念
```

## 降级策略
```yaml
若 .knowledge/ 不存在:
  1. 使用 references/ 目录作为备选
  2. 使用 memory MCP 查询历史知识
  3. 提示用户创建知识库

若特定文档不存在:
  1. 记录缺失
  2. 继续使用通用规范
  3. 建议补充文档
```

## 配置
```yaml
# orchestrator.yaml
knowledge_base:
  enabled: true
  path: .knowledge/
  index: index.md
  auto_load:
    - standards/code-style.md
    - company/security.md
  search_engine: sou  # 或 grep
```
