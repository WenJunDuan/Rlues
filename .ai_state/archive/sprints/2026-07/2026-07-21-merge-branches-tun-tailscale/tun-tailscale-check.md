# TUN / Tailscale compatibility check

Date: 2026-07-21

## Repository configuration

`clash/mihomo_sparkle.yaml` parses successfully with both PyYAML and `mihomo -t` (Mihomo Meta 1.19.29). Its intended Tailscale safeguards are present:

- `tun.auto-route: true`, `tun.auto-detect-interface: true`, `tun.strict-route: false`.
- `tun.route-exclude-address` includes `100.64.0.0/10` and `fd7a:115c:a1e0::/48`, plus RFC1918/private ranges.
- Rules send `100.64.0.0/10`, `fd7a:115c:a1e0::/48`, private CIDRs, `ts.net`, and Tailscale process names to `DIRECT`.
- DNS uses `system` for `+.ts.net` and `tailscale.com`; fake-IP filtering includes `*.ts.net` and `tailscale.com`.

## Host evidence

- `systemextensionsctl list`: Tailscale Network Extension 1.98.8 and Surge Network Extension 5.0 are both activated and enabled.
- `scutil --nc status Tailscale`: Connected.
- `scutil --nc status Surge`: Connected, primary IPv4 interface `utun16`, address `198.18.0.1`.
- `route -n get 100.64.0.1` and `route -n get 100.100.100.100` both select the default route on `utun16` while Surge is primary.
- The active Surge profile has `tun-excluded-routes = 100.64.0.0/10` commented out; its rule instead sends `100.64.0.0/10` to a Surge `tailscale` policy. This is separate from the system Tailscale extension.

## Diagnosis

The active runtime has two VPN/TUN implementations. The observed default route is owned by Surge, so the current failure is a host-level VPN precedence/route conflict. The Mihomo YAML is not active in the observed process and cannot by itself explain the current `utun16` route.

Mihomo's official TUN docs state that `auto-detect-interface` automatically chooses the egress interface and recommend manually specifying it on multi-interface hosts; they also define `route-exclude-address` as the exclusion for auto-route and state that `exclude-interface` conflicts with it. Source: https://wiki.metacubex.one/config/inbound/tun/

Surge's official Tailscale policy docs state that its `tailscale` policy is an application-level outbound and is not a replacement for the system Tailscale client. Source: https://manual.nssurge.com/policy/tailscale.html

Tailscale documents that tailnet node addresses use the `100.x.y.z` CGNAT range. Source: https://tailscale.com/docs/concepts/tailscale-ip-addresses

## Recommended next action

1. Keep only one full-tunnel proxy/TUN active while testing: either Surge or Mihomo; leave the system Tailscale extension enabled.
2. If Mihomo is the intended proxy, ensure it is the active client and bind its egress to the physical interface (on this host, `en0`) instead of relying on auto-detection across VPN interfaces. Do not add `exclude-interface` together with `route-exclude-address`.
3. If Surge remains the intended proxy, enable its Tailscale route exclusion or disable the separate system Tailscale extension; do not run both a system Tailscale tunnel and Surge's built-in `tailscale` policy for the same tailnet unless that split is intentional.
4. The `PROCESS-NAME,tailscale*` rules are not sufficient for a macOS Network Extension; CIDR/domain exclusions and the active proxy's TUN route policy are the effective controls.

No host VPN state was changed during this check.

## Remote Windows follow-up: 192.168.31.2:7890

Server-side checks from the current host:

- TCP `192.168.31.2:7890` succeeded 5/5 times.
- A plain HTTP request returned `400 Bad Request`, which is normal for a proxy listener.
- An HTTPS CONNECT through `http://192.168.31.2:7890` succeeded and the target returned HTTP 204.
- The repository config has `mixed-port: 7890`, `allow-lan: true`, and `bind-address: "*"`.
- The runtime controller rejects the repository secret, so the service on `192.168.31.2` is not loading this file unchanged (or a client override replaces the controller settings). This does not affect the successful 7890 proxy test.

Most likely cause: Tailscale access control for the shared user allows web ports but omits 7890. Tailscale's official sharing example grants `autogroup:shared` only ports 80 and 443, exactly matching "web page works, 7890 fails". Also, sharing a machine does not advertise its subnet routes into the recipient's tailnet; external users must be invited into the owner tailnet to use subnet routers. Source: https://tailscale.com/docs/features/sharing

Windows evidence needed: `Test-NetConnection 192.168.31.2 -Port 80`, the same command for port 7890, `route print 192.168.31.2`, and the relevant tailnet `grants`/`acls` entry.
