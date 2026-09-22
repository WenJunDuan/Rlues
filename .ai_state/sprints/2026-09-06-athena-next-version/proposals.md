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

## 新坑七条内化（2026-09-22 quantum-agent 第七会话，纳入 10.1 提示词迭代）

来源：quantum-agent 第七会话（缺陷清尾专场四片 ship，commit c210103f）现场踩坑，逐条「坑 → 提案」。本版不动门禁，候选机制下版本设计时裁量。

1. 路由简报漏 path 字段
   - 坑：两片 Bugfix 派工漏改 `_index.path`，残留上一片的 System；Stop 时撞 R/S polish 门禁，现场 sed 补救。
   - 提案：路由简报模板把 path 列为必填字段（无默认继承）；spec-gate 与 Stop 侧加校验——`_index.path` 与当前 sprint slug 前缀一致性比对，失配即点名 block，不靠人工记得改。

2. 外部写者 Bugfix 接回缺 issue 三件套
   - 坑：grok 外部写者接回的 Bugfix 缺 fix-note，ship 门禁现场才抓到，返工补档。
   - 提案：外部写者接回简报模板（grok-exec / codex 派工节）加必填清单——Bugfix 路径必带 report / analyze / fix-note 三件套路径，接回前自检，不留给 ship 门禁兜底。

3. packet 验收节标题只认五个字面
   - 坑：packet 验收节写了花式标题，prepare 直接拒，报错未说明合法集合，靠试错定位。
   - 提案：合法标题白名单（`## 验收标准` / `## AC` 等五个字面）写进 packet 模板注释；prepare 拒绝时错误信息列出全部合法字面，一次报清。

4. pre-bash-guard 误拦跨仓 push
   - 坑：主仓 stage=impl 时 guard 连 Rlues 仓的 push 都拦，只能等主仓 ship 窗口才推成（quantum-agent 侧 proposals.md 已登同条）。
   - 提案：guard 按 push 目标仓路径判定——仅当 push 目标是当前项目仓时才受 stage 约束；跨仓（提示词源仓等）放行。

5. cat alias heredoc 静默写出 0 字节
   - 坑：同会话三次实害——`cat > file <<'EOF'` 被 alias 劫持，静默产出 0 字节文件，无报错。
   - 提案：写文件规范条目改为 `tee` 或 `command cat`，禁裸 `cat` heredoc；可并入 heredoc-aware-shell-guard sprint 的检测面统一拦。

6. compose 缺省 tag 已删
   - 坑：compose 文件删掉镜像缺省 tag 后，VM 手跑 compose 忘带 `QUANTUM_AGENT_IMAGE` 即起错镜像。
   - 提案：athena-vm skill 操作规程补一行「compose 操作必显式传镜像变量」。通用教训归项目侧规程模板：删缺省值必须同步所有调用点文档。

7. ship 收口子 agent 署名按子会话模型落
   - 坑：ship 收口由子 agent 执行，commit c210103f 落了子会话模型的 attribution 行，与主会话署名不一致；已推送不改。
   - 提案：派工模板固定句「commit 署名按你会话的 attribution 规则写」，明示主/子会话各自按自己的规则落，避免冲突与事后返工。
