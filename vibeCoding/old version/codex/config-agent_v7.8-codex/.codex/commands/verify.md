---
name: verify
description: 运行验证循环
---

# verify - 验证循环

## Usage

```bash
verify                    # 完整验证
verify --focus=tests      # 仅测试
verify --focus=lint       # 仅 lint
verify --quick            # 快速检查
verify --final            # 提交前门控
```

## Verification

- TypeScript strict
- ESLint/Prettier
- Tests pass
- Coverage >= 80%
- Security scan
