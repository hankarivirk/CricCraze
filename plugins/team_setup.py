import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from utils.state import team_matches, TeamMatch, TeamPlayer, GamePhase
from utils.ui import toss_msg
from utils.gifs import send_match_start_gif

# ── Mode selection → Team ─────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^mode_team_"))
async def choose_team_mode(client: Client, cb: CallbackQuery):
    host_id = int(cb.data.split("_")[-1])
    if cb.from_user.id != host_id:
        return await cb.answer("🔒 Sirf match starter choose kar sakta hai!", show_alert=True)

    chat_id = cb.message.chat.id
    match = TeamMatch(chat_id=chat_id, host_id=host_id, phase=GamePhase.WAITING)
    team_matches[chat_id] = match

    await cb.message.edit_text(
        f"👥  **TEAM MATCH STARTED!**\n\n"
        f"👑  **Host:** {cb.from_user.full_name}\n\n"
        f"➡️  Host, type `/create_teams` to open team joining!\n"
        f"💡  *Tip: Host can also join a team and play!*"
    )
    await cb.answer()

@Client.on_message(filters.command("host") & filters.group)
async def host_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active team match!")
    host = await client.get_users(match.host_id)
    await message.reply(f"👑  **Current Host:** {host.full_name}")

# ── Team Joining ──────────────────────────────────────────────────────────────

@Client.on_message(filters.command("create_teams") & filters.group)
async def create_teams_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active team match! Use /start first.")
    if message.from_user.id != match.host_id:
        return await message.reply("🔒  Only the Host can open team joining!")

    match.team_a.clear()
    match.team_b.clear()
    match.phase = GamePhase.JOINING

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔴 Join Team A", callback_data=f"joinA_{message.chat.id}"),
        InlineKeyboardButton("🔵 Join Team B", callback_data=f"joinB_{message.chat.id}"),
    ]])
    msg = await message.reply(
        "⚔️  **TEAM JOINING OPEN!**\n\n"
        "🔴  **Team A** — 0 players\n"
        "🔵  **Team B** — 0 players\n\n"
        "Tap below to pick your side! 👇\n"
        "💡  *Host can join too!*",
        reply_markup=kb
    )
    match.join_a_msg_id = msg.id

async def update_join_message(client: Client, chat_id: int):
    match = team_matches.get(chat_id)
    if not match:
        return
    a_names = "\n".join(f"  • {p.full_name}" for p in match.team_a.values()) or "  —"
    b_names = "\n".join(f"  • {p.full_name}" for p in match.team_b.values()) or "  —"
    text = (
        "⚔️  **TEAM JOINING OPEN!**\n\n"
        f"🔴  **Team A** — {len(match.team_a)} players\n{a_names}\n\n"
        f"🔵  **Team B** — {len(match.team_b)} players\n{b_names}\n\n"
        "Tap below to pick your side! 👇"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔴 Join Team A", callback_data=f"joinA_{chat_id}"),
        InlineKeyboardButton("🔵 Join Team B", callback_data=f"joinB_{chat_id}"),
    ]])
    try:
        await client.edit_message_text(chat_id, match.join_a_msg_id, text, reply_markup=kb)
    except Exception:
        pass

@Client.on_callback_query(filters.regex("^joinA_"))
async def join_team_a(client: Client, cb: CallbackQuery):
    await _join_team(client, cb, "A")

@Client.on_callback_query(filters.regex("^joinB_"))
async def join_team_b(client: Client, cb: CallbackQuery):
    await _join_team(client, cb, "B")

async def _join_team(client, cb: CallbackQuery, team: str):
    chat_id = int(cb.data.split("_")[1])
    match = team_matches.get(chat_id)
    if not match or match.phase != GamePhase.JOINING:
        return await cb.answer("⚠️  Joining not open right now!", show_alert=True)

    user = cb.from_user
    if user.id in match.team_a or user.id in match.team_b:
        return await cb.answer("✅  Tu already ek team mein hai!", show_alert=True)

    target = match.team_a if team == "A" else match.team_b
    target[user.id] = TeamPlayer(user_id=user.id, full_name=user.full_name)

    await update_join_message(client, chat_id)
    await cb.answer(f"✅  Joined Team {team}!")

