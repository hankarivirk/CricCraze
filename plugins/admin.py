import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database.users import get_all_users, get_user_count, get_all_groups, get_group_count
from database.stats import reset_stats, get_stats
from database import matches_col
import utils.state as state

def is_admin(_, __, message: Message):
    return message.from_user and message.from_user.id == Config.ADMIN_ID

admin_filter = filters.create(is_admin)

@Client.on_message(filters.command("broadcast") & admin_filter)
async def broadcast_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("⚠️  Usage: `/broadcast <message>`")

    text = message.text.split(None, 1)[1]
    users = await get_all_users()

    sent, failed = 0, 0
    status = await message.reply(f"📢  Broadcasting to **{len(users)}** users...")

    for u in users:
        try:
            await client.send_message(u["_id"], f"📢  **Cosmic Cricket Announcement**\n\n{text}")
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await status.edit_text(
        f"✅  **Broadcast Complete!**\n\n"
        f"┣  Sent: **{sent}**\n"
        f"┗  Failed: **{failed}**"
    )

@Client.on_message(filters.command("users") & admin_filter)
async def users_cmd(client: Client, message: Message):
    user_count  = await get_user_count()
    group_count = await get_group_count()
    await message.reply(
        f"📊  **Cosmic Cricket — Bot Statistics**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤  Total Users:  **{user_count}**\n"
        f"👥  Total Groups: **{group_count}**\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

@Client.on_message(filters.command("maintenance") & admin_filter)
async def maintenance_cmd(client: Client, message: Message):
    if len(message.command) < 2 or message.command[1].lower() not in ("on", "off"):
        return await message.reply("⚠️  Usage: `/maintenance on` or `/maintenance off`")

    state.maintenance_mode = message.command[1].lower() == "on"
    status = "🔴 ON" if state.maintenance_mode else "🟢 OFF"
    await message.reply(f"🔧  **Maintenance Mode:** {status}")

@Client.on_message(filters.command("reset_stats") & admin_filter)
async def reset_stats_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("⚠️  Usage: `/reset_stats <user_id>`")
    try:
        uid = int(message.command[1])
    except ValueError:
        return await message.reply("⚠️  Invalid user ID!")

    await reset_stats(uid)
    await message.reply(f"✅  Stats reset for user `{uid}`")

@Client.on_message(filters.command("db_stats") & admin_filter)
async def db_stats_cmd(client: Client, message: Message):
    user_count  = await get_user_count()
    group_count = await get_group_count()
    match_count = await matches_col.count_documents({})

    await message.reply(
        f"🗄️  **Cosmic Cricket — Database Info**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤  Users:   **{user_count}**\n"
        f"👥  Groups:  **{group_count}**\n"
        f"🏏  Matches Logged: **{match_count}**\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

@Client.on_message(filters.command("end_match") & filters.group)
async def end_match_admin(client: Client, message: Message):
    """Allow group admins or bot owner to force-end any running match."""
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    is_group_admin = member.status.value in ("administrator", "creator")

    if not (is_group_admin or message.from_user.id == Config.ADMIN_ID):
        return await message.reply("🔒  Only group admins or bot owner can end a match!")

    chat_id = message.chat.id
    ended = False

    if chat_id in state.solo_matches:
        state.solo_matches.pop(chat_id, None)
        ended = True
    if chat_id in state.team_matches:
        state.team_matches.pop(chat_id, None)
        ended = True
    if chat_id in state.tournaments:
        state.tournaments.pop(chat_id, None)
        ended = True

    if ended:
        await message.reply("🛑  **Match Ended!** All active games in this group have been stopped.")
    else:
        await message.reply("ℹ️  No active match running in this group.")
