from database import users_col, groups_col
from datetime import datetime

# ── Users ─────────────────────────────────────────────────────────────────────

async def add_user(user_id: int, username: str = "", full_name: str = ""):
    await users_col.update_one(
        {"_id": user_id},
        {"$setOnInsert": {
            "_id": user_id,
            "username": username,
            "full_name": full_name,
            "joined": datetime.utcnow()
        }},
        upsert=True
    )

async def get_all_users():
    return await users_col.find({}, {"_id": 1}).to_list(length=None)

async def get_user_count():
    return await users_col.count_documents({})

async def get_user(user_id: int):
    return await users_col.find_one({"_id": user_id})

# ── Groups ────────────────────────────────────────────────────────────────────

async def add_group(chat_id: int, title: str = ""):
    await groups_col.update_one(
        {"_id": chat_id},
        {"$setOnInsert": {
            "_id": chat_id,
            "title": title,
            "joined": datetime.utcnow()
        }},
        upsert=True
    )

async def get_all_groups():
    return await groups_col.find({}, {"_id": 1}).to_list(length=None)

async def get_group_count():
    return await groups_col.count_documents({})
