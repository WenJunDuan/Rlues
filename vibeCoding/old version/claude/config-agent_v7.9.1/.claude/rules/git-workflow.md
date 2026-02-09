# Git Workflow Rules

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

## Examples

```
feat(auth): add JWT token refresh

- Implement automatic token refresh before expiry
- Add refresh token rotation
- Update auth middleware

Closes #123
```

## Branch Naming

```
feature/TICKET-123-short-description
bugfix/TICKET-456-fix-login
hotfix/critical-security-patch
```

## PR Requirements

Before creating PR:
- [ ] Tests pass locally
- [ ] Linting passes
- [ ] No merge conflicts
- [ ] Meaningful commit messages
- [ ] Updated documentation if needed

## Merge Strategy

- Feature branches → Squash merge
- Release branches → Merge commit
- Hotfixes → Cherry-pick to affected branches
