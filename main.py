from fastapi import FastAPI

app = FastAPI(
    title="nl2mongo-assistant",
    description="自然语言转 MongoDB 查询助手（骨架版）",
    version="0.1.0",
)

@app.get("/")
def root():
    return {"message": "nl2mongo-assistant is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/query")
def query(text: str):
    """占位接口：后续把自然语言转成 MongoDB 查询"""
    return {
        "input": text,
        "mongo_query": None,
        "note": "TODO: 接入 NL2Mongo 转换逻辑",
    }