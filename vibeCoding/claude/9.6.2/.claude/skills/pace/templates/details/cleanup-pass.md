# Cleanup Pass — Sprint {N}

> 仅 Refactor / System 路径
> 触发条件: review_pass1 → VERDICT ∈ {PASS, CONCERNS}
> 完成后 stage 由 polish → ship

## 路径上下文

- 路径: Refactor | System (二选一)
- Sprint: {N}
- 起源 review: details/reviews/sprint-{N}.md
- 本 polish 启动时间: {YYYY-MM-DD HH:MM}

---

## 1. 临时测试代码清理

> 扫描 console.log / print / TODO / FIXME / hardcoded test values

- [x] `src/auth.ts:42` 删除 console.log (commit abc123) [executed]
- [x] `tests/auth.test.ts:15` 删除 hardcoded "test123" (commit def456) [executed]
- [ ] `src/api/v1.ts:88` `// FIXME` 无 issue 号 → 已转为 `// TODO(issue-789)` (commit ghi789) [executed]
- [!] (no remaining finding)

---

## 2. 注释完善

> 按 ~/.agents/standards/doc-style.md (cc) 或 ~/.agents/standards/doc-style.md (cx)

- [x] `src/auth/jwt.ts` 加 docstring for `verifyToken` (P0 公开 API 必填) [executed]
- [x] `src/auth/jwt.ts:55` 复杂分支逻辑加解释性注释 (P1) [executed]
- [ ] (defer) `src/utils/helpers.ts` 缺 docstring 但被 deprecated, 下 sprint 删除时一并处理

---

## 3. 冗余

> 死代码 / 重复实现 / 重复配置

- [x] 删除 `src/utils/legacy.ts` (`rg legacy.ts` 全 repo 0 引用) [executed: commit jkl012]
- [ ] (defer) `src/api/v1.ts` 与 `src/api/v2.ts` 70% 重复, 但 v1 仍有外部调用方, 下 sprint deprecation 完成后合并

---

## 4. 低效

> N+1 / O(n²) where O(n log n) 可达 / 同步阻塞

- [!] (no finding)
- (or) [x] `src/api/users.ts:33` 修复 N+1 (用 SQL JOIN 替代循环 query) [executed: commit mno345]

---

## 5. 过度设计

> YAGNI 违反 / 抽象层只有 1 个实现 / 未来才用的扩展点

- [x] 删除 `src/plugins/PluginRegistry.ts` 抽象层 (唯一实现是 AuthPlugin, 直接 import 即可) [executed: commit pqr678]
- [ ] (defer) `src/services/EventBus.ts` 复杂 (5 个抽象) 但只 1 个 producer + 1 个 consumer, 下次有第二个 producer 时再保留 / 简化

---

## 合并 review 意见 (来自 details/reviews/sprint-{N}.md)

- review finding F3 P1 "JWT secret 应从 env 读, 不要硬编码 fallback": **已在 polish 阶段处理** (commit stu901)
- review finding F5 P2 "useEffect deps 不全": **已在 polish 阶段处理** (commit vwx234)
- review finding IM-2 P1 "README 仍写旧 token TTL": **deferred** 到 docs sprint (写入 lessons.md)

---

## VERDICT (polish 自己的)

**PASS**

- 5 个检查项全部 executed 或 deferred (有明确 issue / lessons.md 引用)
- review_pass1 的 P2 finding 合并完成
- 无新增 P0 问题
- 改动后 `npm test` / `pytest` 全部 GREEN

→ stage 转 ship
