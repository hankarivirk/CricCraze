from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

client = AsyncIOMotorClient(Config.MONGO_URI)
db = client["CricketManiaBot"]

# Collections
users_col      = db["users"]
stats_col      = db["stats"]
matches_col    = db["matches"]
tournament_col = db["tournaments"]
groups_col     = db["groups"]
