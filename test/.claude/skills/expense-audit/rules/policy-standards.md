# 报销制度标准参考

> 本文件为规则层提供制度参考数据。规则（amount-check、category-match）在判定时引用此处的标准值。

## 职级报销限额

| 职级 | 单次限额 (CNY) | 说明 |
|------|--------------|------|
| L1 | 500 | 初级员工 |
| L2 | 1,200 | 中级员工 |
| L3 | 2,000 | 高级员工 |
| L4 | 3,500 | 管理层 |

未匹配到职级时，使用默认限额 **800 CNY** 并标记 `warning`。

## 部门允许报销类目

| 部门 | 允许类目 |
|------|---------|
| finance | transport, hotel, meal, office |
| sales | transport, hotel, meal, client |
| hr | transport, hotel, meal, training |

未匹配到部门时，使用默认类目集 `[transport, hotel, meal]` 并标记 `warning`。

## 敏感类目

以下类目需要额外备注说明业务场景，缺失则标记 `warning`：
- gift（礼品）
- entertainment（招待）
- client（客户招待）

## 引用方式

规则中引用格式：`policy://expense/limit`、`policy://expense/category`。
