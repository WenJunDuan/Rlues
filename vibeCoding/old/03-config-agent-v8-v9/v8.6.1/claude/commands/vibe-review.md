增强代码审查:
1. 运行 `/review` 官方审查
2. 调用 validator 子代理: 测试+lint+类型检查
3. 调用 security-auditor 子代理: 安全扫描
4. 综合审查结果 → 写入 `.ai_state/review.md`
5. 经验沉淀 → 更新 pitfalls.md / patterns.md
