# Claude Login Reset

Surge iOS module. It forces Claude account APIs to return `session_expired`, then clears Claude / Anthropic web login cookies at the HTTP layer.

## Files

- `claude-cookie-clean.sgmodule`: Surge module to import on iPhone
- `claude_cookie.js`: Script used by the module
- `README.md`: Usage notes

## Online URLs

Module Raw URL:

```text
https://raw.githubusercontent.com/WenJunDuan/Rlues/refs/heads/main/surge/module/Claude%20Cookie%20Cleaner/claude-cookie-clean.sgmodule
```

Script Raw URL:

```ini
https://raw.githubusercontent.com/WenJunDuan/Rlues/refs/heads/main/surge/module/Claude%20Cookie%20Cleaner/claude_cookie.js
```

## Use On iPhone

1. Surge iOS -> Modules -> Install Module.
2. Paste the module Raw URL.

```text
https://raw.githubusercontent.com/WenJunDuan/Rlues/refs/heads/main/surge/module/Claude%20Cookie%20Cleaner/claude-cookie-clean.sgmodule
```

3. Enable the module.
4. Make sure Surge MITM is enabled and the CA certificate is installed and trusted.
5. Open Claude iOS or Claude Web once.
6. Wait until Claude returns to the login screen or account state resets.
7. Disable the module immediately, otherwise Claude APIs will keep returning `session_expired`.

## What It Does

- Forces `https://claude.ai/api/account...` to return HTTP `401` with `session_expired`.
- Forces `https://a-api.anthropic.com/...` to return HTTP `401` with `session_expired`.
- Removes the outgoing `Cookie` header for Claude and Anthropic domains.
- Removes incoming `Set-Cookie` headers from Claude and Anthropic responses.
- Sends expired `Set-Cookie` headers for known and observed Claude-related cookie names.

Matched domains:

```text
claude.ai
*.claude.ai
claude.com
*.claude.com
a-api.anthropic.com
anthropic.com
*.anthropic.com
```

## Why This Shape

The `401 session_expired` path matches Claude app behavior better than only deleting cookies: the app sees an expired session and runs its own logout/reset flow. Cookie deletion remains useful as a browser fallback.

The module includes both:

- `Script`: dynamic reset response plus broad Cookie cleanup
- `Map Local`: static `401 session_expired` fallback if the reset endpoint is matched

## Limits

This cannot clear iOS/macOS Keychain items, Claude app private storage, Safari LocalStorage, IndexedDB, or Cache Storage.

Surge scripts run on HTTP requests and responses. They do not have permission to access system Keychain or another app's private data.

For deeper manual cleanup on iPhone:

1. Clear Safari website data for `claude.ai`, `claude.com`, and `anthropic.com`.
2. Delete and reinstall the Claude app if you use the native app.
3. Check iOS Passwords/Passkeys manually for saved Claude credentials.

References:

- Surge Module: https://manual.nssurge.com/others/module.html
- Surge Scripting: https://manual.nssurge.com/scripting/common.html
- Surge Map Local: https://manual.nssurge.com/http-processing/mock.html
- Surge MITM: https://manual.nssurge.com/http-processing/mitm.html
- Apple Keychain Services: https://developer.apple.com/documentation/security/keychain-services
