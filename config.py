import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Bot Credentials ──────────────────────────────
    API_ID        = int(os.environ.get("API_ID", 0))
    API_HASH      = os.environ.get("API_HASH", "")
    BOT_TOKEN     = os.environ.get("BOT_TOKEN", "")

    # ── Admin ─────────────────────────────────────────
    ADMIN_ID      = int(os.environ.get("ADMIN_ID", 0))

    # ── Database ──────────────────────────────────────
    MONGO_URI     = os.environ.get("MONGO_URI", "")

    # ── Links ─────────────────────────────────────────
    PLAYZONE_LINK = os.environ.get("PLAYZONE_LINK", "https://t.me/")
    SUPPORT_LINK  = os.environ.get("SUPPORT_LINK", "https://t.me/")

    # ── GIF Assets (from @assetshaibkl channel) ───────
    GIF_1_RUN     = "https://t.me/assetshaibkl/2"
    GIF_2_RUN     = "https://t.me/assetshaibkl/4"
    GIF_3_RUN     = "https://t.me/assetshaibkl/6"
    GIF_4_RUN     = "https://t.me/assetshaibkl/7"
    GIF_5_RUN     = "https://t.me/assetshaibkl/9"
    GIF_6_RUN     = "https://t.me/assetshaibkl/11"
    GIF_WICKET    = "https://t.me/assetshaibkl/12"
    GIF_WALKBACK  = "https://t.me/assetshaibkl/13"
    GIF_BOWLING   = ["https://t.me/assetshaibkl/15",
                     "https://t.me/assetshaibkl/16",
                     "https://t.me/assetshaibkl/17"]
    GIF_TROPHY    = "https://t.me/assetshaibkl/22"
    GIF_MATCH_START = "https://t.me/assetshaibkl/23"

    # ── Game Settings ─────────────────────────────────
    JOIN_TIMEOUT       = 120   # seconds
    BOWL_TIMEOUT       = 60    # seconds
    BAT_TIMEOUT        = 60    # seconds
    MIN_PLAYERS_SOLO   = 2
    MAX_PLAYERS_SOLO   = 20
    TOURNAMENT_TEAM_SIZE = 3
