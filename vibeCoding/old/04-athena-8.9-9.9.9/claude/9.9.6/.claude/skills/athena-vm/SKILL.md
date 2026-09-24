---
name: athena-vm
description: 把用户虚拟机注册为 runtime-verify 的真实环境。需要 VM 环境或跑 setup / doctor 时触发。
---

# /athena-vm — VM 运行时接入 (v9.9.6)

## 为什么存在

runtime-verify 的"不同环境"此前只有本机 (空库/满库/慢网络都是模拟). 真实 VM 提供:
- 干净环境 (无本机全家桶依赖) 暴露隐式依赖
- 真实 Linux 发行版 / 版本差异 (本机 macOS ≠ 生产 Ubuntu)
- 破坏性测试的隔离沙箱 (敢 rm 敢压测)

## 不做

- ❌ 不当部署工具 (VM 是验证环境, 不是生产; 部署是 ship 之后人的决定)
- ❌ 不存明文密码 (见上, 硬拒绝)
- ❌ 不把 SSH 别名描述成权限边界. 实际授权由本机 rules/settings、approval policy 与 sandbox 决定; 本 skill 只约定使用 `athena-vm-*` 别名并在执行前核对目标
- CX 端注: Codex Remote 已 GA + DigitalOcean Droplet Workspace 插件是原生远程路径, 本 skill 的 ssh 别名方案两端通用; CX 原生方案作为增强可选

## 详细 playbook

完整工作流、模板、schema 与联动细节见 `references/playbook.md` —— 按需 Read, 不进热路径。
