from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.stats import get_stats, get_leaderboard, init_stats
from database.users import add_user
from utils.ui import stats_card, leaderboard_card

@Client.on_message(filters.command("stats"))
async def stats_cmd(client: Client, message: Message):
    target_user = None
    target_id   = None

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        target_id   = target_user.id
    elif len(message.command) > 1:
        arg = message.command[1].replace("@", "")
        try:
            target_id = int(arg)
            target_user = await client.get_users(target_id)
        except ValueError:
            try:
                target_user = await client.get_users(arg)
                target_id = target_user.id
            except Exception:
                return await message.reply("⚠️  User not found!")
    else:
        target_user = message.from_user
        target_id   = target_user.id

    s = await get_stats(target_id)
    if not s:
        await init_stats(target_id, target_user.full_name)
        s = await get_stats(target_id)

    await message.reply(stats_card(target_user.full_name, s))

LEADERBOARD_OPTIONS = {
    "overall": ("runs", "Runs"),
    "runs":    ("runs", "Runs"),
    "wickets": ("wickets_taken", "Wickets"),
    "sr":      ("runs", "Runs"),       # computed separately if needed
    "centuries": ("centuries", "Centuries"),
    "hattricks": ("hat_tricks", "Hat-tricks"),
    "motm":    ("motm", "MOTM"),
}

def leaderboard_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏆 Overall", callback_data="lb_overall"),
            InlineKeyboardButton("🏃 Runs", callback_data="lb_runs"),
        ],[
            InlineKeyboardButton("🎯 Wickets", callback_data="lb_wickets"),
            InlineKeyboardButton("💯 Centuries", callback_data="lb_centuries"),
        ],[
            InlineKeyboardButton("🎩 Hat-tricks", callback_data="lb_hattricks"),
            InlineKeyboardButton("⭐ MOTM", callback_data="lb_motm"),
        ]
    ])

@Client.on_message(filters.command("leaderboard"))
async def leaderboard_cmd(client: Client, message: Message):
    await message.reply(
        "🏆  **CRICKET MANIA — LEADERBOARD**\n\nChoose a category 👇",
        reply_markup=leaderboard_keyboard()
    )

@Client.on_callback_query(filters.regex("^lb_"))
async def leaderboard_callback(client: Client, cb: CallbackQuery):
    category = cb.data.split("_", 1)[1]
    key, label = LEADERBOARD_OPTIONS.get(category, ("runs", "Runs"))

    players = await get_leaderboard(sort_by=key, limit=10)
    title = f"Top Players — {label}"

    if not players:
        await cb.message.edit_text(
            "📊  No stats recorded yet. Play a match first! 🏏",
            reply_markup=leaderboard_keyboard()
        )
        return await cb.answer()

    text = leaderboard_card(title, players, key, label)
    await cb.message.edit_text(text, reply_markup=leaderboard_keyboard())
    await cb.answer()
