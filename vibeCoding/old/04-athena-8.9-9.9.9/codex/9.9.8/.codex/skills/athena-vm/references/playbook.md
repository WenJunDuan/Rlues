# athena-vm · playbook

> 从 SKILL.md 下沉的完整正文 (v9.9.6 渐进披露拆分)。热路径只留触发与判据。

## 配置文件: `~/.athena/vm.json` (chmod 600)

**不放 .ai_state/** — 那是项目级、会进 git 的目录. 凭证类配置一律全局 + 600 权限.

```json
{
  "version": 1,
  "vms": [
    {
      "name": "dev-vm",
      "host": "192.168.1.100",
      "port": 22,
      "user": "athena",
      "auth": { "method": "key", "key_path": "~/.ssh/athena_vm" },
      "os": "ubuntu-24.04",
      "workdir": "/home/athena/work",
      "purpose": ["runtime-verify", "e2e"],
      "limits": { "max_session_minutes": 30 }
    }
  ]
}
```

**auth 两种形态 (key 优先)**:

| method | 字段 | 说明 |
|---|---|---|
| `key` (推荐) | `key_path` | setup 引导跑一次 `ssh-copy-id`, 之后零交互 |
| `password_env` (降级) | `password_env: "ATHENA_VM_PW"` | 存**环境变量名**, 不存密码本身; 需要 `sshpass`, 丑但可用 |

❌ **禁止**: `"password": "明文"` — setup 和 doctor 见到该字段直接报错拒绝工作. 配置文件会被 cp、会被 subagent 读、可能被误提交, 明文密码进 JSON 没有借口.

## setup (一次性)

```bash
mkdir -p ~/.athena && chmod 700 ~/.athena

# 1. 收集: name / host / port / user (问用户, 不猜)
# 2. 认证:
#    key 路线 (推荐): 无 key 则 ssh-keygen -t ed25519 -f ~/.ssh/athena_vm -N ""
#      然后让用户自己跑 ssh-copy-id -i ~/.ssh/athena_vm.pub -p {port} {user}@{host}
#      (这一步要输密码, 用户亲手输, agent 不经手)
#    password_env 路线: 让用户在 shell profile 里 export ATHENA_VM_PW=...; 检查 sshpass 已装
# 3. 写 ~/.athena/vm.json (上面 schema) && chmod 600 ~/.athena/vm.json
# 4. 写 SSH 别名 (只统一目标命名与连接参数; 不等于命令授权或 sandbox):
cat >> ~/.ssh/config << EOF
Host athena-vm-dev-vm
  HostName 192.168.1.100
  Port 22
  User athena
  IdentityFile ~/.ssh/athena_vm
  StrictHostKeyChecking accept-new
  ConnectTimeout 10
EOF
# 5. 项目内: 更新 .ai_state/_index.md tools_available.vm_available: true
```

password_env 路线的连接姿势: `sshpass -e ssh athena-vm-{name} '...'` (sshpass -e 读 SSHPASS 环境变量:
执行前 `export SSHPASS="$ATHENA_VM_PW"`. 密码始终只在环境变量里, 不进命令行参数不进文件).

## doctor (连通自检, 进 runtime-verify 前跑)

```bash
ssh athena-vm-dev-vm 'echo ATHENA_VM_OK && uname -a && df -h /tmp | tail -1'
# 期望: ATHENA_VM_OK + 系统信息. 失败 → vm_available=false, runtime-verify 降级回本机模拟
```

## 在 runtime-verify 中使用 (环境矩阵)

| 环境 | 何时用 | 姿势 |
|---|---|---|
| 本机 | 默认, 快速迭代 | 直接跑 |
| **远程 VM** | vm_available=true 时 System/Refactor 建议必跑一轮; 依赖敏感 / 破坏性场景 | `ssh athena-vm-{name} 'cd {workdir} && ...'` |

- 代码同步: VM 侧 `git clone/pull` 拉最新 commit, 或 `rsync` 工作区 (小改动); 注意 `git push` 受 stage 门禁
- 证据规则不变: **ssh 命令 + 远端输出原样晒进对话** (Goals 完成判定只认演示)
- `limits.max_session_minutes` 是预算护栏 (Loop Readiness 第 2 问), 超时中断并记录
