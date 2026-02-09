# 代码质量 (Code Quality)

## Linus Torvalds 哲学

### 核心理念
> "Good taste is about being able to recognize the difference between ugly code and beautiful code, and having the strength to write the beautiful code even when the ugly code works."

### 品味清单
```
每次写代码前问自己:

□ 这是最简单的实现方式吗？
□ 有没有更直接的方法？
□ 三个月后我能理解这段代码吗？
□ 这个抽象真的需要吗？
□ 能否用更少的代码实现？
```

## Boris Cherny 实践

### 计划驱动
```yaml
原则:
  - 先想清楚再动手
  - 复杂任务先拆解
  - 每步都可验证

实践:
  - 必须有 TODO
  - 边做边更新状态
  - 完成后验证闭环
```

### 验证循环
```yaml
每次修改后:
  1. 功能验证
  2. 类型检查
  3. 规范检查
  4. 边界测试
```

## 代码简化规则

### 何时简化
```yaml
信号:
  - 代码重复 > 2处
  - 函数 > 50行
  - 嵌套 > 3层
  - 参数 > 5个
  - 文件 > 300行
```

### 简化技术

#### 提取函数
```typescript
// Before
function process() {
  // 20行验证逻辑
  // 20行处理逻辑
  // 20行保存逻辑
}

// After
function process() {
  validate();
  transform();
  save();
}
```

#### 早返回
```typescript
// Before
function check(x) {
  if (x) {
    if (x.valid) {
      return x.value;
    }
  }
  return null;
}

// After
function check(x) {
  if (!x) return null;
  if (!x.valid) return null;
  return x.value;
}
```

#### 移除死代码
```yaml
检查:
  - 未使用的变量
  - 未调用的函数
  - 注释掉的代码
  - 永远不会执行的分支
```

## 错误学习

### 记录格式
```markdown
## 错误: [简述]

**时间**: 2025-01-01
**文件**: path/to/file.ts
**错误类型**: [TypeError/LogicError/...]

**代码**:
\`\`\`typescript
// 错误代码
\`\`\`

**根因**: [为什么出错]

**修复**:
\`\`\`typescript
// 修复后代码
\`\`\`

**教训**: [可泛化的经验]
```

### 常见教训
```yaml
类型安全:
  - 总是检查 null/undefined
  - 使用类型守卫
  - 避免 any

异步处理:
  - 处理 Promise rejection
  - 考虑竞态条件
  - 设置超时

边界条件:
  - 空数组/对象
  - 极大/极小值
  - 特殊字符
```

## 调试规范

### 调试流程
```
1. 复现问题
2. 最小化用例
3. 定位根因
4. 修复验证
5. 记录教训
```

### MCP 增强调试
```javascript
// 复杂问题推理
sequential_thinking({
  problem: "函数返回意外结果",
  steps: [
    "列出输入输出",
    "追踪执行路径",
    "检查每步状态",
    "定位偏差点"
  ]
})
```

### 调试工具
```yaml
日志:
  - console.log (基础)
  - debug 包 (带命名空间)
  
断点:
  - debugger 语句
  - VSCode 断点

分析:
  - Chrome DevTools
  - Node --inspect
```

## 重构规范

### 重构原则
```
1. 有测试覆盖
2. 小步进行
3. 每步验证
4. 功能不变
```

### 重构类型

#### 提取
```yaml
提取变量: 复杂表达式 → 命名变量
提取函数: 代码块 → 函数
提取模块: 相关函数 → 模块
提取接口: 重复结构 → 类型
```

#### 内联
```yaml
内联变量: 只用一次的变量
内联函数: 过度封装的函数
```

#### 重命名
```yaml
变量: 更准确的名字
函数: 描述做什么，不是怎么做
文件: 反映内容
```

### MCP 增强重构
```javascript
// 复杂重构
sequential_thinking({
  problem: "重构200行函数",
  context: "函数职责混杂...",
  steps: [
    "识别职责边界",
    "规划提取顺序",
    "逐步提取验证",
    "清理整合"
  ]
})
```

## 质量检查清单

### 每次修改
```markdown
- [ ] 类型正确
- [ ] 无 lint 错误
- [ ] 逻辑正确
- [ ] 边界处理
```

### 代码审查
```markdown
- [ ] 命名清晰
- [ ] 逻辑简洁
- [ ] 无重复
- [ ] 注释适当
- [ ] 测试覆盖
```

### 发布前
```markdown
- [ ] 全部测试通过
- [ ] 无 TypeScript 错误
- [ ] Lint 检查通过
- [ ] 性能达标
- [ ] 文档更新
```
