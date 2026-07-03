# R1 - RESEARCH (感知理解)

> 加载时机：RIPER 第一阶段 | 角色：PDM

---

## 执行步骤

### Step 1: 状态恢复
```
读取 .ai_state/session.lock
  ├── 存在 → 工作流恢复模式
  └── 不存在 → 创建新会话锁
```

### Step 2: 加载 Memory
```javascript
// 必须加载
memory.recall({ category: "user_preference" })
memory.recall({ category: "forbidden_action" })
memory.recall({ category: "code_pattern" })
memory.recall({ category: "lesson_learned" })
```

### Step 3: 代码搜索
```
使用 sou/augment 搜索相关代码
只读直接相关文件（不要读整个项目）
  - 目标文件
  - 依赖文件
  - 类型定义
```

### Step 4: 需求澄清
```
IF 需求有歧义:
  调用 cunzhi MCP 暂停
  输出理解 + 问题
  等待用户澄清
  
⚠️ 禁止猜测！不确定就澄清！
```

---

## 产出物

- [ ] session.lock（新建/更新）
- [ ] Memory 加载记录
- [ ] 相关代码位置清单
- [ ] 需求理解摘要

---

## 检查点

- [ ] 会话锁已检查/创建
- [ ] Memory 已加载（4个类别）
- [ ] 相关代码已定位
- [ ] 需求已完全理解（无歧义）

---

## 完成后

→ 进入 I 阶段，加载 `skills/innovate.md`
