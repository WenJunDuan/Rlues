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

## 必做清单

1. 全组件清单：列出仓库内**所有** manifest（根目录与子包、工具链、CI、Dockerfile 基础镜像、运行时版本文件如 `.nvmrc` / `.python-version`），逐个检查，不只查主 package。
2. 每个结论标来源：registry 元数据接口 URL + 查询时间；查不到写「未能查到」。
3. SDK / 框架跨版本升级：列出项目对其私有或未文档化契约的使用（内部字段、猴子补丁、`as unknown as`、非公开导入路径），逐条对照新版 changelog / 源码复核；有一条对不上就标「需改代码」。
4. 末步：本机 Node / Python 各保持一个主版本（与版本文件一致）；发现多版本并存先报告，不在多版本环境下装依赖。

## 详细 playbook

完整工作流、模板、schema 与联动细节见 `references/playbook.md` —— 按需 Read, 不进热路径。
