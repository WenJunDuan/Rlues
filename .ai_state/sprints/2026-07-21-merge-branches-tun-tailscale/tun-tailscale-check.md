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
