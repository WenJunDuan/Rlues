---
name: deps-check
description: 在线查依赖可升级版本 (Maven / npm / PyPI / Cargo / Go / RubyGems / Composer / NuGet)。用户问有无依赖要更新时触发。
---

# /deps-check — 多生态依赖更新检查 (v1)

## 核心原则 (这是本 skill 存在的理由)

> **永远查权威 registry 的"元数据接口", 不查搜索索引 (search index)。**

- 搜索索引 (如 `search.maven.org/solrsearch`、npm 网站搜索) **会延迟/缓存**,
  曾导致把"明明存在的最新版"误判成"编造的版本号"。
- 版本三态必须分清, 不要混为一谈:
  1. **声明版本是否存在** — manifest 里写的版本能否在 registry 拉到 (404 = 不存在/写错)。
  2. **最新稳定版是多少** — registry 的 `release` / `latest` / `max_stable_version` 字段。
  3. **是否含预发布** — `latest` 常包含 `-alpha/-rc/-beta`, 升级建议默认只推稳定版。
- 报告"某依赖可升级"前, 必须真的拿到 registry 返回的版本号; 不确定就标注"未能查到", 不猜。
- 尊重 semver range 语义 (`^` 锁主版本, `~` 锁次版本, 精确锁定), 区分"range 内可升"和"跨大版本"。

## 边界

- 本 skill 只查 **可升级性**, 不查 CVE/安全公告 (那是 `npm audit`/`pip-audit`/OSV 的活, 可附带提)。
- lockfile 已锁的传递依赖不在直接报告范围, 除非用户要求审计全树。
- 私服/企业镜像: 换 registry base URL, 查询逻辑不变。

## 详细 playbook

完整工作流、模板、schema 与联动细节见 `references/playbook.md` —— 按需 Read, 不进热路径。
