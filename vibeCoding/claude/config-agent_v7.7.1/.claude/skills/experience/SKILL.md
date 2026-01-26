# Experience Skill

## 概述
经验沉淀与检索技能，在开发流程的关键节点自动检索相关经验，在任务完成后沉淀新经验。

## 核心能力

### 1. 经验检索 (experience-index)
```yaml
触发时机:
  - 需求分析前
  - 方案设计前
  - 代码编写前
  - 问题诊断时

检索方式:
  - 关键词匹配
  - 语义搜索 (sou MCP)
  - 标签过滤
```

### 2. 经验沉淀 (experience-deposit)
```yaml
触发时机:
  - 任务完成后
  - 问题解决后
  - 用户纠正后
  - 重要决策后

沉淀内容:
  - 技术决策及原因
  - 问题解决方案
  - 最佳实践发现
  - 踩坑教训
```

### 3. 经验匹配 (experience-match)
```yaml
匹配维度:
  - 技术栈 (React, Node, etc.)
  - 场景类型 (认证, 支付, etc.)
  - 问题类型 (性能, 安全, etc.)
  - 复杂度级别
```

## 经验库结构
```
.ai_state/experience/
├── index.md                 # 经验索引
├── EXP-001.md               # 经验条目
├── EXP-002.md
└── categories/
    ├── decisions.md         # 决策类经验索引
    ├── solutions.md         # 解决方案索引
    ├── best-practices.md    # 最佳实践索引
    └── pitfalls.md          # 踩坑教训索引
```

## 经验条目格式
```markdown
# EXP-001: [经验标题]

## 元信息
- **ID**: EXP-001
- **创建时间**: 2025-01-01
- **关联任务**: REQ-xxx
- **类型**: decision | solution | best-practice | pitfall
- **标签**: [tag1, tag2, tag3]

## 背景
[问题或场景的背景描述]

## 经验内容
[具体的经验、决策或解决方案]

## 适用场景
[什么情况下可以参考这个经验]

## 注意事项
[使用这个经验时需要注意的点]

## 相关链接
- [相关文档]
- [代码示例]
```

## 索引文件格式
```markdown
# 经验索引

## 按类型
### 技术决策
| ID | 标题 | 标签 | 日期 |
|:---|:---|:---|:---|
| EXP-001 | JWT vs Session | auth, security | 2025-01 |

### 解决方案
| ID | 标题 | 标签 | 日期 |
|:---|:---|:---|:---|
| EXP-002 | N+1查询优化 | performance, database | 2025-01 |

## 按标签
- **auth**: EXP-001, EXP-005
- **performance**: EXP-002, EXP-008
- **security**: EXP-001, EXP-003
```

## 自动检索流程

### 需求分析前
```yaml
1. 提取需求关键词
2. 搜索相关经验:
   - 类似功能的实现经验
   - 相关技术的决策记录
3. 加载匹配的经验到上下文
4. 输出经验提示

示例输出:
  "发现 3 条相关经验:"
  "- EXP-001: JWT认证实现 (匹配度: 高)"
  "- EXP-003: 用户数据安全规范 (匹配度: 中)"
```

### 方案设计前
```yaml
1. 提取设计关键词
2. 搜索:
   - 架构决策经验
   - 技术选型经验
   - 最佳实践
3. 提供设计建议

示例输出:
  "根据经验 EXP-005，建议使用 Redis 做会话存储"
  "原因: 支持分布式、性能好、可快速撤销"
```

### 代码编写前
```yaml
1. 识别代码场景
2. 搜索:
   - 代码模式经验
   - 踩坑教训
3. 提供编码建议

示例输出:
  "注意: 根据 EXP-007，此场景需要处理并发问题"
  "建议: 使用乐观锁避免数据竞争"
```

## 经验沉淀流程

### 任务完成时
```yaml
1. 回顾任务过程
2. 提取有价值的经验:
   - 重要决策
   - 解决的问题
   - 发现的最佳实践
3. 生成经验条目
4. 更新索引

自动检测:
  - 是否有技术决策
  - 是否解决了困难问题
  - 是否有用户纠正
  - 是否发现更好的方法
```

### 用户纠正时
```yaml
1. 记录错误行为
2. 记录正确做法
3. 分析原因
4. 生成教训经验
5. 标记为 pitfall 类型

格式:
  错误: [做了什么]
  正确: [应该怎么做]
  原因: [为什么]
```

## MCP 集成

### 检索时
```javascript
// 语义搜索经验
sou_search({
  query: "用户认证相关经验",
  scope: ".ai_state/experience/",
  limit: 5
})

// 从 Memory MCP 查询
memory_search({
  query: "JWT 认证决策",
  category: "experience",
  limit: 3
})
```

### 沉淀时
```javascript
// 存储到 Memory MCP
memory_store({
  category: "experience",
  title: "JWT vs Session 决策",
  content: "选择 JWT 因为...",
  tags: ["auth", "jwt", "decision"]
})

// 同步到本地经验库
// 写入 .ai_state/experience/EXP-xxx.md
```

## 使用示例

### 手动检索
```bash
# 搜索经验
/vibe-exp search "缓存策略"

# 查看经验详情
/vibe-exp show EXP-001

# 列出所有经验
/vibe-exp list
```

### 手动沉淀
```bash
# 添加新经验
/vibe-exp add "标题" --type=decision --tags=tag1,tag2

# 从当前任务沉淀
/vibe-exp deposit
```

## 配置
```yaml
# orchestrator.yaml
experience:
  skill_path: skills/experience/SKILL.md
  storage:
    local: .ai_state/experience/
    mcp: memory  # 同步到 Memory MCP
  auto_search:
    enabled: true
    phases: [research, innovate, execute]
  auto_deposit:
    enabled: true
    on_complete: true
    on_correction: true
  search_engine: sou  # 或 grep
```

## 降级策略
```yaml
若 sou MCP 不可用:
  → 使用关键词匹配搜索

若 Memory MCP 不可用:
  → 仅使用本地经验库

若本地经验库为空:
  → 提示用户开始积累经验
```
