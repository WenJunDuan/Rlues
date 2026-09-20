# 活体误拦样本原文（本会话，主 agent 自身命令被安装态 pre-bash-guard 拦截）

计数说明：session-log 记 6 次拦截事件，去重后为 4 个命令形态（形态 1 触发 3 次、形态 2/3/4 各 1 次）。全部首行 = `python3 - <<'PYEOF'`（quoted 单声明、行尾定界符）。

## 形态 1（×3）：heredoc 正文含正则 `$|` 与管道字符 → BLOCKED: unparsable command substitution

```
python3 - <<'PYEOF'
import re
HEAD = re.compile(r"^#{1,6}\s*\**\s*(?:done contract|acceptance criteria|验收标准)(?=$|[\s*:：()（）\[\]【】·—-])", re.I)
cells = [c.strip() for c in t.strip("|").split("|")]
PYEOF
```

## 形态 2（×1）：正文引用危险命令示例文本（设计文档字符串）→ BLOCKED: unparsable command substitution

```
python3 - <<'PYEOF'
d = d.replace('正文里举例的 $(rm -rf /) 仍被递归分析', '...')
e = e.replace("`cat <<EOF | rm -rf /` 同行段", "...")
PYEOF
```

## 形态 3（×1）：正文为 review receipt JSON，引用 `&& rm -rf /` 反例文本 → BLOCKED: recursive force removal of root/home

```
python3 - <<'PYEOF'
body = '行续反斜杠形态（cat <<EOF \\ 换行 && rm -rf /）bash 真执行续行命令'
json.dump({"output": body}, open("result.json","w"))
PYEOF
```

## 形态 4（×1）：正文含奇数反引号（markdown 行内代码被换行截断）→ BLOCKED: unparsable command substitution

```
python3 - <<'PYEOF'
s = "负向夹具以字面量内联（含首轮活体命中行「### AC 标识一律从合同结构提取（#7）」）"
t = "`heredocSpans(command)`（CX `heredoc_spans"
PYEOF
```

## 白名单覆盖核验

四形态首行均为 `python3 - <<'PYEOF'`：TOKEN(`python3`) SP TOKEN(`-`) SP `<<` QUOTED_DELIM(`'PYEOF'`) 行尾 → 全部落白名单窄形 quoted 分支 → 正文掩码 → 误拦消除。本会话另有 `tee -a <path> >/dev/null <<'EOF'`、`cat >> <path> <<'EOF'` 形态的 heredoc **未**被拦（正文恰好无触发字符），同样落白名单（WORD/REDIR token），一并纳入 AC1 重放矩阵作正向样本。
