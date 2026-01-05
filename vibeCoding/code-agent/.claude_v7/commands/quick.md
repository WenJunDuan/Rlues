---
description: 快速开发，Path A，静默执行
---

# /quick - 快速开发

**触发词**: 快速、简单、bug修复、小改动

**路径**: Path A (单文件/<30行/纯修复)

## 工作流

```
R1感知 → E执行 → R2验收
```

## 执行步骤

### R1 - RESEARCH
```
1. memory.recall(project_path)
2. sou.search 定位相关代码
3. 快速评估确认符合Path A
```

### E - EXECUTE
```
1. codex skill 静默执行
2. 不创建文档/不测试/不编译
3. 失败自动重试(max 3)
```

### R2 - REVIEW
```
1. 寸止请求验收
2. 只展示结果，不冗长解释
```

## 适用条件

- [ ] 单文件修改
- [ ] <30行代码
- [ ] 纯修复/优化
- [ ] 无架构影响

## 超出范围

发现以下情况 → 升级到 /dev：
- 涉及文件 >1个
- 需要架构调整
- 影响多个模块

## 示例

```
用户: "修复登录按钮不响应"
→ Path A
→ R1: sou.search("登录按钮 onClick")
→ E: codex "修复点击事件绑定 @src/Login.tsx"
→ R2: 寸止验收
```
