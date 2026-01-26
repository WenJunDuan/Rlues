---
name: code-quality
description: |
  Code quality assurance with Linus-style review principles. Enforces
  simplicity, good naming, proper error handling, and "good taste".
  Integrates with verification-loop for automated checks.
---

# Code Quality Skill

## Linus Review Checklist

- [ ] **Data First**: 数据结构是最简的吗？
- [ ] **Naming**: 命名准确反映本质？
- [ ] **Simplicity**: 是否过度设计？能删掉什么？
- [ ] **Taste**: 代码有"品味"吗？
- [ ] **No Any**: TypeScript 无 any
- [ ] **Error Handling**: 错误处理完整？

## Quality Gates

### Pre-Commit
```yaml
Required:
  - TypeScript strict pass
  - ESLint clean
  - Prettier formatted
  - Tests pass
  - Coverage >= 80%
```

### Pre-Review
```yaml
Additional:
  - No console.log
  - No TODO comments (or tracked)
  - Documentation updated
  - Security scan clean
```

## Automated Checks

```bash
# TypeScript
npx tsc --noEmit

# Lint
npm run lint

# Format
npm run format:check

# Test
npm run test

# Coverage
npm run test:coverage
```

## Code Smell Detection

| Smell | Detection | Fix |
|:---|:---|:---|
| Long function | >50 lines | Extract |
| Deep nesting | >3 levels | Early return |
| Magic numbers | Literals | Constants |
| Duplicate code | Similar blocks | DRY |
| God object | Many responsibilities | Split |

## Integration

Called by:
- `verification-loop` skill
- `vibe-review` command
- Pre-commit hooks
