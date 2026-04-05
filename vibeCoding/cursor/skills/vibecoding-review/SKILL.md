---
description: "VibeCoding 审查与质量评估。由 vibecoding-workflow 编排调度到测试验证(T)阶段时使用。也可在用户直接要求'审查代码''review''检查质量'时独立触发。包含测试验证、Quality Gate 四维评估。"
name: VibeCoding Review
---

# 审查阶段

## T 测试验证

### Path A (快速，含简化 Quality Gate)
1. 验证 bug 已修复或配置已生效
2. 确认没有引入新问题
3. 快速检查：功能正确 + 无明显安全问题 + 无语法错误
4. 直接判定 PASS 或 CONCERNS（不需要完整四维评估）

### Path B+ (完整)
1. 对照 R0 阶段的验收标准逐项检查
2. 运行项目现有测试：
   - 先搜索项目中的测试配置（package.json scripts / pytest.ini / Makefile 等）
   - 执行测试命令，报告结果
   - 如果没有现有测试，声明"项目无现有测试"并跳过
3. 自我代码审查：
   - 边界条件处理
   - 错误处理完整性
   - 类型安全（如适用）
   - 性能隐患（N+1 查询、不必要的循环等）

### Path D (增强)
以上全部 + 建议用户使用 /best-of-n 对关键逻辑做多模型交叉验证

产出：测试结果 + 审查意见 + 发现的问题清单

## Quality Gate 四维评估

T 阶段完成后，执行 Quality Gate：

### 评估维度

**1. 功能完整性**
- 所有 MUST 需求是否已实现？
- 验收标准是否全部满足？
- 是否有遗漏的边界情况？

**2. 代码质量**
- 无 TODO / FIXME / HACK 遗留？（CI/CD 的 TODO 除外）
- 无硬编码魔法数字或字符串？
- 错误处理完整（不吞异常、有降级方案）？
- 函数职责单一？

**3. 一致性**
- 符合项目现有命名风格？
- 文件结构和组织方式与项目一致？
- 导入方式和模块引用方式一致？

**4. 安全性**
- 无明文密码 / 密钥 / token？
- 无 SQL 注入 / XSS 风险？
- 无不受限的用户输入直接使用？
- 无不安全的 eval / exec？

### 判定

| 判定 | 条件 | 动作 |
|------|------|------|
| **PASS** | 全部通过 | → V 归档阶段 |
| **CONCERNS** | 有小问题不影响核心功能 | 列出 → 修复 → 重新评估 |
| **REWORK** | 有结构性问题 | → 回到 E 阶段重做对应任务 |
| **FAIL** | 方案有根本缺陷 | → 回到 D 阶段重新设计 |

### 状态写入

如 .ai_state/ 存在，评估完成后写入 quality.json：
```json
{
  "verdict": "PASS",
  "dimensions": {
    "completeness": "pass",
    "quality": "pass",
    "consistency": "pass",
    "security": "pass"
  },
  "issues": [],
  "timestamp": "2026-04-05T10:00:00Z"
}
```

如果判定非 PASS，issues 数组列出每个问题：
```json
{
  "issues": [
    {"dimension": "quality", "severity": "minor", "desc": "utils.js 第 42 行有 TODO"},
    {"dimension": "security", "severity": "major", "desc": "API key 硬编码在 config.js"}
  ]
}
```
