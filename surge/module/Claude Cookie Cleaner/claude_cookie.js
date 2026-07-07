(() => {
  const targetHost = /(^|\.)((claude\.ai)|(claude\.com)|(anthropic\.com))$/i;
  const storePrefix = "claude_cookie_cleaner.";
  const sessionExpiredBody = JSON.stringify({
    type: "error",
    error: {
      type: "session_expired",
      message: "Session expired"
    }
  });
  const knownCookieNames = [
    "activitySessionId",
    "ajs_anonymous_id",
    "ajs_user_id",
    "anthropic-device-id",
    "anthropic-session-id",
    "auth0",
    "auth0_compat",
    "cf_clearance",
    "intercom-device-id",
    "intercom-id",
    "intercom-session",
    "lastActiveOrg",
    "next-auth.callback-url",
    "next-auth.csrf-token",
    "next-auth.session-token",
    "__Host-next-auth.csrf-token",
    "__Secure-next-auth.callback-url",
    "__Secure-next-auth.session-token",
    "organization",
    "orgId",
    "routingHint",
    "sessionKey",
    "user"
  ];

  function hostnameFromUrl(url) {
    const match = String(url || "").match(/^https?:\/\/([^/:?#]+)/i);
    return match ? match[1] : "";
  }

  function pathnameFromUrl(url) {
    const match = String(url || "").match(/^https?:\/\/[^/]+([^?#]*)/i);
    return match ? match[1] || "/" : "/";
  }

  function isResetEndpoint(url) {
    const host = hostnameFromUrl(url);
    const path = pathnameFromUrl(url);

    return (
      (/^claude\.ai$/i.test(host) && /^\/api\/account(?:\/|$)/i.test(path)) ||
      (/^a-api\.anthropic\.com$/i.test(host))
    );
  }

  function nameBeforeEquals(cookie) {
    return String(cookie || "").split("=")[0].trim();
  }

  function setCookieName(cookie) {
    return nameBeforeEquals(String(cookie || "").split(";")[0]);
  }

  function findHeaderKey(headers, headerName) {
    const lowerHeaderName = headerName.toLowerCase();
    return Object.keys(headers || {}).find((key) => key.toLowerCase() === lowerHeaderName);
  }

  function uniqueCookieNames(names) {
    const seen = new Set();
    const result = [];

    names.forEach((name) => {
      const normalized = String(name || "").trim();
      const key = normalized.toLowerCase();
      if (!normalized || seen.has(key)) {
        return;
      }

      seen.add(key);
      result.push(normalized);
    });

    return result;
  }

  function parseRequestCookieNames(headers) {
    const cookieKey = findHeaderKey(headers, "cookie");
    if (!cookieKey || !headers[cookieKey]) {
      return [];
    }

    return String(headers[cookieKey])
      .split(";")
      .map((item) => nameBeforeEquals(item.trim()))
      .filter(Boolean);
  }

  function storeKey(host) {
    return `${storePrefix}${host}`;
  }

  function readStoredCookieNames(host) {
    try {
      if (typeof $persistentStore === "undefined") {
        return [];
      }

      return JSON.parse($persistentStore.read(storeKey(host)) || "[]");
    } catch (error) {
      return [];
    }
  }

  function writeStoredCookieNames(host, names) {
    try {
      if (typeof $persistentStore === "undefined") {
        return;
      }

      $persistentStore.write(JSON.stringify(uniqueCookieNames(names)), storeKey(host));
    } catch (error) {
      // Ignore storage failures; header cleanup still works without persistence.
    }
  }

  function expiryDomains(host) {
    const domains = [];

    if (/(^|\.)claude\.ai$/i.test(host)) {
      domains.push(".claude.ai");
    }

    if (/(^|\.)claude\.com$/i.test(host)) {
      domains.push(".claude.com");
    }

    if (/(^|\.)anthropic\.com$/i.test(host)) {
      domains.push(".anthropic.com");
    }

    return uniqueCookieNames(domains);
  }

  function expiryCookies(host, names) {
    const paths = ["/"];
    const domains = expiryDomains(host);

    return uniqueCookieNames(names).flatMap((name) => {
      const hostOnlyCookies = paths.map(
        (path) =>
          `${name}=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=${path}; Secure; SameSite=Lax`
      );
      const domainCookies = domains.flatMap((domain) =>
        paths.map(
          (path) =>
            `${name}=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=${path}; Domain=${domain}; Secure; SameSite=Lax`
        )
      );

      return [...hostOnlyCookies, ...domainCookies];
    });
  }

  function sessionExpiredHeaders(host) {
    return {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
      "Set-Cookie": expiryCookies(host || "claude.ai", [
        ...knownCookieNames,
        "routingHint",
        "sessionKey"
      ])
    };
  }

  function notifyReset(url) {
    try {
      if (typeof $notification !== "undefined") {
        $notification.post("Claude Login Reset", "Intercepted Claude session API", url);
      }
    } catch (error) {
      // Notification is best-effort; reset should still continue.
    }
  }

  try {
    const host = hostnameFromUrl($request.url);
    if (!targetHost.test(host)) {
      return $done({});
    }

    if (typeof $response === "undefined") {
      if (isResetEndpoint($request.url)) {
        notifyReset($request.url);
        return $done({
          response: {
            status: 401,
            headers: sessionExpiredHeaders(host),
            body: sessionExpiredBody
          }
        });
      }

      const headers = $request.headers || {};
      const requestCookieNames = parseRequestCookieNames(headers);
      const existingCookieNames = readStoredCookieNames(host);
      const cookieKey = findHeaderKey(headers, "cookie");

      writeStoredCookieNames(host, [
        ...knownCookieNames,
        ...existingCookieNames,
        ...requestCookieNames
      ]);

      if (cookieKey) {
        delete headers[cookieKey];
      }

      return $done({ headers });
    }

    const headers = $response.headers || {};
    const setCookieKey = findHeaderKey(headers, "set-cookie");
    const originalSetCookies = setCookieKey
      ? Array.isArray(headers[setCookieKey])
        ? headers[setCookieKey]
        : [headers[setCookieKey]]
      : [];
    const responseCookieNames = originalSetCookies.map(setCookieName);
    const requestCookieNames = parseRequestCookieNames($request.headers || {});
    const storedCookieNames = readStoredCookieNames(host);
    const namesToExpire = uniqueCookieNames([
      ...knownCookieNames,
      ...storedCookieNames,
      ...requestCookieNames,
      ...responseCookieNames
    ]);

    Object.keys(headers).forEach((key) => {
      if (key.toLowerCase() === "set-cookie") {
        delete headers[key];
      }
    });

    headers["Set-Cookie"] = expiryCookies(host, namesToExpire);
    writeStoredCookieNames(host, namesToExpire);

    return $done({ headers });
  } catch (error) {
    return $done({});
  }
})();
