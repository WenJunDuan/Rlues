# Security Rules

## Mandatory Checks

Before ANY code change:
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] No sensitive data in logs
- [ ] Input validation present
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)

## Forbidden Patterns

```
NEVER commit:
- .env files with real values
- Private keys or certificates
- Database connection strings with credentials
- API keys or tokens
- Passwords or auth tokens
```

## Security Scanning

Before commit:
1. Run `git diff --cached | grep -E "(password|secret|key|token)"`
2. Check for exposed ports in configs
3. Verify no debug endpoints in production

## Dependencies

- Check for known vulnerabilities: `npm audit` / `pip-audit`
- Pin dependency versions
- Review new dependencies before adding
