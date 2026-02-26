# Memory Retrieval

## 检索目标
为当前任务返回最相关历史记忆，降低重复判断成本。

## 输入
- `tenant_id`
- `query`
- `command`
- `top_k`

## 混合检索策略（MVP）
0. 索引定位：
   - 先读取 `MEMORY.md` 获取分层文件入口。
   - 再按需读取 `memory/projects.md`、`memory/lessons.md`、`memory/YYYY-MM-DD.md`。
1. Keyword 检索：
   - 对 `summary/issues/evidence` 文本做关键词匹配。
   - 计算命中词数量作为 `keyword_score`。
2. Semantic 检索：
   - 当前阶段使用轻量近似（词项重叠 + 字段权重）代替真实向量检索。
   - 预留后续替换向量库接口。
3. 融合排序：
   - `final_score = 0.6 * keyword_score + 0.4 * semantic_score`。
   - 返回 `top_k` 条结果。

## 过滤规则
1. 强过滤 `tenant_id`。
2. 同 `command` 结果优先。
3. 超过 30 天的记忆默认降权。

## 输出字段
- `task_id`
- `session_id`
- `summary`
- `score`
- `created_at`

## 失败降级
- 检索失败返回空列表，不阻断主流程。
- 必须记录结构化错误并可追踪。
