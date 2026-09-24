import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB", "nl2mongo_demo")]

db.users.delete_many({})
db.users.insert_many([
    {"name": "张伟", "age": 35, "email": "zhangwei@example.com", "city": "北京", "created_at": datetime(2025, 3, 12)},
    {"name": "李娜", "age": 28, "email": "lina@example.com", "city": "上海", "created_at": datetime(2025, 6, 1)},
    {"name": "王强", "age": 42, "email": "wangqiang@example.com", "city": "深圳", "created_at": datetime(2024, 11, 20)},
    {"name": "刘洋", "age": 31, "email": "liuyang@example.com", "city": "北京", "created_at": datetime(2026, 1, 5)},
    {"name": "陈静", "age": 26, "email": "chenjing@example.com", "city": "杭州", "created_at": datetime(2026, 7, 18)},
])
print("已插入 5 条测试数据")