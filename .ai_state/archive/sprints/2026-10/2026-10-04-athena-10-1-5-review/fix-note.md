# 修复与验证

- 版本 10.1.5，保留 major.minor 构建目录与 schema 代际 10.1。
- 修复报告 R1–R9；未变更 H1–H5、证据可证明边界或自动合并类型。
- 全量：327 tests in 126.269s，OK (skipped=1，pytest 缺失)；athena run 证据 2c566e3cb449，源码树 286c997aff79。
- 红灯证据：599500acae95 / 0dd3599026c7 / 55dd0e23a52a / 5cbc2ed701d4 / 76d03905a8f2；随后全量绿。
- 原生 CC validate/details、CX 临时安装/发现，见 test_native_plugins.py；仅组件发现不覆盖模型调用、hook 受信与原生工具事件。
- 发布待办 U-001、D-014 和未实跑探针仍开放；本 sprint 交付 review/debug 候选，不等同于 S7 发布。
- 独立终审 620457fc REWORK：同树较新失败被旧 PASS 掩盖。红灯 fd82fdf08ad6；最小修复后 rebind 9 项通过（236fa16f4495）。唯一 pytest 跳过项已由 uv 临时环境补验（388f78699c68），未添加项目依赖。

- 最终静止源码树 72f015d673ba：328 tests / 127.930s / OK、零跳过（9a75bb5222de）；文档 3a002715eacc。旧的 327 项结果保留为修复过程记录，最终以 evidence.yaml 为准。

- R9 SSH 分类变化分支同样先红后绿：eee6ed3e13e0 → 9b7b3e894843；最终树 fba7d9a2dab1，全量 329 项、零跳过（10e4c929ec9e），前两次 REWORK 原样保留。
