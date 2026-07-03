(() => {
  const targetHost = /(^|\.)((claude\.ai)|(claude\.com)|(anthropic\.com))$/i;
  const targetPath = /(^|\/)(login|logout)(\/|$)/i;
  const strippedNames = new Set(["sessionkey", "routinghint"]);

  function hostnameFromUrl(url) {
    const match = String(url || "").match(/^https?:\/\/([^/:?#]+)/i);
    return match ? match[1] : "";
  }

  function pathnameFromUrl(url) {
    const match = String(url || "").match(/^https?:\/\/[^/]+([^?#]*)/i);
    return match ? match[1] || "/" : "/";
  }

  function cookieName(cookie) {
    return String(cookie || "").split("=")[0].trim().toLowerCase();
  }

  function setCookieName(cookie) {
    return String(cookie || "").split(";")[0].split("=")[0].trim().toLowerCase();
  }

  try {
    const host = hostnameFromUrl($request.url);
    const path = pathnameFromUrl($request.url);
    if (!targetHost.test(host) || !targetPath.test(path)) {
      return $done({});
    }

    if (typeof $response === "undefined") {
      const headers = $request.headers || {};
      const cookieKey = Object.keys(headers).find(
        (key) => key.toLowerCase() === "cookie"
      );

      if (cookieKey && headers[cookieKey]) {
        const keptCookies = String(headers[cookieKey])
          .split(";")
          .map((item) => item.trim())
          .filter((item) => item && !strippedNames.has(cookieName(item)));

        if (keptCookies.length) {
          headers[cookieKey] = keptCookies.join("; ");
        } else {
          delete headers[cookieKey];
        }
      }

      return $done({ headers });
    }

    const headers = $response.headers || {};
    Object.keys(headers).forEach((key) => {
      if (key.toLowerCase() !== "set-cookie") {
        return;
      }

      const originalValue = headers[key];
      const cookies = Array.isArray(originalValue) ? originalValue : [originalValue];
      const keptCookies = cookies.filter(
        (cookie) => !strippedNames.has(setCookieName(cookie))
      );

      if (!keptCookies.length) {
        delete headers[key];
      } else {
        headers[key] = Array.isArray(originalValue) ? keptCookies : keptCookies[0];
      }
    });

    return $done({ headers });
  } catch (error) {
    return $done({});
  }
})();
