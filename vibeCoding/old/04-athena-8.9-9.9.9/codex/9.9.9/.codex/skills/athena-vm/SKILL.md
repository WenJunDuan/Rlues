---
name: athena-vm
description: 把用户虚拟机注册为 runtime-verify 的真实环境。需要 VM 环境或跑 setup / doctor 时触发。
---

# /athena-vm — VM 运行时接入 (v9.9.9)

真实入口：`scripts/configure-vm.py` 写私有 `~/.athena/vm.json`；`scripts/runtime-run.py snapshot|doctor|run` 执行验证。使用和输出协议见 `references/playbook.md`。配置存在、SSH 可达、项目场景 ready 是不同事实。单端 CC 或 CX 都可独立调用；VM 是项目合同选择的环境，不是全局门禁。

## 为什么存在

runtime-verify 的"不同环境"此前只有本机 (空库/满库/慢网络都是模拟). 真实 VM 提供:
- 干净环境 (无本机全家桶依赖) 暴露隐式依赖
- 真实 Linux 发行版 / 版本差异 (本机 macOS ≠ 生产 Ubuntu/RHEL)
- 破坏性测试的隔离沙箱 (敢 rm 敢压测)

## 包内自带（fresh install 不依赖旧版）

发行包自带 schema 与示例，**不**从已装 9.9.8 或 `~/.athena/vm.json` 抄：

| 文件 | 用途 |
|---|---|
| `templates/vm.json.example` | 无秘密的配置样例；复制到 `~/.athena/vm.json` 后填真实 host/key |
| `references/vm.schema.json` | 字段与禁止明文密码的校验 |
| `scripts/runtime-run.py` | snapshot / doctor / run |

```bash
python3 ~/.agents/skills/athena-vm/scripts/runtime-run.py --help
python3 ~/.agents/skills/athena-vm/scripts/runtime-run.py doctor --runner local
python3 ~/.agents/skills/athena-vm/scripts/runtime-run.py doctor --runner ssh --vm dev
```

复用已有 `~/.athena/vm.json`（chmod 600）和现有认证，不输出凭证、不写 SSH/host 配置。SSH 目标与原生授权仍有效；不把连接能力当生产部署或破坏性操作授权。

## 不做

- ❌ 不当部署工具 (VM 是验证环境, 不是生产; 部署是 ship 之后人的决定)
- ❌ 不存明文密码 (schema 拒绝 `"password"` 字段)
- ❌ 不把 SSH 别名描述成权限边界. 实际授权由本机 rules/settings、approval policy 与 sandbox 决定
- ❌ 没有 VM 时不阻塞本机闭环

## 详细 playbook

完整工作流、schema、snapshot/run 协议见 `references/playbook.md`。
