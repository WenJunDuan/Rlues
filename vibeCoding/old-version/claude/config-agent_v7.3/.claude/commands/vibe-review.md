---
name: vibe-review
aliases: ["/vr"]
description: 代码审查模式，集成官方审查插件
loads:
  agents: ["qe", "sa"]
  skills: ["verification/"]
  plugins: ["code-review", "pr-review-toolkit", "security-guidance"]
---

# /vibe-review - 代码审查模式

> **Aggressive Testing**: 假设代码一定有Bug。

## 触发方式

```bash
/vibe-review                        # 标准审查
/vibe-review --strict               # 攻击性审查
/vibe-review --security             # 专注安全审查
/vibe-review --pr                   # PR审查模式
/vr                                 # 简写
```

## 工作流

```
变更分析 → 逻辑审查 → 安全检查 → 性能分析 → [REVIEW_DONE]
```

## 执行步骤

### 1. 变更分析
```
sou.search 定位变更代码
分析变更范围和影响
```

### 2. 逻辑审查
```markdown
关注点（不关心代码风格，那是Linter的事）:
- [ ] 逻辑漏洞
- [ ] 边界条件
- [ ] 空指针风险
- [ ] 并发问题
- [ ] 资源泄漏
```

### 3. 安全检查（加载security-guidance）
```markdown
- [ ] SQL注入
- [ ] XSS
- [ ] CSRF
- [ ] 敏感信息泄露
- [ ] 权限检查
```

### 4. 性能分析
```markdown
- [ ] N+1查询
- [ ] 内存泄漏
- [ ] 不必要的循环
- [ ] 缺少索引
```

## 问题分级

| 级别 | 标识 | 行动 |
|------|------|------|
| Critical | 🔴 | 必须修复，阻塞合并 |
| Major | 🟠 | 强烈建议修复 |
| Minor | 🟡 | 建议修改 |
| Info | 🟢 | 仅供参考 |

## 严格模式 (--strict)

```bash
/vibe-review --strict
```

启用攻击性测试思维:
- 假设每行代码都有问题
- 不要在意开发者感受
- 只关注事实和逻辑
- 发现问题直接指出

## PR审查模式 (--pr)

```bash
/vibe-review --pr
```

加载 `pr-review-toolkit` 插件:
- 分析PR变更
- 检查commit规范
- 生成审查报告

## 输出模板

```markdown
## 代码审查报告

**范围**: [文件列表]
**变更**: +XX/-XX 行

### 🔴 Critical
1. [文件:行号] 问题描述
   - 原因: ...
   - 建议: ...

### 🟠 Major
1. ...

### 🔐 安全问题
1. ...

### ✅ 优点
1. [值得肯定的设计]

### 📋 结论
[Deploy/Improve/Rework]
```

## 与官方插件集成

| 插件 | 用途 |
|:---|:---|
| `code-review` | 代码审查核心能力 |
| `pr-review-toolkit` | PR审查工具 |
| `security-guidance` | 安全检查指导 |

## 验证闭环

> **代码审查即系统调教** — Boris Cherny

审查意见应沉淀为可执行的规则：
1. 反馈到 `.claude/skills/knowledge-bridge/`
2. 或添加到自动化检查流程
3. 形成持续改进的闭环
