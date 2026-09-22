# nl2mongo-assistant

自然语言转 MongoDB 查询助手：输入一句话，输出可执行的 MongoDB 查询。

## 功能

- [x] FastAPI 服务骨架 + 基础路由
- [ ] NL → MongoDB 查询语句转换
- [ ] MongoDB 连接与查询执行
- [ ] 查询结果自然语言解释

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

访问 http://localhost:8000/docs 查看接口文档。

## 项目结构

```
nl2mongo-assistant/
├── main.py           # FastAPI 入口与路由
├── requirements.txt
└── README.md
```

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 服务状态 |
| GET | `/health` | 健康检查 |
| POST | `/query` | NL 查询（占位） |

## License

MIT