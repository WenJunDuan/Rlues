# Proposals — 2026-09-06
- 触发：用户纠偏“你展示的三个选项都需要”。
- 提案：本次下一版设计同时覆盖流程效率、复杂任务并行、全栈业务交付；优先项不等于排除项。
- 处理：brainstorm.md 已调整为三条主线，后两条不再仅列可选扩展。
- 状态：范围已确认；架构和实现计划仍为提案，未修改现行规则。

## 状态档案减脂（2026-09-20 用户纠偏，纳入下版本；用户称 10.1.0，即本档规划的 9.10.0）

症状（切片 3/4 实测）：session-log 叙事化膨胀（单切片 20+ 条长段）；review 三重存储（_native receipt + 转录 md + session-log 标记行）；每次 stage 转换一个 chore(state) commit；诊断样本（如 pre-bash-guard 误拦）在 session-log 与 roadmap 两处重复。

候选机制（下版本设计时裁量，本版不动门禁）：
1. session-log 电报体硬预算：机器标记行之外每事件 ≤1 行，超预算 spill 到 sprint overflow。
2. review 存储单源：只存原生 receipt + 哈希；implementation-review.md 按需由 accept 生成，不三处重复。
3. ship 收口自动归档：完成 sprint 即移 archive/（9.9.8 机制默认化），热层只留当前 sprint。
4. 记账提交合并：stage 转换不单独 commit，随下一实质提交或收口一次落。
5. 诊断样本只进 roadmap 条目 notes，session-log 只留一行指针。
