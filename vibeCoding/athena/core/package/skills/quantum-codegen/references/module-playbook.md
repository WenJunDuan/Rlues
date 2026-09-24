<!-- quantum-codegen playbook (前身独立 skill; 现为 quantum-codegen 的 mode 参考) -->

# quantum-codegen · mode=module

生成期代码脚手架 skill。**脚手架无关**：它本身不懂任何具体框架，全部框架知识来自
目标脚手架发布的 **Convention Pack（约定包）**。换一个脚手架 = 换一份 Convention Pack，本 skill 不改。

## 何时使用

- "给我在 quantum-backend 生成一个 XX 业务模块（含列表/详情/增删改查/权限点）"
- "在 quantum-front 加一个 XX 管理页面"
- 任何"按需求 + 依赖某个框架约定，快速产出可编译模块骨架"的场景

## 何时**不**使用

- 需要读取**正在运行**的系统里的真实数据 → 用 `quantum-data`
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

## PACE 集成

- plan/design：从需求与 Convention Pack 冻结模块边界、权限点和验收标准。
- impl：按模板生成代码，使用 `athena run --covers ACn -- <校验命令>` 留证据。
- runtime-verify/review：需要真实服务时按 runtime-env 实跑，再由一次独立 review 核对需求、产物与证据。

各脚手架的 Convention Pack 由各脚手架仓库自带（quantum-backend 见 `docs/ai/convention-pack/`）。