@Client.on_message(filters.command(["join_A", "join_a"]) & filters.group)
async def join_a_cmd(client: Client, message: Message):
    await _join_team_text(client, message, "A")

@Client.on_message(filters.command(["join_B", "join_b"]) & filters.group)
async def join_b_cmd(client: Client, message: Message):
    await _join_team_text(client, message, "B")

async def _join_team_text(client, message: Message, team: str):
    chat_id = message.chat.id
    match = team_matches.get(chat_id)
    if not match or match.phase != GamePhase.JOINING:
        return await message.reply("⚠️  Joining not open right now!")
    user = message.from_user
    if user.id in match.team_a or user.id in match.team_b:
        return await message.reply("✅  Tu already ek team mein hai!")
    target = match.team_a if team == "A" else match.team_b
    target[user.id] = TeamPlayer(user_id=user.id, full_name=user.full_name)
    await update_join_message(client, chat_id)
    await message.reply(f"✅  **{user.full_name}** joined Team {team}!")

@Client.on_message(filters.command("recreate_teams") & filters.group)
async def recreate_teams_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match or message.from_user.id != match.host_id:
        return await message.reply("🔒  Only the Host can do this!")
    await create_teams_cmd(client, message)

@Client.on_message(filters.command(["add_A", "add_a"]) & filters.group)
async def add_a_cmd(client: Client, message: Message):
    await _force_add(client, message, "A")

@Client.on_message(filters.command(["add_B", "add_b"]) & filters.group)
async def add_b_cmd(client: Client, message: Message):
    await _force_add(client, message, "B")

async def _force_add(client, message: Message, team: str):
    match = team_matches.get(message.chat.id)
    if not match or message.from_user.id != match.host_id:
        return await message.reply("🔒  Only the Host can force-add!")
    if not message.reply_to_message:
        return await message.reply("⚠️  Reply to a user's message to add them!")
    user = message.reply_to_message.from_user
    target = match.team_a if team == "A" else match.team_b
    target[user.id] = TeamPlayer(user_id=user.id, full_name=user.full_name)
    await message.reply(f"✅  **{user.full_name}** added to Team {team}!")

@Client.on_message(filters.command("remove") & filters.group)
async def remove_player_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match or message.from_user.id != match.host_id:
        return await message.reply("🔒  Only the Host can remove players!")
    if not message.reply_to_message:
        return await message.reply("⚠️  Reply to a user's message to remove them!")
    uid = message.reply_to_message.from_user.id
    removed = match.team_a.pop(uid, None) or match.team_b.pop(uid, None)
    if removed:
        await message.reply(f"🗑️  **{removed.full_name}** removed from the match!")
    else:
        await message.reply("⚠️  Player not found in any team!")

@Client.on_message(filters.command("members_list") & filters.group)
async def members_list_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active team match!")
    a_names = "\n".join(f"  • {p.full_name}" for p in match.team_a.values()) or "  —"
    b_names = "\n".join(f"  • {p.full_name}" for p in match.team_b.values()) or "  —"
    await message.reply(
        f"👥  **TEAM MEMBERS**\n\n"
        f"🔴  **Team A** ({len(match.team_a)})\n{a_names}\n\n"
        f"🔵  **Team B** ({len(match.team_b)})\n{b_names}"
    )

# ── Captains ──────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("choose_caps") & filters.group)
async def choose_caps_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match or message.from_user.id != match.host_id:
        return await message.reply("🔒  Only the Host can choose captains!")
    if len(match.team_a) < 1 or len(match.team_b) < 1:
        return await message.reply("⚠️  Both teams need at least 1 player!")

    kb_a = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔴 {p.full_name}", callback_data=f"capA_{uid}_{message.chat.id}")]
        for uid, p in match.team_a.items()
    ])
    kb_b = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔵 {p.full_name}", callback_data=f"capB_{uid}_{message.chat.id}")]
        for uid, p in match.team_b.items()
    ])
    await message.reply("🔴  **Team A — Choose your Captain:**", reply_markup=kb_a)
    await message.reply("🔵  **Team B — Choose your Captain:**", reply_markup=kb_b)

