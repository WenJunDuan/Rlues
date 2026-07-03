# vibe-archive

将 done.md 中的已完成任务归档到 archive.md。

## 语法

```bash
vibe-archive               # 归档所有已完成
vibe-archive --keep=5      # 保留最近5条在 done.md
```

## 执行流程

```
1. 读取 done.md
2. 将内容追加到 archive.md (带时间戳分隔)
3. 清空或保留 done.md
4. 更新 session.md
```
