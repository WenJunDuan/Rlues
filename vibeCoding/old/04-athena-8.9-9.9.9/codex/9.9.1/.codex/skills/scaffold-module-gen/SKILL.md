---
name: scaffold-module-gen
description: >-
  Use when the user wants to generate a new business module, page, or CRUD
  feature in an existing enterprise scaffold (backend or frontend) from a
  requirement description. Reads the target scaffold's Convention Pack
  (conventions + templates + validate command), generates code that matches the
  scaffold's layering/naming/permission conventions, then closes the loop by
  running the scaffold's compile/build command and self-repairing on failure.
  This is a dev-time codegen skill — it writes source files, it does NOT read
  runtime data (use project-data-reader for that).
---

# scaffold-module-gen

生成期代码脚手架 skill。**脚手架无关**：它本身不懂任何具体框架，全部框架知识来自
目标脚手架发布的 **Convention Pack（约定包）**。换一个脚手架 = 换一份 Convention Pack，本 skill 不改。

## 何时使用

- "给我在 quantum-backend 生成一个 XX 业务模块（含列表/详情/增删改查/权限点）"
- "在 quantum-front 加一个 XX 管理页面"
- 任何"按需求 + 依赖某个框架约定，快速产出可编译模块骨架"的场景

## 何时**不**使用

- 需要读取**正在运行**的系统里的真实数据 → 用 `project-data-reader`
- 自由发挥、不依赖任何既有框架约定的一次性脚本

## 输入

1. `scaffold_id`：目标脚手架标识（如 `quantum-backend` / `quantum-front` / `<client>`）
2. 需求描述：实体字段、需要的操作、权限点、菜单归属等

## 工作流（模板定骨架 · AI 填语义 · 编译器兜底）

1. 定位并加载 `scaffold_id` 对应的 Convention Pack：
   - `conventions.md`（分层 / 命名 / 权限 / 数据权限约定）
   - `templates/`（各层骨架模板）
   - `validate.md`（校验命令与自修流程）
2. 依需求把模板实例化成各层文件（后端：entity/mapper/serviceImpl/controller/DTO/convert/权限点/菜单 SQL；
   前端：page/api/route/组件）。**结构照模板，业务语义由你填**。
3. 运行 Convention Pack 声明的**校验命令**（如 `mvn -q -pl <module> -am compile` / `pnpm build`）。
4. 校验失败 → 读编译/构建错误 → 定点修复 → 回到 3，直到通过。
5. 产出可编译的模块骨架 + 菜单/权限落库 SQL，并列出新增/修改的文件清单。

## 铁律

- **绝不**从零凭记忆写整模块——必用 Convention Pack 的模板，避免偏离既有约定。
- **绝不**在生成代码里自建认证/权限——沿用目标框架的权限注解与数据权限约定。
- 生成后**必须**跑一遍校验命令，未通过不算完成。

## 与 aether/pace 集成

本目录即一个标准 Agent Skill，直接放进 aether/pace 的 skills 目录、与 vm 叠加即可。
各脚手架的 Convention Pack 由各脚手架仓库自带（quantum-backend 见 `docs/ai/convention-pack/`）。
