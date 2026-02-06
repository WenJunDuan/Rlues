# vibe-review

增强 `/review`，多维度代码审查 + 质量检查。

## 语法

```bash
vibe-review                # 审查最近变更
vibe-review --strict       # 攻击性审查 (Linus 模式)
vibe-review --security     # 安全专项审查
```

## 执行流程

```
1. /review                        # 调用官方 review
2. 加载 code-quality skill        # 质量检查
3. 加载 .ai_state/conventions.md  # 项目约定
4. 对比 .ai_state/plan.md         # 是否偏离方案
5. 输出审查报告
6. 发现的模式 → experience skill 学习
```

## 审查维度

| 维度 | 检查内容 |
|:---|:---|
| 结构 | 函数<50行, 嵌套<3层, 职责单一 |
| 命名 | 准确反映本质，无缩写歧义 |
| 类型 | TypeScript 无 any，完整类型标注 |
| 错误 | 完整错误处理，无静默吞异常 |
| 安全 | 输入验证，无硬编码密钥 |
| 品味 | 数据结构最简？能删掉什么？ |

## --strict 模式

启用 Linus 风格审查，对以下零容忍：
- 过度设计 (over-engineering)
- 无意义抽象层
- 复制粘贴代码
- 魔法数字/字符串
- 未处理的 edge case

## 审查结果写入

发现的问题写入 `.ai_state/todo.md` 作为修复任务。
学到的模式通过 `vibe-learn` 写入经验库。
