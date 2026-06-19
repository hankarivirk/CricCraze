import asyncio
import logging
import pyromod  # noqa: F401  — patches pyrogram.Client with .listen() used in plugins/solo.py & team_gameplay.py
from pyrogram import Client
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

plugins = dict(root="plugins")

app = Client(
    "CricketManiaBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=plugins
)

async def main():
    async with app:
        me = await app.get_me()
        logger.info(f"✅ @{me.username} — {me.first_name} is LIVE!")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
