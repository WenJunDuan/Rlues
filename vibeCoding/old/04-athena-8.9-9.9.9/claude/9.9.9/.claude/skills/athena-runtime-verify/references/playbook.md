# Runtime verify 9.9.9

可执行入口是 `athena-vm/scripts/runtime-run.py`（snapshot / doctor / run）。`/goal` 仅在用户显式要求或已有 Goal 时作为可选增强，不是唯一通道。

先从当前 design 的 Done Contract 选出可判断的真实场景、required/advisory 环境、预算和允许副作用。项目 runtime-env 提供准备/探活/断言/清理命令；缺必需条件时保持未验证，继续不依赖它的授权工作。

1. 按 `athena-vm/references/playbook.md` 生成 scenario JSON 与受控工作树 bundle。明确允许的未跟踪输入，必需输入用 `--required-input`；不要用只含 HEAD 的 clone/pull 代替待测工作区。
2. 用 `../athena-vm/scripts/runtime-run.py doctor` 检查所需 transport，用 `run` 校验输入、prepare→ready→command→teardown。无 VM 合同的项目直接 local 闭环；required RHEL 等环境不可用时不能以 local 通过替代。
3. 根据真实结果归因：输入拒绝修输入；prepare/ready 修环境；断言失败回 impl；超时/未知保留缺口与 run 资源标识。只复跑受影响及必要回归，不重复派发已经完成且输入仍有效的场景。
4. 将结果 artifact 路径/哈希、对应 AC、环境和未覆盖原因写入当前 sprint `runtime-verify.md` / 既有 evidence。runner 不拥有另一份 PACE 状态，也不替主 agent 宣称通过。

```bash
python3 ~/.claude/skills/athena-vm/scripts/runtime-run.py run --help
python3 ~/.claude/skills/athena-vm/scripts/runtime-run.py run --bundle <input.tar.gz> --contract <design.md> --scenario <scenario.json> --output <result.json> --runner local --requirement required --timeout 60
```

result 的 input_manifest_sha256/contract_sha256/scenario_sha256/environment_sha256 绑定实际输入与非敏感环境；相关代码/合同/环境变化后旧证据失效。业务运行证据可被另一端消费；原生平台协议需要对应端证据。只打印必要的脱敏结果，不将完整远端环境或凭证晒进对话。

主 agent 的 runtime-verify.md 保留 `## 完成条件与停止条件`、`## 测试场景`、`## 自测自改记录`、`## Reflect`、`## VERDICT`。表中每行引用实跑输出并明确 PASS/FAIL/BLOCKED，未运行不能 PASS。Reflect 仅对照当前合同补缺口；后续阶段按 pace/stages.md 路由，System/Refactor 为 runtime-verify→polish→一次独立 review。
