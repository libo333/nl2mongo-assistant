# nl2mongo-assistant

自然语言转 MongoDB 查询助手：输入一句话，自动生成并执行 MongoDB 查询，返回结果和解释。

## 功能

- [x] FastAPI 服务骨架 + 基础路由
- [x] NL → MongoDB 查询生成（DeepSeek / OpenAI 兼容接口）
- [x] 查询安全校验（只读、limit 上限、写操作拦截）
- [x] 查询执行（find / aggregate）+ BSON 序列化
- [x] 一体化接口 `/query/run`（生成 + 执行一步完成）
- [x] Schema 自动推断
- [ ] 多轮对话（上下文追问）
- [ ] 前端页面

## 快速开始

```bash
# 1. 环境
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2. 依赖
pip install -r requirements.txt

# 3. 配置（参考 .env.example）
cp .env.example .env            # 填入 LLM_API_KEY 等

# 4. 造测试数据
python seed_data.py

# 5. 启动
uvicorn main:app --reload
```

访问 http://localhost:8000/docs 查看接口文档。

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 服务状态 |
| GET | `/health` | 健康检查 |
| POST | `/query` | NL → 生成 MongoDB 查询 |
| POST | `/query/execute` | 执行给定查询 |
| POST | `/query/run` | 一体化：生成 + 执行 |
| GET | `/schema/{collection}` | 自动推断集合 schema |

## 项目结构

```
nl2mongo-assistant/
├── main.py            # FastAPI 入口、路由、LLM 调用、查询执行
├── seed_data.py       # MongoDB 测试数据脚本
├── requirements.txt
├── .env               # 本地配置（不提交）
├── .env.example       # 配置模板
└── README.md
```

## 配置说明（.env）

```env
LLM_API_KEY=sk-...                     # DeepSeek / OpenAI key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=nl2mongo_demo
```

## 安全设计

- LLM 输出双层校验：Prompt 约束 + 后端 `validate_query` 强制检查
- 仅允许 `find` / `aggregate`，拦截 `$out`、`$merge`、`$where`
- 所有查询强制 limit 上限（默认 20，最大 100）
- `.env` 含密钥，已加入 `.gitignore`

## License

MIT