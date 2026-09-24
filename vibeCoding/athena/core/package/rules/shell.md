# Shell（本机已知坑）

- `cat` 可能被 alias 成 `bat`：heredoc 写文件用 `command cat > f <<'EOF'` 或写文件工具，写完核对字节数（空 heredoc 门禁会警告）。
- macOS 没有 `timeout`：用 `gtimeout`（coreutils）或工具自带的超时参数。
- `!` 前缀命令没有 TTY：`sudo` 读不到密码，交互命令会挂；需要密码的操作请用户在自己终端跑。
- 长命令不要放后台再判定结果（`&`、`nohup`）：`athena run` 视为不可证明。
- 本机 Node / Python 各保持一个主版本（见 deps-check）；版本不对先修环境，不绕过。
