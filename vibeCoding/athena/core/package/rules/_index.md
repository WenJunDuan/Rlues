# Rules 索引

项目规范（不是命令权限）。本平台无路径作用域，按下表需要时读（CC 按文件头 `paths` 自动加载，不装本文件）。项目自己的规范与本目录同时生效，冲突时以项目为准。

| 文件 | 何时读 |
|---|---|
| coding.md | 写/审代码 |
| security.md | 碰用户输入、密钥、网络、文件、权限 |
| ui.md | 写/审前端界面 |
| docs.md | 写注释、文档、`.ai_state` 产物 |
| git.md | commit / branch / PR |
| shell.md | 本机命令行的已知坑 |

严重度见 coding.md 开头。会话流程（开场、写者、验证、合入、收尾）见 athena-session skill。
每条规则的来由与删除条件见源码仓 `vibeCoding/athena/core/rules.md`。
