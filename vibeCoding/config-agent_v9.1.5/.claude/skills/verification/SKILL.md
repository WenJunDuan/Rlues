---
name: verification
description: 代码验证 — 测试/lint/类型检查 (对应 rules.md MUST 级规范)
context: main
---
## 检查清单 (对应 rules.md)
1. **测试通过** (MUST): 自动检测并运行项目测试
   - npm test / pytest / cargo test / go test
2. **lint 通过** (MUST): eslint / ruff / clippy / golangci-lint
3. **类型检查** (MUST): tsc --noEmit / mypy / cargo check
4. **无 TODO/FIXME** (MUST): `grep -rn "TODO\|FIXME\|HACK" src/`
5. **无密钥泄露** (MUST): `grep -rn "API_KEY\|SECRET\|PASSWORD" --include="*.ts" --include="*.py" src/`
6. **conventions 符合** (SHOULD): 对照 .ai_state/conventions.md

## Path 差异
- A: 检查 1 即可
- B: 全部, 输出 .ai_state/verified.md
- C+: + Agent(validator) 子代理

## 产出: .ai_state/verified.md (通过/失败 + 详情)
