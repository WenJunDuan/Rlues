---
name: athena-vm
description: |
  VM 运行时接入 (v9.9.1). 把用户的虚拟机注册为 runtime-verify 的真实环境矩阵一员.
  子命令: setup (引导注册 + 写 ~/.athena/vm.json + SSH 别名) / doctor (连通性自检) / 用法速查.
  安全底线: 明文密码永不落盘 — key 认证优先, 密码只存环境变量名引用.
---

# /athena-vm — VM 运行时接入 (v9.9.1, Codex)

## 为什么存在

runtime-verify 的"不同环境"此前只有本机 (空库/满库/慢网络都是模拟). 真实 VM 提供:
- 干净环境 (无本机全家桶依赖) 暴露隐式依赖
- 真实 Linux 发行版 / 版本差异 (本机 macOS ≠ 生产 Ubuntu)
- 破坏性测试的隔离沙箱 (敢 rm 敢压测)

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

## 不做

- ❌ 不当部署工具 (VM 是验证环境, 不是生产; 部署是 ship 之后人的决定)
- ❌ 不存明文密码 (见上, 硬拒绝)
- ❌ 不把 SSH 别名描述成权限边界. 实际授权由本机 rules/settings、approval policy 与 sandbox 决定; 本 skill 只约定使用 `athena-vm-*` 别名并在执行前核对目标
- CX 端注: Codex Remote 已 GA + DigitalOcean Droplet Workspace 插件是原生远程路径, 本 skill 的 ssh 别名方案两端通用; CX 原生方案作为增强可选
