---
name: document-sync
description: 文档同步系统，持续检查学习项目文档，保持知识最新
trigger: 每个阶段开始和结束时
---

# Document Sync Skill

> **核心问题**: 如何保持对项目文档的持续学习？
> **解决方案**: 周期性检查 + 变更检测 + 知识提取

---

## 🎯 核心功能

1. **周期性检查** — 每个阶段检查文档变化
2. **变更检测** — 识别文档更新
3. **知识提取** — 从文档中提取规则和约定
4. **同步更新** — 保持 AI 知识与文档同步

---

## 📁 监控文档列表

### 项目级文档

| 文档 | 内容 | 检查频率 |
|:---|:---|:---|
| `README.md` | 项目说明 | 每阶段 |
| `CONTRIBUTING.md` | 贡献指南 | 每阶段 |
| `CHANGELOG.md` | 变更记录 | 每阶段 |
| `package.json` | 依赖配置 | 每阶段 |
| `tsconfig.json` | TS配置 | 每阶段 |
| `.eslintrc` | Lint规则 | 每阶段 |

### AI 状态文档

| 文档 | 内容 | 检查频率 |
|:---|:---|:---|
| `active_context.md` | 当前任务 | 每操作 |
| `kanban.md` | 进度看板 | 每任务 |
| `conventions.md` | 项目约定 | 每阶段 |
| `decisions.md` | 技术决策 | 每阶段 |
| `session.yaml` | 会话状态 | 每操作 |

---

## 🔄 检查流程

```
┌─────────────────────────────────────────────────────────────┐
│                    文档检查流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  阶段开始 / 阶段结束                                        │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Step 1: 扫描文档列表                                 │   │
│  │ - 检查文件是否存在                                   │   │
│  │ - 获取文件修改时间                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Step 2: 检测变更                                     │   │
│  │ - 对比上次检查时间                                   │   │
│  │ - 标记变更的文档                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Step 3: 读取变更内容                                 │   │
│  │ - 读取变更的文档                                     │   │
│  │ - 提取关键信息                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Step 4: 更新知识                                     │   │
│  │ - 更新项目约定                                       │   │
│  │ - 更新禁止规则                                       │   │
│  │ - 记录到 Memory                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Step 5: 记录检查时间                                 │   │
│  │ - 更新 last_check 时间戳                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 检查记录文件

`project_document/.ai_state/doc_check.yaml`:

```yaml
# 文档检查记录
last_check: "2025-01-12T10:30:00Z"

# 文档状态
documents:
  README.md:
    last_modified: "2025-01-10T15:00:00Z"
    last_checked: "2025-01-12T10:30:00Z"
    hash: "abc123..."
    
  conventions.md:
    last_modified: "2025-01-12T09:00:00Z"
    last_checked: "2025-01-12T10:30:00Z"
    hash: "def456..."
    extracted_rules: 5
    
# 提取的知识
extracted:
  - source: "conventions.md"
    type: "rule"
    content: "所有API响应使用统一格式"
    added_at: "2025-01-12T10:30:00Z"
