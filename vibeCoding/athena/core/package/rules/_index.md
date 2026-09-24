# Rules 索引

项目规范（不是命令权限）。CC 按文件头 `paths` 在碰到匹配文件时加载；其他平台按下表需要时读。项目自己的规范与本目录同时生效，冲突时以项目为准。

| 文件 | 何时读 |
|---|---|
| coding.md | 写/审代码 |
| security.md | 碰用户输入、密钥、网络、文件、权限 |
| ui.md | 写/审前端界面 |
| docs.md | 写注释、文档、`.ai_state` 产物 |
| git.md | commit / branch / PR |
| shell.md | 本机命令行的已知坑 |

严重度：P0 违反 = REWORK；P1 = CONCERNS；P2 = 建议。一个 finding 违反多条，取最高。
每条规则的来由与删除条件见源码仓 `vibeCoding/athena/core/rules.md`。
