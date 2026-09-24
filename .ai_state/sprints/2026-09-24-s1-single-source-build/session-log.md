# Session log — S1 single-source-build

- 2026-09-24：路由 System（athena-10-1 S1，用户「开 S1」）；分支 athena-10.1 @8903233。design 落盘 AC1–AC6，含 4 条对 10.1 设计的已裁量偏差。conf=0.9。
- 2026-09-24：导入一次性完成（脚本不入库）：CC/CX 包内同名 110 个 → 67 逐字节相同 + 7 仅差 `~/.claude/skills`↔`~/.agents/skills`（模板 `{{athena:SKILLS_DIR}}`）入 core；36 真分叉 + CC 独有 41 + CX 独有 42 入 adapters/{cc,cx}/package；包外文件入 adapters/*/top；Pi 86 个整包入 adapters/pi/top。
- 2026-09-24：review 2 轮：CONCERNS（P1 rmSync 无保护）→ PASS；P3 两条补修。fixture 20/20，athena999 231 OK。
- 2026-09-24：坑：device_commit_files 对同一 stagedPath 重复提交时交付了旧版 build.mjs（哈希不符），换新 stagedPath 后一致。此后跨端传文件一律核 sha256。
- 2026-09-24：附带发现：安装切片 5 后 validateContainment 要求 `harness_target_outside_repo` 配 `_sprint` 字段；quantum-agent `_index` 自 09-10 残留 true → 下次 ship/Stop 必拦。已在 quantum 工作区把该值复位为 false（未提交，交用户）。
