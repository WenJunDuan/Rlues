# I - INNOVATE (方案设计)

> 加载时机：RIPER 第二阶段 | 角色：AR | 适用：Path B/C

---

## 执行步骤

### Step 1: 问题分解（第一性原理）
```
问自己三个问题：
1. 这个需求的本质是什么？（去掉表面描述）
2. 去掉所有假设后，还剩什么？（真实约束 vs 可变假设）
3. 最简方案是什么？（能用最少代码实现吗？）
```

### Step 2: 数据结构设计（Data First）
```typescript
// 先定义数据，再写逻辑

// Step 2.1: 定义核心实体
interface Entity {
  id: string;
  // ... 最少必要字段
}

// Step 2.2: 定义输入输出
interface Request { }
interface Response { }

// Step 2.3: 自问
// - 这是最简结构吗？
// - 能删掉什么字段？
// - 命名准确吗？
```

### Step 3: 方案对比
```markdown
| 维度 | 方案A | 方案B |
|:---|:---|:---|
| 数据结构 | ... | ... |
| 复杂度 | 低/中/高 | ... |
| 可扩展性 | ... | ... |
| 实现难度 | ... | ... |

推荐：方案X，理由：...
```

### Step 4: Linus 审查
```
- [ ] Data First: 数据结构是最简的吗？
- [ ] Naming: 命名准确反映本质？
- [ ] Simplicity: 是否过度设计？
- [ ] Compatibility: 向后兼容？
- [ ] Taste: 设计有"品味"吗？
```

### Step 5: 寸止 [DESIGN_FREEZE]
```
调用 cunzhi MCP（或 mcp-feedback）

输出：
- 数据结构定义
- 方案对比表
- 推荐方案及理由
- Linus 审查结果

等待用户选择：A / B / 讨论
```

---

## 产出物

- [ ] 问题分解文档
- [ ] 数据结构定义（Interface）
- [ ] 方案对比表
- [ ] Linus 审查报告
- [ ] decisions.md 更新

---

## 检查点

- [ ] 问题本质已识别
- [ ] 数据结构已定义（无冗余）
- [ ] 至少2个方案对比
- [ ] Linus 5项全部通过
- [ ] 已调用寸止等待用户

---

## 完成后

用户确认方案 → 进入 P 阶段，加载 `skills/plan.md`
