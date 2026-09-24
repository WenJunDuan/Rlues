---
name: deps-check
description: |
  检查项目依赖 (库 / 包 / jar) 是否有可升级版本, 适配多生态:
  Maven / npm·pnpm·yarn·bun / PyPI / Cargo / Go / RubyGems / Composer / NuGet.
  铁律: 版本号必须从官方 registry 在线查询, 不靠记忆/编造, 且区分
  "声明的版本是否存在" 与 "是否最新". 用户要求"看有没有要更新的依赖"时使用.
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

## 工作流

```
1. 探测生态   → 扫 manifest / lockfile, 判定用哪些 registry
2. 抽取依赖   → 解析出 (包名, 当前声明版本/range)
3. 在线查询   → 对每个包打权威 registry, 拿 latest / release + 验证当前版本存在
4. 比对归类   → MAJOR (跨大版本) / MINOR-PATCH (range 内或小升) / 已最新 / 查不到
5. 出报告     → 表格 + 升级建议, 大版本单列并提示 breaking 风险, 由用户决定
```

### 1. 探测生态 (manifest → 生态映射)

| manifest 文件 | 生态 | lockfile |
|---|---|---|
| `pom.xml` / `build.gradle(.kts)` | Maven / Gradle | — |
| `package.json` | npm 系 | `package-lock.json`/`pnpm-lock.yaml`/`yarn.lock`/`bun.lock` |
| `pyproject.toml` / `requirements*.txt` / `Pipfile` | PyPI | `poetry.lock`/`uv.lock`/`Pipfile.lock` |
| `Cargo.toml` | Cargo | `Cargo.lock` |
| `go.mod` | Go modules | `go.sum` |
| `Gemfile` | RubyGems | `Gemfile.lock` |
| `composer.json` | Composer (PHP) | `composer.lock` |
| `*.csproj` / `packages.config` | NuGet (.NET) | — |

多生态项目 (前后端 monorepo) → 各生态分别跑, 分节报告。

### 2~3. 各生态权威查询命令

> 下列命令可直接复制运行。批量时写到 `/tmp/depcheck_<eco>.sh` 循环跑 (本 skill 不预置脚本, 按需生成)。
> `jq` 不可用时用 `grep -o '"version":"[^"]*"'` 兜底解析。

#### Maven / Gradle — `repo1.maven.org` metadata
```bash
# groupId 的点要转成路径斜杠: org.redisson -> org/redisson
G=org/redisson; A=redisson-spring-boot-starter
curl -s "https://repo1.maven.org/maven2/$G/$A/maven-metadata.xml" \
  | grep -oE '<(release|latest)>[^<]+' | sed 's/<[^>]*>//'
# <release> = 最新稳定版 (推荐据此判断); <latest> 可能含快照/预发布
# 验证某声明版本是否存在 (404 = 不存在):
V=4.4.0; curl -s -o /dev/null -w "%{http_code}\n" "https://repo1.maven.org/maven2/$G/$A/$V/"
```
- 私服/镜像 (Nexus/Artifactory/阿里云) 同理换 base URL。
- 多模块项目: 版本常集中在 root `pom.xml` 的 `<properties>`, 优先读那里。
- **不要用** `search.maven.org/solrsearch/select` 的 `latestVersion` 判断最新 (有缓存延迟)。

#### npm / pnpm / yarn / bun — `registry.npmjs.org`
```bash
# 最新稳定版 (dist-tags.latest):
curl -s "https://registry.npmjs.org/react/latest" | grep -o '"version":"[^"]*"' | head -1
# scoped 包: '/' 要编码成 %2f  ->  @tanstack/react-query -> @tanstack%2freact-query
curl -s "https://registry.npmjs.org/@tanstack%2freact-query/latest" | grep -o '"version":"[^"]*"' | head -1
# 验证声明版本存在 (404 = 不存在):
curl -s -o /dev/null -w "%{http_code}\n" "https://registry.npmjs.org/react/19.2.5"
# 列全部版本 + 各 dist-tag:
curl -s "https://registry.npmjs.org/react" | jq '.["dist-tags"]'
```
- 包管理器原生命令也可 (离线/已装依赖时更快, 但仍以 registry 为准):
  `npm outdated` / `pnpm outdated` / `yarn outdated` / `bun outdated`。
- range 解析: `^1.2.3` 允许 `<2.0.0`; `~1.2.3` 允许 `<1.3.0`; 无前缀 = 精确锁定。

#### Python / PyPI — `pypi.org/pypi/<pkg>/json`
```bash
curl -s "https://pypi.org/pypi/requests/json" | jq -r '.info.version'          # 最新
curl -s "https://pypi.org/pypi/requests/json" | jq -r '.releases | keys[]'      # 所有版本
# 验证某版本存在:
curl -s -o /dev/null -w "%{http_code}\n" "https://pypi.org/pypi/requests/2.31.0/json"
```
- `.info.version` 已是最新稳定 (yanked 版本在 `.releases[ver][].yanked`)。

