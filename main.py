import json
import os
import re
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field
from bson import ObjectId
from pymongo import MongoClient

mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client[os.getenv("MONGO_DB", "nl2mongo_demo")]

load_dotenv()

app = FastAPI(
    title="nl2mongo-assistant",
    description="自然语言转 MongoDB 查询助手",
    version="0.2.0",
)

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
)

# ---------- 数据模型 ----------

class QueryRequest(BaseModel):
    question: str = Field(..., description="自然语言问题", examples=["查询年龄大于30岁的用户"])
    collection: str = Field(..., description="集合名", examples=["users"])
    schema: dict = Field(
        default={},
        description="集合的字段结构，如 {\"name\": \"string\", \"age\": \"number\"}",
        examples=[{"name": "string", "age": "number", "created_at": "date"}],
    )
    limit: int = Field(default=20, ge=1, le=100, description="返回条数上限")

class QueryResponse(BaseModel):
    collection: str
    mongo_query: dict
    explanation: str

class ExecuteRequest(BaseModel):
    collection: str
    mongo_query: dict
    limit: int = Field(default=20, ge=1, le=100)

def serialize(doc):
    """把 ObjectId 等 BSON 类型转成 JSON 可序列化的格式"""
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc
# ---------- Prompt ----------

SYSTEM_PROMPT = """你是一个 MongoDB 查询生成器。用户会给你集合的字段结构(schema)和一个自然语言问题。
你的任务是把问题转换成 MongoDB 查询，并严格按以下 JSON 格式返回（不要输出任何其他内容）：

{
  "operation": "find | aggregate",
  "filter": {},            // find 时的查询条件；aggregate 时留空对象
  "pipeline": [],          // aggregate 时的聚合管道数组；find 时留空数组
  "projection": {},        // 要返回的字段，1 表示返回
  "sort": {},              // 排序，如 {"age": -1}
  "explanation": "对这个查询的简短中文解释"
}

规则：
1. 只输出合法 JSON，不要 markdown 代码块，不要解释性文字
2. 只允许 find 和 aggregate 两种操作，禁止 update/insert/delete/drop
3. 所有查询必须只读、安全
4. 不确定的字段宁可不用，也不要瞎编字段名
5. 日期一律用 ISO 格式字符串，如 "2026-01-01T00:00:00Z"
6. 模糊匹配用正则表达式，如 {"name": {"$regex": "张", "$options": "i"}}
"""

def nl_to_mongo(question: str, collection: str, schema: dict) -> dict:
    user_msg = (
        f"集合名：{collection}\n"
        f"字段结构：{json.dumps(schema, ensure_ascii=False)}\n"
        f"问题：{question}"
    )
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "deepseek-chat"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0,  # 查询生成要稳定，不要创造性
        response_format={"type": "json_object"},  # 强制 JSON 输出
    )
    return json.loads(resp.choices[0].message.content)

# ---------- 安全校验 ----------

ALLOWED_OPS = {"find", "aggregate"}
MAX_LIMIT = 100

def validate_query(q: dict, limit: int) -> dict:
    op = q.get("operation", "find")
    if op not in ALLOWED_OPS:
        raise HTTPException(400, f"不允许的操作：{op}（只允许 find/aggregate）")

    # 检查管道里有没有写操作
    for stage in q.get("pipeline", []):
        if any(k.startswith("$") and k in {"$out", "$merge"} for k in stage):
            raise HTTPException(400, "聚合管道包含写操作，已拦截")

    q["limit"] = min(limit, MAX_LIMIT)
    if op == "find" and "$where" in json.dumps(q.get("filter", {})):
        raise HTTPException(400, "包含 $where，已拦截（存在注入风险）")
    return q

# ---------- 路由 ----------

@app.get("/")
def root():
    return {"message": "nl2mongo-assistant is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    try:
        raw = nl_to_mongo(req.question, req.collection, req.schema)
        safe = validate_query(raw, req.limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"LLM 生成失败：{e}")

    return QueryResponse(
        collection=req.collection,
        mongo_query=safe,
        explanation=safe.pop("explanation", ""),
    )

@app.post("/query/execute")
def execute_query(req: ExecuteRequest):
    # 复用安全校验，防止有人绕过 /query 直接提交恶意查询
    safe = validate_query(req.mongo_query, req.limit)
    coll = db[req.collection]

    try:
        if safe["operation"] == "find":
            cursor = coll.find(
                safe.get("filter", {}),
                safe.get("projection") or None,
            )
            if safe.get("sort"):
                cursor = cursor.sort(list(safe["sort"].items()))
            docs = [serialize(d) for d in cursor.limit(safe["limit"])]
        else:  # aggregate
            pipeline = list(safe.get("pipeline", []))
            pipeline.append({"$limit": safe["limit"]})   # 强制加 limit
            docs = [serialize(d) for d in coll.aggregate(pipeline)]
    except Exception as e:
        raise HTTPException(500, f"查询执行失败：{e}")

    return {"count": len(docs), "data": docs}