@Client.on_callback_query(filters.regex("^capA_"))
async def set_cap_a(client: Client, cb: CallbackQuery):
    _, uid, chat_id = cb.data.split("_")
    uid, chat_id = int(uid), int(chat_id)
    if cb.from_user.id != uid:
        return await cb.answer("🔒  Only that player can confirm as captain!", show_alert=True)
    match = team_matches.get(chat_id)
    match.cap_a = uid
    await cb.message.edit_text(f"🔴  **Team A Captain:** {match.team_a[uid].full_name} 👑")
    await cb.answer("✅  You're the Captain!")
    await check_both_captains(client, chat_id)

@Client.on_callback_query(filters.regex("^capB_"))
async def set_cap_b(client: Client, cb: CallbackQuery):
    _, uid, chat_id = cb.data.split("_")
    uid, chat_id = int(uid), int(chat_id)
    if cb.from_user.id != uid:
        return await cb.answer("🔒  Only that player can confirm as captain!", show_alert=True)
    match = team_matches.get(chat_id)
    match.cap_b = uid
    await cb.message.edit_text(f"🔵  **Team B Captain:** {match.team_b[uid].full_name} 👑")
    await cb.answer("✅  You're the Captain!")
    await check_both_captains(client, chat_id)

async def check_both_captains(client: Client, chat_id: int):
    match = team_matches.get(chat_id)
    if match.cap_a and match.cap_b:
        await do_toss(client, chat_id)

# ── Toss ──────────────────────────────────────────────────────────────────────

async def do_toss(client: Client, chat_id: int):
    match = team_matches.get(chat_id)
    winner_team = random.choice(["A", "B"])
    match.toss_winner = winner_team
    winner_cap_id = match.cap_a if winner_team == "A" else match.cap_b
    winner_name = (match.team_a if winner_team == "A" else match.team_b)[winner_cap_id].full_name

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏏 Bat First", callback_data=f"toss_bat_{chat_id}"),
        InlineKeyboardButton("🎯 Bowl First", callback_data=f"toss_bowl_{chat_id}"),
    ]])
    await client.send_message(
        chat_id,
        f"🪙  **TOSS TIME!**\n\n🏆  **{winner_name}** (Team {winner_team}) wins the toss!\n\nChoose 👇",
        reply_markup=kb
    )

@Client.on_callback_query(filters.regex("^toss_"))
async def toss_choice(client: Client, cb: CallbackQuery):
    _, choice, chat_id = cb.data.split("_")
    chat_id = int(chat_id)
    match = team_matches.get(chat_id)
    winner_cap_id = match.cap_a if match.toss_winner == "A" else match.cap_b

    if cb.from_user.id != winner_cap_id:
        return await cb.answer("🔒  Only the toss-winning captain can decide!", show_alert=True)

    if choice == "bat":
        match.batting_team = match.toss_winner
        match.bowling_team = "B" if match.toss_winner == "A" else "A"
    else:
        match.bowling_team = match.toss_winner
        match.batting_team = "B" if match.toss_winner == "A" else "A"

    await cb.message.edit_text(toss_msg(
        (match.team_a if match.toss_winner == "A" else match.team_b)[winner_cap_id].full_name,
        "Bat" if choice == "bat" else "Bowl"
    ))
    await cb.answer()

    bat_cap_id = match.cap_a if match.batting_team == "A" else match.cap_b
    bat_cap_name = (match.team_a if match.batting_team == "A" else match.team_b)[bat_cap_id].full_name
    await client.send_message(
        chat_id,
        f"📏  **{bat_cap_name}**, set the number of overs!\nUse `/set_overs <number>`"
    )

@Client.on_message(filters.command("set_overs") & filters.group)
async def set_overs_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active match!")
    bat_cap_id = match.cap_a if match.batting_team == "A" else match.cap_b
    if message.from_user.id != bat_cap_id:
        return await message.reply("🔒  Only the batting captain can set overs!")
    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply("⚠️  Usage: `/set_overs <number>`")

    match.overs = int(message.command[1])
    match.phase = GamePhase.BOWLING
    await send_match_start_gif(client, message.chat.id)
    await message.reply(f"🏏  **{match.overs} overs match!** Let the game begin! 🔥")

    bowl_cap_id = match.cap_a if match.bowling_team == "A" else match.cap_b
    bowl_cap_name = (match.team_a if match.bowling_team == "A" else match.team_b)[bowl_cap_id].full_name
    await message.reply(f"🎯  **{bowl_cap_name}**, choose your bowler!\nUse `/bowling` (reply to player)")
