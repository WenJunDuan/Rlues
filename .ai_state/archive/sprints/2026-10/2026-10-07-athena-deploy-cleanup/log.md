# Log — 2026-10-07-athena-deploy-cleanup

- 2026-10-07 start: path=Quick item=

## 2026-10-07 收尾

- 仓库 VERSION 与 origin 最新发布均为 10.1.5，HEAD 034058a。部署前系统 doctor 报 10.1.0；从当前源码构建并经 install CLI 更新 cc,cx，233 write、3 merge、0 retire。部署后 doctor 无漂移，托管文件逐项匹配源码构建。
- 回滚备份：`~/.athena/backups/20261007T120737900Z`；CLI 链接 `~/.local/bin/athena`，登录 shell 可用。
- 会话保护：对 7024 个受保护文件（2,651,761,801 bytes）记录旧内容 SHA256；会话旧内容一致，1 个活动文件正常追加。实时 global state/session index 只核对文件存在；6 个数据库原 inode 保留。用户配置、权限和用户 hooks 经备份比对通过。
- 清理 1271 个已审核、未使用的缓存/垃圾条目（17,925,295 bytes，约 17.1 MiB），包括过期临时 Git objects、Finder/Python 缓存与遗留原子写临时文件。115 个旧 Athena 技能文件移出 `.codex/skills`，完整备份至上述回滚目录的 `retired-codex-skills`，保留系统技能及用户 chronicle 技能。有效插件缓存、工作区、会话、附件和数据库保留。
- 已删除本地及 origin 的 `pre-athena-10.1-state`；`v10.1.0` 与 `v10.1.5` 均保留。
- 验证：`athena run --covers AC1,AC2,AC3,AC4 -- python3 -m unittest discover -s /private/tmp/athena-deploy-20261007 -p test_deployment.py -q`，4 checks PASS，exit=0，kind=test，provable=true，evidence 62fe20f77c6e，tree 23aa85b65af6。
- 无剩余范围内事项；记账不单独提交。
- 2026-10-07 shipped (evidence 62fe20f77c6e)