```

---

## 🧠 知识提取规则

### 从 conventions.md 提取

```javascript
async function extractFromConventions(content) {
  const rules = [];
  
  // 提取命名规范
  const namingSection = extractSection(content, '命名规范');
  if (namingSection) {
    rules.push({
      type: 'naming',
      content: namingSection
    });
  }
  
  // 提取代码规范
  const codeSection = extractSection(content, '代码规范');
  if (codeSection) {
    rules.push({
      type: 'code_style',
      content: codeSection
    });
  }
  
  // 提取禁止规则
  const forbiddenSection = extractSection(content, '禁止');
  if (forbiddenSection) {
    for (const rule of parseForbiddenRules(forbiddenSection)) {
      await memory.add({
        category: 'forbidden_action',
        content: rule,
        source: 'conventions.md'
      });
    }
  }
  
  return rules;
}
```

### 从 decisions.md 提取

```javascript
async function extractFromDecisions(content) {
  const decisions = parseADR(content);  // ADR格式
  
  for (const decision of decisions) {
    // 记录技术决策
    await memory.add({
      category: 'project_decision',
      content: `${decision.title}: ${decision.decision}`,
      context: decision.context,
      source: 'decisions.md'
    });
  }
}
```

### 从 package.json 提取

```javascript
async function extractFromPackage(content) {
  const pkg = JSON.parse(content);
  
  // 提取依赖信息
  const deps = {
    ...pkg.dependencies,
    ...pkg.devDependencies
  };
  
  // 检查是否有禁用的依赖
  const forbidden = await memory.recall({ category: 'forbidden_action' });
  for (const dep of Object.keys(deps)) {
    for (const rule of forbidden) {
      if (rule.content.includes(dep)) {
        console.warn(`⚠️ 发现禁用依赖: ${dep}`);
      }
    }
  }
}
```

---

## 🔗 与工作流集成

### 阶段钩子集成

```javascript
// 在 lifecycle 钩子中调用
async function onPhaseEnter(phase) {
  // 检查文档变化
  await documentSync.check();
  
  // 应用最新规则
  await applyLatestRules();
}

async function onPhaseExit(phase) {
  // 检查是否有需要更新的文档
  await documentSync.check();
  
  // 如果有新学到的知识，记录
  if (hasNewLearnings) {
    await documentSync.recordLearnings();
  }
}
```

### 任务执行时检查

```javascript
async function beforeTaskExecute(task) {
  // 检查相关文档
  const relatedDocs = findRelatedDocs(task);
  
  for (const doc of relatedDocs) {
    if (await hasChanged(doc)) {
      // 重新读取并应用
      await applyDocRules(doc);
    }
  }
}
```

---

## 📊 变更报告

当检测到重要变更时，生成报告：

```markdown
## 📄 文档变更检测

### 变更文件
- `conventions.md` (更新于 5分钟前)
- `decisions.md` (更新于 1小时前)

### 新增规则
1. **命名规范**: 组件使用 PascalCase
2. **API规范**: 响应格式统一为 { success, data, error }

### 新增禁止项
1. 禁止使用 moment.js
2. 禁止在循环中使用 await

### 已应用
这些规则已应用到当前会话。
```

---

## ⚠️ 强制规则

1. **每个阶段必须检查** — 不能跳过
2. **变更必须应用** — 保持同步
3. **禁止项必须记录到 Memory** — 跨会话生效
4. **冲突必须报告** — 不能静默忽略

---

## 🛠️ 实现代码

```javascript
class DocumentSync {
  constructor() {
    this.watchList = [
      'README.md',
      'conventions.md',
      'decisions.md',
      'package.json'
    ];
  }
  
  async check() {
    const changes = [];
    const checkRecord = await this.loadCheckRecord();
    
    for (const doc of this.watchList) {
      if (await this.hasChanged(doc, checkRecord)) {
        changes.push(doc);
        await this.processChange(doc);
      }
    }
    
    await this.saveCheckRecord();
    
    if (changes.length > 0) {
      await this.reportChanges(changes);
    }
  }
  
  async hasChanged(doc, record) {
    const stat = await fs.stat(doc);
    const lastMod = stat.mtime.toISOString();
    const lastCheck = record.documents[doc]?.last_checked;
    
    return !lastCheck || lastMod > lastCheck;
  }
  
  async processChange(doc) {
    const content = await fs.readFile(doc, 'utf-8');
    
    switch (doc) {
      case 'conventions.md':
        await this.extractFromConventions(content);
        break;
      case 'decisions.md':
        await this.extractFromDecisions(content);
        break;
      case 'package.json':
        await this.extractFromPackage(content);
        break;
    }
  }
}
```

---

**核心价值**: 保持 AI 知识与项目文档同步 | **触发**: 每阶段 | **输出**: 知识更新
