import random
import logging
from config import Config

logger = logging.getLogger(__name__)

# Cache: link → file_id
_gif_cache: dict = {}

async def get_file_id(client, link: str) -> str | None:
    """Fetch file_id from a t.me channel post link."""
    if link in _gif_cache:
        return _gif_cache[link]
    try:
        # Parse channel username and message id from link
        # e.g. https://t.me/assetshaibkl/12
        parts = link.rstrip("/").split("/")
        username = parts[-2]
        msg_id   = int(parts[-1])
        msg = await client.get_messages(f"@{username}", msg_id)
        if msg and msg.animation:
            fid = msg.animation.file_id
        elif msg and msg.video:
            fid = msg.video.file_id
        elif msg and msg.document:
            fid = msg.document.file_id
        else:
            return None
        _gif_cache[link] = fid
        return fid
    except Exception as e:
        logger.warning(f"GIF fetch failed for {link}: {e}")
        return None

async def send_gif(client, chat_id: int, link: str, caption: str = ""):
    """Send a GIF/video by channel link."""
    fid = await get_file_id(client, link)
    if fid:
        try:
            return await client.send_animation(chat_id, fid, caption=caption, parse_mode="markdown")
        except Exception:
            try:
                return await client.send_video(chat_id, fid, caption=caption, parse_mode="markdown")
            except Exception as e:
                logger.warning(f"Send GIF failed: {e}")
    return None

async def send_run_gif(client, chat_id: int, runs: int, batter_name: str):
    run_map = {
        1: Config.GIF_1_RUN,
        2: Config.GIF_2_RUN,
        3: Config.GIF_3_RUN,
        4: Config.GIF_4_RUN,
        5: Config.GIF_5_RUN,
        6: Config.GIF_6_RUN,
    }
    run_captions = {
        1: f"1️⃣  Single taken — smart cricket! — **{batter_name}**",
        2: f"2️⃣  Two runs — excellent running between the wickets! — **{batter_name}**",
        3: f"3️⃣  Excellent running — three well-earned runs! — **{batter_name}**",
        4: f"🟢  FOUR! — Timed to perfection, races to the boundary! — **{batter_name}**",
        5: f"5️⃣  Five runs — rare sight, brilliant effort! — **{batter_name}**",
        6: f"🔥  SIX! — Absolutely smashed into the stands, what a strike! — **{batter_name}**",
    }
    link    = run_map.get(runs)
    caption = run_captions.get(runs, f"**{runs}** runs — **{batter_name}**")
    if link:
        await send_gif(client, chat_id, link, caption)

async def send_wicket_gif(client, chat_id: int, batter_name: str):
    caption = (
        f"❌  **WICKET!** — {batter_name} is gone! Brilliant delivery, no answer!\n\n"
        f"🚶  {batter_name} walks back — a short stay, a long walk home!"
    )
    await send_gif(client, chat_id, Config.GIF_WICKET, caption)
    # Also send walkback
    await send_gif(client, chat_id, Config.GIF_WALKBACK)

async def send_bowling_prompt_gif(client, chat_id: int):
    link = random.choice(Config.GIF_BOWLING)
    await send_gif(client, chat_id, link)

async def send_match_start_gif(client, chat_id: int):
    await send_gif(client, chat_id, Config.GIF_MATCH_START)

async def send_trophy_gif(client, chat_id: int, caption: str = ""):
    await send_gif(client, chat_id, Config.GIF_TROPHY, caption)
