---
name: verification-loop
description: |
  Checkpoint-based verification for code quality assurance. Use for: running
  verification loops, saving checkpoints, evaluating implementations against
  acceptance criteria. Commands: /verify, /checkpoint.
---

# Verification Loop Skill

Systematic verification through checkpoints and quality gates.

## Verification Types

| Type | Command | Purpose |
|:---|:---|:---|
| Checkpoint | /checkpoint "name" | Save state for recovery |
| Continuous | /verify --continuous | Ongoing checks |
| Final Gate | /verify --final | Pre-commit verification |

## Verification Criteria

### Code Quality
- [ ] TypeScript strict mode
- [ ] ESLint/Prettier clean
- [ ] No `any` types
- [ ] Error handling complete

### Testing
- [ ] Unit tests pass
- [ ] Coverage >= 80%
- [ ] Integration tests pass

### Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] Dependencies secure

## Checkpoint Storage

```
.ai_state/checkpoints/
├── checkpoint-001-feature.yaml
└── checkpoint-latest.yaml
```

## Integration

Works with:
- `code-quality` skill for quality checks
- `cunzhi` skill for pause points
- Git for actual file versioning
