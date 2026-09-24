# RIPER-10 执行循环

## 完整流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                      RIPER-10 Flow                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐           │
│  │ R1  │───▶│  I  │───▶│  P  │───▶│  E  │───▶│ R2  │           │
│  └─────┘    └─────┘    └─────┘    └─────┘    └─────┘           │
│  感知       设计       规划       执行       闭环               │
│                                                                 │
│  PDM        AR         PM        LD         QE                 │
│  sou        thinking   meeting   codex      verification       │
│             寸止       寸止               寸止                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## R1 - RESEARCH (感知)

**目标**: 理解需求和代码上下文

**主导**: PDM

**动作**:
```
1. 读取 .ai_state/active_context.md  // 状态同步
2. memory.recall(project_path)        // 加载记忆
3. sou.search("<关键词>")             // 语义搜索
4. 仅读取直接相关文件                // 禁止全量扫描
5. 识别歧义 → 寸止澄清
```

**产出**:
- 需求分析文档
- 用户故事（Path B/C）
- 验收标准
- 代码上下文

---

## I - INNOVATE (设计) [Path B/C]

**目标**: 设计技术方案

**主导**: AR，SA参与（Path C）

**动作**:
```
1. promptx.switch("AR")
2. sequential-thinking 深度推演
3. Data First: 先定义数据结构
4. 生成2-3个可行方案
5. Linus审查清单检查
6. SA安全审查（Path C）
7. 多方案 → [DESIGN_FREEZE] 让用户选择
```

**Linus审查**:
- [ ] Data First: 数据结构最简？
- [ ] Naming: 命名准确？
- [ ] Simplicity: 是否过度设计？
- [ ] Compatibility: 向后兼容？

**寸止时机**: `[DESIGN_FREEZE]` 方案确认

---

## P - PLAN (规划) [Path B/C]

**目标**: 制定执行计划

**主导**: PM，AR+LD参与

**动作**:
```
1. 加载 meeting skill
2. 召开任务分解会
3. PM主持讨论
4. AR提供技术视角
5. LD提供实现视角
6. 输出WBS任务清单
7. [PLAN_READY] 等待确认
```

**产出**:
- 任务清单（ID/描述/负责/预估/依赖）
- 里程碑（Path C）
- 风险清单（Path C）

**寸止时机**: `[PLAN_READY]` 计划确认

---

## E - EXECUTE (执行)

**目标**: 实现代码

**主导**: LD

**动作**:
```
1. promptx.switch("LD")
2. 读取 .ai_state/active_context.md
3. 按任务清单顺序执行
4. codex skill 执行代码
5. 执行前自检（规范检查）
6. 执行后验证（verification skill）
7. 失败自动重试(max 3)
8. Path C: 每Phase [PRE_COMMIT] 确认
```

**验证回路**:
```
Execute → Verify → Pass? → Next Task
              ↓ No
         Analyze → Fix → Retry (max 3)
                          ↓ Fail
                    [VERIFICATION_FAILED]
```

**寸止时机**: 
- `[PRE_COMMIT]` 大规模修改前
- `[VERIFICATION_FAILED]` 验证失败

---

## R2 - REVIEW (闭环)

**目标**: 验收和知识固化

**主导**: QE，SA参与（Path C）

**动作**:
```
1. promptx.switch("QE")
2. 检查验收标准
3. SA安全检查（Path C）
4. 完整性校验
5. memory.add 固化重要决策
6. 更新 .ai_state/active_context.md
7. [TASK_DONE] 请求验收
8. 等待用户确认
```

**检查项**:
- [ ] 所有任务完成
- [ ] 验收标准满足
- [ ] 无Critical Bug
- [ ] 安全检查通过（Path C）
- [ ] 无遗留TODO

**寸止时机**: `[TASK_DONE]` 最终验收，禁止自行结束

---

## 状态同步

### 对话开始
```
读取 .ai_state/active_context.md
汇报当前状态
```

### 对话结束
```
更新任务状态
记录验证结果
保存到 .ai_state/active_context.md
```

---

## 异步意识

> **你只是并发运行的多个AI会话中的一个。不要依赖你的内存，文件系统是唯一的真理。**

- 所有重要信息写入 `.ai_state/`
- 每次开始都重新读取状态
- 不假设上次会话的内容
