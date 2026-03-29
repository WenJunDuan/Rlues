---
name: verification
description: T 阶段验收标准逐条确认 + 技术验证。superpowers verification-before-completion 做功能完整性后, 本 skill 做验收标准对标。
---
# Verification — 验收标准确认

## 技术验证
1. `npm test` 或项目测试命令
2. `npx tsc --noEmit` (如有 tsconfig.json)
3. `npx eslint . --max-warnings 0` (如有 eslint, Path C+ 强制)

## 验收标准逐条确认
4. 读 .ai_state/design.md "## 验收标准"
5. 逐条: 满足? 证据 (测试名/文件位置)?
6. 未满足 → quality.md "## 未满足验收标准"
7. 有 E2E 框架 → 运行 E2E

## 安全扫描 (ECC)
8. `npx ecc-agentshield scan` (如已安装)
9. 结果追加 quality.md
