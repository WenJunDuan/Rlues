---
description: 完整开发工作流，Path B/C，RIPER-10
---

# /dev - 完整开发

**触发词**: RIPER、完整开发、新功能、从0到1

**路径**: Path B (2-10文件) 或 Path C (>10文件)

## 核心理念

> **渐进式开发**: 在着手任何设计或编码工作前，必须完成前期调研并厘清所有疑点

## 工作流

```
R1感知 → I设计 → P锁定 → E执行 → R2闭环
```

## 执行步骤

### R1 - RESEARCH (感知)
```markdown
1. memory.recall(project_path)
2. sou.search("<核心关键词>")
3. 理解现有代码结构
4. 识别需要澄清的点
```

### I - INNOVATE (设计)
```markdown
1. 召开 meeting skill (技术设计会议)
   参与: AR + LD + SA

2. 第一性原理分析
   - 问题本质是什么？
   - 最简数据结构是什么？

3. Linus审查
   - 数据结构最简？
   - 是否过度设计？

4. 多方案 → 寸止让用户选择
```

### P - PLAN (锁定)
```markdown
1. 召开 meeting skill (任务规划会议)
   参与: PM + LD

2. 任务分解
   | ID | 任务 | 文件 | 预估 |
   |:---|:---|:---|:---|

3. 寸止确认任务清单
4. 禁止未批准开始编码
```

### E - EXECUTE (执行)
```markdown
1. promptx.switch("LD")
2. codex skill 按任务执行
3. 自检: 类型完整? 错误处理? 
4. 自我修复(max 3) → 寸止人工
```

### R2 - REVIEW (闭环)
```markdown
1. 完整性校验
2. memory.add 固化重要决策
3. 寸止请求验收
4. 等待用户确认
```

## 寸止时机

| Path | 寸止点 |
|:---|:---|
| Path B | I确认方案 + R2验收 |
| Path C | 每个关键决策 + 每Phase完成 |

## 多角色协作流程

```
PM → 主持需求分析会议
     ↓
PDM → 编写用户故事 + 验收标准
     ↓
AR → 第一性原理设计 + 数据结构
     ↓
SA → 安全评审（如涉及）
     ↓
LD → 代码实现
     ↓
QE → 测试验证（用户要求时）
```
