# P.A.C.E. Complexity Router

## Path A - Quick Fix
- 单文件, <30行
- Workflow: R1 → E → R2
- Duration: 30-60分钟

## Path B - Planned Development
- 2-10文件
- Workflow: R1 → I → P → E → R2
- Duration: 2-8小时

## Path C - System Development
- >10文件, 跨模块
- Workflow: 完整九步
- Duration: 数天-数周

## Selection Rules
```yaml
criteria:
  file_count: [1, 2-10, >10]
  code_lines: [<30, 30-500, >500]
  architecture_impact: [none, minor, major]
```
