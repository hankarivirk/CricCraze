import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from database.users import add_user, add_group
import utils.state as state

logger = logging.getLogger(__name__)

START_TEXT = """
🏏  **CRICKET MANIA** — *where legends are born*

🎙  *Live the game. Feel the roar.*

Real ball-by-ball cricket — straight in your Telegram group.
No app needed. No drama. Pure *cricket.*

⚔️  **CHOOSE YOUR BATTLE**
┣  👥  Team Match — *Two sides. One champion.*
┗  🧍  Solo Match — *Every man for himself.*

🏆  **WHAT'S IN THE PITCH**
┣  🎯  Live gameplay — *ball by ball*
┣  📊  Scorecards that update in *real-time*
┣  🪙  Toss · Overs · Captains
┣  🎩  Hat-tricks & 💯 Century alerts
┗  🏅  Player of the Match — *you could be next*

💥  Ready to play? Add me to your group — type /start

🔇  *Psst — your group will never be the same again* 😈
"""

HELP_TEXT = """
📖  **CRICKET MANIA — HELP**

*Choose a game mode to get started* 👇
"""

SOLO_HELP = """
🧍  **SOLO MATCH — COMMANDS**

`/start` — New match shuru karo
`/join_solo` — Solo match join karo
`/leave_solo` — Match se niklo (before start)
`/solo_list` — Joined players dekho
`/solo_score` — Live scorecard
`/start_solo` — Force start *(Group Admin)*
`/extend_solo` — Joining +30 sec *(Group Admin)*
`/resume_solo` — Match resume *(Group Admin)*
`/end_solo` — Match khatam karo *(Group Admin)*

━━━━━━━━━━━━━━━━━━━━
🧍  **HOW TO PLAY — SOLO**

🚀  `/start` → Solo Match → overs choose karo
👥  Min **2**, Max **20** players
🎯  Bowler — **DM** mein secret number bhejo
🏏  Batter — **Group** mein 1 to 6 type karo
❌  Same number = **WICKET**
✅  Different = **Runs** (batter's number counts)
⚠️  Time out = auto OUT / dot ball penalty
🏆  Highest scorer **WINS!**
"""

TEAM_HELP = """
👥  **TEAM MATCH — COMMANDS**

`/start` — Match shuru karo (tu Host banega)
`/host` — Current host kaun hai
`/create_teams` — Team joining kholo *(Host)*
`/recreate_teams` — Reset & reopen *(Host)*
`/join_A` `/join_B` — Team join karo
`/add_A` `/add_B` — Force add *(Host)*
`/remove` — Player remove *(Host)*
`/members_list` — Teams & players dekho
`/choose_caps` — Captains select *(Host)*
`/set_overs` — Overs set karo *(Captain)*
`/batting` — Next batter choose *(Captain)*
`/bowling` — Bowler choose *(Captain)*
`/score` — Live scorecard
`/change_host` — Host change vote
`/change_cap` — Captaincy transfer *(Host)*
`/end_match` — Match khatam *(Host/Admin)*

━━━━━━━━━━━━━━━━━━━━
👥  **HOW TO PLAY — TEAM**

🚀  `/start` → Team Match → Tu Host
👥  `/create_teams` → Team A & B joining
👑  `/choose_caps` → Captains select karo
🪙  Toss automatic — coin flip!
⚙️  Toss winner → Bat ya Bowl choose
📏  Captain → `/set_overs`
🎯  Bowler → DM mein secret number
🏏  Batter → Group mein 1-6 type karo
❌  Same = WICKET  |  ✅  Different = Runs
🔄  Innings change → Target chase!
🏆  Higher score **WINS!**

⚠️  *Bowler must /start the bot in DM first!*
"""

TOURNAMENT_HELP = """
🏆  **TOURNAMENT MODE — HOW TO PLAY**

🚀  `/tournament` — Tournament shuru karo
👥  Teams banao: A, B, C... (3 players each)
🎮  Har team dono se khele (Round Robin)
🏅  Finals mein top 2 teams!
👑  **Host bhi khel sakta hai!**

Commands:
`/tournament` — Naya tournament start
`/t_join_A` `/t_join_B` `/t_join_C` — Team join
`/t_start` — Tournament begin *(Host)*
`/t_score` — Tournament standings
`/t_end` — Tournament khatam *(Host/Admin)*
"""