#### Rust / Cargo — `crates.io` (需 User-Agent)
```bash
curl -s -H "User-Agent: deps-check" "https://crates.io/api/v1/crates/serde" \
  | jq -r '.crate.max_stable_version'      # 最新稳定; .crate.newest_version 含预发布
```

#### Go modules — `proxy.golang.org`
```bash
M=github.com/gin-gonic/gin
curl -s "https://proxy.golang.org/$M/@latest" | jq -r '.Version'   # 最新
curl -s "https://proxy.golang.org/$M/@v/list"                       # 所有版本 (大写路径需转义见官方文档)
```

#### Ruby / RubyGems
```bash
curl -s "https://rubygems.org/api/v1/versions/rails/latest.json" | jq -r '.version'
```

#### PHP / Composer — `repo.packagist.org`
```bash
curl -s "https://repo.packagist.org/p2/monolog/monolog.json" \
  | jq -r '.packages["monolog/monolog"][0].version'
```

#### .NET / NuGet
```bash
curl -s "https://api.nuget.org/v3-flatcontainer/newtonsoft.json/index.json" \
  | jq -r '.versions[-1]'   # 包名需小写
```

### 4. 比对归类规则

| 类别 | 判定 | 建议 |
|---|---|---|
| 已最新 | 声明版本 == registry release | 跳过 |
| range 内可升 | registry release 落在声明 range 内 | 安全升 (改 lockfile 即可) |
| 小版本升 (改 manifest) | 同主版本, range 外 | 推荐升, 低风险 |
| **大版本升 (MAJOR)** | 主版本号变化 | **单列**, 提示 breaking, 需查 changelog/迁移指南, 由用户决定 |
| 查不到 / 声明版本 404 | registry 无此版本 | 标红, 可能写错或来自私服 — 核实, **不要**直接判"编造" |
| 预发布 only | 仅有 `-rc/-beta` 更新 | 默认不推, 标注 |

### 5. 报告格式

```
## <生态> 依赖检查 (源: <registry URL>)
| 包 | 当前(声明) | 最新稳定 | 类别 | 建议 |
|---|---|---|---|---|
| react | ^19.2.5 | 19.2.5 | 已最新 | — |
| react-day-picker | 9.14.0 | 10.0.1 | MAJOR | 跨大版本, 看 v10 迁移 |
...
小结: 共 N 个, 可安全升 X, 大版本 Y (需确认), 查不到 Z。
```
- 默认**只报告**, 不擅自升级。用户说"全升"再动手。
- 大版本升级要单独确认 (breaking change), 不和小升混在一起一把梭。

## 升级与验证 (用户确认升级后)

1. 改 manifest (Maven properties / package.json / pyproject 等), 一类一类改, 别一次全改完无法定位。
2. 装/锁: `mvn -q dependency:resolve` · `npm/pnpm/bun install` · `pip install -U` · `cargo update` ...
3. **必须本地验证**: 编译 + 测试 + (前端) 构建。例:
   - Maven: `mvn clean compile` (确认所有模块真的重新编译, 别被 0.x 秒的假成功骗了)
   - 前端: `tsc --noEmit` + `vite build` / `npm run build`
4. 大版本升级若编译报错 → 查官方 migration guide 改代码 (如 react-day-picker v10 的 `table` -> `month_grid`)。

## 错误处理 / 坑

| 现象 | 处理 |
|---|---|
| 搜索索引版本比声明的还旧 | **正常**, 索引有延迟; 以 metadata 接口为准, 别误判编造 |
| scoped npm 包 404 | `/` 没编码成 `%2f` |
| Maven 查不到 | groupId 点没转斜杠 / 包在私服 (换 base URL) / classifier 特殊 |
| crates.io 403 | 缺 `User-Agent` 头 |
| jq 未安装 | 用 `grep -o '"version":"[^"]*"'` 兜底, 或 `python3 -c` 解析 |
| `latest` 是预发布 | 改看 `release`(Maven) / `max_stable_version`(crates) / 过滤 `-rc|-beta|-alpha` |
| 网络/代理失败 | 重试; 仍失败则标"未能在线核实", 不靠记忆填版本号 |

## 边界

- 本 skill 只查 **可升级性**, 不查 CVE/安全公告 (那是 `npm audit`/`pip-audit`/OSV 的活, 可附带提)。
- lockfile 已锁的传递依赖不在直接报告范围, 除非用户要求审计全树。
- 私服/企业镜像: 换 registry base URL, 查询逻辑不变。
