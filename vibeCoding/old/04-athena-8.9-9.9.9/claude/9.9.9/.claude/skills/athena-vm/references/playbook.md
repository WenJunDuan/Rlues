# Athena VM 9.9.9 · executable protocol

使用 Python 3.9+ 和 POSIX 本机/SSH；脚本仅依赖标准库，SSH 远端须有 python3。实际代码为相邻 `../scripts/runtime-run.py`，不是待实现 SDK。

```bash
python3 ~/.claude/skills/athena-vm/scripts/runtime-run.py --help
python3 ~/.claude/skills/athena-vm/scripts/runtime-run.py doctor --runner local
python3 ~/.claude/skills/athena-vm/scripts/runtime-run.py doctor --runner ssh --vm dev
python3 ~/.claude/skills/athena-vm/scripts/runtime-run.py snapshot --repo <project> --output <project>/.ai_state/.runtime/input.tar.gz --allow-untracked tests/new-probe.py --required-input tests/new-probe.py
python3 ~/.claude/skills/athena-vm/scripts/runtime-run.py run --bundle <project>/.ai_state/.runtime/input.tar.gz --contract <project>/.ai_state/sprints/<slug>/design.md --scenario <project>/.ai_state/.runtime/scenario.json --output <project>/.ai_state/.runtime/result.json --runner local --requirement required --timeout 60
```

SSH 场景将最后一条改为 `--runner ssh --vm dev`。不增加其他平台依赖，也不自动 git push、clone/pull 或全量 rsync。产物统一放 `.ai_state/.runtime/`，防止旧 bundle/result 被下一次快照纳入；本次 `--output` 也始终排除。主 agent 将必要结果/哈希引用归入当前 sprint 的 runtime-verify/evidence，runner 不写索引或推进 PACE。

## Existing private VM config

默认 `~/.athena/vm.json`，也可 `--config`；必须为非 symlink 私有文件 (0600)。支持已有 schema：

```json
{"version":1,"vms":[{"name":"dev","host":"example.invalid","port":22,"user":"athena","auth":{"method":"key","key_path":"~/.ssh/athena_vm"},"workdir":"/home/athena/work","limits":{"max_session_minutes":30}}]}
```

读取选中条目的 host/user/port/auth/workdir，要求 workdir 已存在；只在其中创建本 run 私有目录。key 使用已有 SSH key/agent，StrictHostKeyChecking=yes，不自动接受主机密钥。旧 `password_env` 形式仅读取其环境变量名并经已有 sshpass 注入 SSHPASS；明文 `password` 字段直接拒绝。密码不放 CLI 参数、代码快照或日志。注册新 VM/建立 known_hosts 需要用户给出目标并授权，脚本不猜测或覆盖现有配置。

## Scenario from project runtime-env

根据项目 runtime-env 和 Done Contract 派生本次场景；每项为 argv，不自动 shell 拼接：

```json
{"name":"approval-smoke","prepare":["python3","tests/prepare.py"],"ready":["python3","tests/ready.py"],"command":["python3","tests/assert-approval.py"],"teardown":["python3","tests/cleanup.py"]}
```

name/command 必填，其他步骤可选。每步 cwd 是校验后的 source 目录；注入 `ATHENA_RUN_ID`、`ATHENA_RUN_ROOT`。prepare 创建的服务可以继续供 ready/command 使用，teardown 之后停止本 run 进程组并删除本 run 目录。测试不能逃逸进程组、修改共享资源或把唯一结果留在远端；外部资源使用 run ID 命名并由 teardown 清理。所需秘密经既有授权环境单独注入，不写 scenario argv。

ready/prepare 失败不执行 command；总场景 timeout 有界，teardown 另有 15 秒。VM 配置预算可缩短场景时间。SSH 失联结果为 transport_failed、cleanup unknown，保留 run ID，恢复时只检查该 ID 的资源；不循环重试或清理其他任务。无受管虚拟机时使用 local；required OS 场景必须在该 OS 真实通过。

## Controlled input and acceptance

snapshot 使用实际 HEAD、Git 受管路径和逐项允许的 untracked，读取工作区最终内容，因此包含已暂存/未暂存变更及删除项。按路径排序记录 type/mode/size/SHA-256、受控变更哈希和 manifest 自身哈希；打包前后二次核对，不把原始 diff 或 .git 历史发送出去。

ignored、`.env*`、凭证目录/私钥路径和命中秘密模式的内容默认排除，受跟踪也不豁免。`--required-input` 命中排除/缺失则阻塞准备。秘密扫描不是未知秘密的完备证明；不会输出或哈希命中的秘密值。目录/symlink/submodule 目前明确拒绝，绝不跟随到快照外。单次压缩及展开上限 256 MiB。

接收端先验证 manifest 自身 hash、精确文件集（无缺失/额外/重复项）、安全相对路径、文件类型、权限和每项内容，再物化到新 run 目录。只接受同一 run/input/contract/scenario 绑定返回；代码或合同变化需生成新输入并按影响复验。

## Results

`result.json` 包括 run_id、input_manifest_sha256、base_commit、contract_sha256、scenario_sha256、非敏感 environment/environment_sha256（OS/release/arch/Python）、分层状态、步骤退出码、截断标记、脱敏 stdout/stderr 与哈希、cleanup 及资源标识。日志每流最多 128 KiB，命中敏感模式的整行替换后才哈希。

configured/transport/scenario 分开；failure.kind 区分 input_invalid、configuration_failed、transport_failed、prepare_failed、ready_failed、command_failed、timed_out、interrupted、teardown_failed、cleanup_failed。成功 exit 0；失败/未知 exit 2。advisory 失败同样非零，只令 blocks_delivery=false；绝不把跳过或可达标 PASS。doctor 不运行场景，scenario 永远 not_run。

来源：[OpenSSH ssh](https://man.openbsd.org/ssh)、[Python subprocess](https://docs.python.org/3/library/subprocess.html)、[tarfile extraction risks](https://docs.python.org/3/library/tarfile.html#extraction-filters)。
