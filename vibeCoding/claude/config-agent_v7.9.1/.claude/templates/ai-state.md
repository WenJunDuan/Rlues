# .ai_state/ 目录模板

初始化后的目录结构：

```
.ai_state/
├── requirements/        # 需求文档
│   └── .gitkeep
├── designs/             # 设计文档
│   └── .gitkeep
├── experience/          # 经验库
│   ├── index.md         # 经验索引
│   └── learned/         # 自动提取的模式
│       └── .gitkeep
├── checkpoints/         # 验证检查点
│   └── .gitkeep
├── context/             # 知识库索引
│   └── index.md
└── meta/                # 元信息
    ├── session.lock     # 会话锁
    ├── kanban.md        # 看板
    └── errors.md        # 错误记录
```

## 使用说明

- `requirements/`: 存放需求文档 (REQ-xxx.md)
- `designs/`: 存放设计文档 (DESIGN-xxx.md)
- `experience/`: 存放经验和自动提取的模式
- `checkpoints/`: 存放验证检查点
- `meta/`: 存放会话状态和看板