STATS_HELP = """
📊  **STATS & LEADERBOARD**

`/stats` — Apni stats dekho
`/stats @username` — Kisi ki bhi stats
`/leaderboard` — Top players list
"""

ADMIN_HELP = """
⚙️  **ADMIN COMMANDS**

`/broadcast <msg>` — Sabko message bhejo
`/users` — Total users & groups
`/maintenance on/off` — Bot on/off
`/end_match` — Koi bhi match force end
`/reset_stats <user_id>` — Stats reset
`/db_stats` — Database info
"""

def help_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧍 Solo Match", callback_data="help_solo"),
            InlineKeyboardButton("👥 Team Match", callback_data="help_team"),
        ],[
            InlineKeyboardButton("🏆 Tournament", callback_data="help_tournament"),
            InlineKeyboardButton("📊 Stats & LB", callback_data="help_stats"),
        ],[
            InlineKeyboardButton("⚙️ Admin Commands", callback_data="help_admin"),
        ],[
            InlineKeyboardButton("🏏 PlayZone", url=Config.PLAYZONE_LINK),
            InlineKeyboardButton("🆘 Support", url=Config.SUPPORT_LINK),
        ]
    ])

def back_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("◀️ Back", callback_data="help_main")
    ]])

@Client.on_message(filters.command("ping"))
async def ping_cmd(client: Client, message: Message):
    logger.info("PING from user=%s chat=%s", message.from_user.id, message.chat.id)
    try:
        await message.reply("🏏  **Bot is LIVE!** Pong! ✅")
        logger.info("PING reply sent OK")
    except Exception as e:
        logger.error("PING reply failed: %s", e, exc_info=True)

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    user = message.from_user
    logger.info("START (private) from user=%s", user.id)

    try:
        await add_user(user.id, user.username or "", user.full_name)
    except Exception as e:
        logger.error("add_user failed: %s", e)

    if state.maintenance_mode and user.id != Config.ADMIN_ID:
        return await message.reply(
            "🔧  **Maintenance Mode**\n\n"
            "Bot abhi maintenance par hai. Thodi der baad aana! 🙏"
        )

    try:
        me = await client.get_me()
        bot_username = me.username
    except Exception as e:
        logger.error("get_me() failed: %s", e)
        bot_username = "CricketManiaBot"

    try:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏏 PlayZone", url=Config.PLAYZONE_LINK),
            InlineKeyboardButton("🆘 Support", url=Config.SUPPORT_LINK),
        ],[
            InlineKeyboardButton("➕ Add me to your Group!", url=f"https://t.me/{bot_username}?startgroup=true"),
        ]])
        await message.reply(START_TEXT, reply_markup=kb)
        logger.info("START reply sent OK to user=%s", user.id)
    except Exception as e:
        logger.error("START reply failed: %s", e, exc_info=True)

@Client.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    logger.info("HELP from user=%s chat=%s", message.from_user.id, message.chat.id)
    try:
        await message.reply(HELP_TEXT, reply_markup=help_keyboard())
    except Exception as e:
        logger.error("HELP reply failed: %s", e, exc_info=True)

@Client.on_callback_query(filters.regex("^help_"))
async def help_callback(client: Client, cb: CallbackQuery):
    data = cb.data
    try:
        if data == "help_main":
            await cb.message.edit_text(HELP_TEXT, reply_markup=help_keyboard())
        elif data == "help_solo":
            await cb.message.edit_text(SOLO_HELP, reply_markup=back_keyboard())
        elif data == "help_team":
            await cb.message.edit_text(TEAM_HELP, reply_markup=back_keyboard())
        elif data == "help_tournament":
            await cb.message.edit_text(TOURNAMENT_HELP, reply_markup=back_keyboard())
        elif data == "help_stats":
            await cb.message.edit_text(STATS_HELP, reply_markup=back_keyboard())
        elif data == "help_admin":
            if cb.from_user.id != Config.ADMIN_ID:
                return await cb.answer("🔒 Sirf bot owner dekh sakta hai!", show_alert=True)
            await cb.message.edit_text(ADMIN_HELP, reply_markup=back_keyboard())
        await cb.answer()
    except Exception as e:
        logger.error("help_callback error: %s", e, exc_info=True)
