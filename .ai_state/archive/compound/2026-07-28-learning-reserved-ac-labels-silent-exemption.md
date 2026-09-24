# Learning — 保留元标号 AC11/AC12 被业务 AC 占用 = ship 时静默免检

## Pitfall

`delivery-gate` 把 **编号 11/12 当作 harness 保留元标号**，任何模板、skill、rules 都没写过这件事。
业务 AC 一旦编到 11/12：

- `validateAcMapping` (cjs:813 / py:666-667) 显式把这两个标号**排除在 per-AC 证据绑定校验之外** —
  排除本身有正当理由（给元 AC 造 evidence 行是循环论证，py 注释自陈），但后果是**占用者免检**。
- `validateMetaAcceptance` (cjs:852-866) 反而据标号存在施加**另一套**义务：命中 11 号要求 evaluator
  VERDICT=PASS；命中 12 号要求 `cleanup-pass.md` 含 `PASS|completed|完成` 且活动 worktree 数 = 1。

净效果：**最需要证据的那两条 AC 不要证据，却换来两条与其语义无关的元校验**。

2026-07-28 实测：`2026-07-25-athena-9-9-6-prompt-engineering` 的 AC11「local-only 测试树全覆盖」与
AC12「prompt A/B N≥3 Pareto」正是业务 AC，已静默免检数周无人发现。同型失败在消费侧
`quantum-cowork` 的 `ledger-debt-batch` sprint 同期发生（该 sprint 的 evidence.yaml 绑定字段命中 = 0）。

## Pitfall（衍生，修复过程中当场复现）

重编号成 AC17/AC18 后，在条目正文写溯源说明会**把保留标号重新注射回标号集**：

```markdown
- [ ] AC17 (原 AC11, 避让保留元标号): local-only 测试树……   ← 错
```

`validateAcMapping` 抽标号用的是 `criterion.matchAll(/(?:^|[^A-Za-z0-9])(AC\d+)(?![0-9])/g)`，
扫的是**条目正文**而非行首标号。上面这行同时产出 `AC17` 和 `AC11`，重编号等于没做。

## Constraint

1. **业务 AC 一律避开编号 11/12。** 已占用的重编号到未使用的高位。
2. **AC 条目正文内禁写任何其他 AC 编号。** 编号映射、溯源、依赖关系只能写在
   验收标准节的**表头注**（引用块或 HTML 注释），那里不被 `acceptanceCriteria()` 采集。
3. 重编号是**加严**：标号挪出免检名单后，ship 时必须交 admissible per-AC PASS evidence
   （`source: command` 带 sha256+exit0+implementation_commit / `source: artifact` / `source: review`）。
   代价要在 design 里认下来，不能改完就当没事。
4. **重编号有副作用需单独评估**：AC11/AC12 挪走后 `validateMetaAcceptance` 不再触发，
   原本"碰巧生效"的 evaluator-PASS 与 cleanup+worktree 校验随之失效。若该路径确实需要这两条义务，
   必须确认已由别处覆盖，否则重编号引入净损失。

## 判据沉淀

> **门禁的判据必须在它所约束的文档模板里可见，否则就是隐藏考纲。**

本条已升为 sprint `2026-07-25-athena-9-9-6-prompt-engineering` design §12 的设计原则，
修法是把机器契约写进两端 `pace/templates/sprints/design.md`（AC19），
论证全文见该 sprint `annex-2026-07-27-gate-contract.md`。

## 相关

- `harness-patches.md`（安装态补丁台账，改 gate 必登记）
- `proposals.md` P10/P11（本轮衍生的两条 hook 层根治提案）
- 铁律[证据与出处]：绑定必须是**有意为之的断言** — 谁声称这条命令覆盖了 ACn，谁签名；
  故不改 evidence-collector 自动补 `covers`（机器替人签名 = 伪造绑定）。
