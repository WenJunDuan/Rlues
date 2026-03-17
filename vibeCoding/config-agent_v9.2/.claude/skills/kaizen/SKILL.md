---
name: kaizen
description: 交付后复盘 — V 阶段使用
context: main
---
## 管道位置: V → 追加 knowledge.md + lessons.md

## 复盘问题
1. 哪些代码/模式值得记录以便下次复用? → knowledge.md
2. 遇到了什么坑? 怎么解决的? → lessons.md
3. 有没有"差不多就行"的妥协? 能改进吗?
4. 时间估计准吗? 哪里偏差大?

## 产出格式
```markdown
# knowledge.md 追加
## [日期] JWT认证
- 使用 jose 库签发/验证 JWT
- refresh_token 存 httpOnly cookie

# lessons.md 追加
## [日期] JWT认证
- 坑: jsonwebtoken 库不支持 ESM, 改用 jose
- 改进: 初期应检查框架兼容性再选库
```
