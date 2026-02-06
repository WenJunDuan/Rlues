# vibe-verify

验证循环：执行 → 验证 → 通过/修复 → 重试。

## 语法

```bash
vibe-verify                # 验证当前 doing 任务
vibe-verify --cross        # 交叉验证 (Model A 实现 → Model B 审查)
```

## 验证流程

```
Execute → Verify → Pass? ──Yes──→ doing → done
                    │ No
                    ↓
              Analyze → Fix → Retry (max 3)
                               │ 3次失败
                               ↓
                         cunzhi: 请求人工介入
```

## --cross 交叉验证

利用 model-router 实现双模型交叉检查：
- Claude 实现 → Codex 审查
- Codex 实现 → Claude 审查

增加缺陷发现率，适用于 Path C/D 的关键功能。

## 验证结果写入

- 通过 → doing.md 中标记 verified
- 失败 → 追加修复子任务到 todo.md
