# 活体误拦样本（最小等价复现，逐一经今日发行 guard 实测 BLOCK）

规范化说明（rev 7 复核 P1-1 要求）：原始命令为本会话数百行的 python heredoc 脚本，此处为**最小等价样本**——保留触发机制的最短形式，每条已用今日 `pre-bash-guard.cjs` 的 `analyze()` 实测复现记载的拦截原因（验证脚本 /tmp/verify_samples3.js，2026-09-20）。触发机制勘定：shell 双引号内反引号替换与 `$(` 是活性的，python 源码里的 markdown 反引号/示例文本因此被当 shell 结构解析。

## 形态 1 · 奇数反引号（python strip 参数）→ 实测 `unparsable command substitution`

```
python3 - <<'PYEOF'
cells = [c.strip().strip("*`") for c in t.split("|")]
PYEOF
```

## 形态 2 · 双引号串内成对反引号包住危险示例 → 实测 `recursive force removal of root/home`

```
python3 - <<'PYEOF'
e = e.replace("`cat <<EOF | rm -rf /` 同行段", "x")
PYEOF
```

## 形态 3 · 双引号串内奇数反引号（markdown 行内代码截断）→ 实测 `unparsable command substitution`

```
python3 - <<'PYEOF'
t = "`heredocSpans(command)`（CX `heredoc_spans"
PYEOF
```

## 形态 4 · 双引号串内未闭合 `$(` → 实测 `unparsable command substitution`

```
python3 - <<'PYEOF'
s = "正文里出现未闭合的 $(a + b"
PYEOF
```

## 正向样本（本会话真实命令首行，今日未拦、须持续放行）

```
tee -a .ai_state/sprints/2026-09-20-review-binding-preflight/session-log.md >/dev/null <<'EOF'
tee .ai_state/sprints/2026-09-20-contract-parser-diagnostics/cleanup-pass.md >/dev/null <<'EOF'
```

## 白名单覆盖核验

四形态首行 `python3 - <<'PYEOF'`：TOKEN(`python3`) SP TOKEN(`-`) `<<` `'PYEOF'` 行尾，首 token `python3` ∈ 消费者集合 → 窄形 quoted → 正文掩码 → 误拦消除。正向样本首行 `tee` + 路径 WORD（`.`/`/`/`-` 均在字符集）+ `>/dev/null` REDIR + 行尾定界符，`tee` ∈ 消费者集合 → 窄形。
