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
        f"👥  **COSMIC CRICKET — TEAM MATCH!**\n\n"
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
    # Check if already in the same team
    target_dict = match.team_a if team == "A" else match.team_b
    other_dict  = match.team_b if team == "A" else match.team_a

    if user.id in target_dict:
        return await cb.answer(f"✅  Tu already Team {team} mein hai!", show_alert=True)

    # If in other team, remove from there first
    if user.id in other_dict:
        del other_dict[user.id]

    target_dict[user.id] = TeamPlayer(user_id=user.id, full_name=user.full_name)
    await cb.answer(f"✅  Joined Team {team}!")
    await update_join_message(client, chat_id)

@Client.on_message(filters.command("join_A") & filters.group)
async def join_a_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match or match.phase != GamePhase.JOINING:
        return await message.reply("⚠️  Joining not open right now!")
    user = message.from_user
    if user.id in match.team_b:
        del match.team_b[user.id]
    match.team_a[user.id] = TeamPlayer(user_id=user.id, full_name=user.full_name)
    await message.reply(f"✅  **{user.full_name}** joined 🔴 Team A!")
    await update_join_message(client, message.chat.id)

@Client.on_message(filters.command("join_B") & filters.group)
async def join_b_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match or match.phase != GamePhase.JOINING:
        return await message.reply("⚠️  Joining not open right now!")
    user = message.from_user
    if user.id in match.team_a:
        del match.team_a[user.id]
    match.team_b[user.id] = TeamPlayer(user_id=user.id, full_name=user.full_name)
    await message.reply(f"✅  **{user.full_name}** joined 🔵 Team B!")
    await update_join_message(client, message.chat.id)

@Client.on_message(filters.command("add_A") & filters.group)
async def add_a_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match or message.from_user.id != match.host_id:
        return await message.reply("🔒  Only Host can force-add!")
    if not message.reply_to_message:
        return await message.reply("⚠️  Reply to the player you want to add!")
    user = message.reply_to_message.from_user
    if user.id in match.team_b:
        del match.team_b[user.id]
    match.team_a[user.id] = TeamPlayer(user_id=user.id, full_name=user.full_name)
    await message.reply(f"✅  **{user.full_name}** added to 🔴 Team A!")
    await update_join_message(client, message.chat.id)

@Client.on_message(filters.command("add_B") & filters.group)
async def add_b_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match or message.from_user.id != match.host_id:
        return await message.reply("🔒  Only Host can force-add!")
    if not message.reply_to_message:
        return await message.reply("⚠️  Reply to the player you want to add!")
    user = message.reply_to_message.from_user
    if user.id in match.team_a:
        del match.team_a[user.id]
    match.team_b[user.id] = TeamPlayer(user_id=user.id, full_name=user.full_name)
    await message.reply(f"✅  **{user.full_name}** added to 🔵 Team B!")
    await update_join_message(client, message.chat.id)

@Client.on_message(filters.command("remove") & filters.group)
async def remove_player_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match or message.from_user.id != match.host_id:
        return await message.reply("🔒  Only Host can remove players!")
    if not message.reply_to_message:
        return await message.reply("⚠️  Reply to the player you want to remove!")
    uid = message.reply_to_message.from_user.id
    name = message.reply_to_message.from_user.full_name
    removed = False
    if uid in match.team_a:
        del match.team_a[uid]
        removed = True
    if uid in match.team_b:
        del match.team_b[uid]
        removed = True
    if removed:
        await message.reply(f"❌  **{name}** removed from the match.")
        await update_join_message(client, message.chat.id)
    else:
        await message.reply("⚠️  That player isn't in any team!")

@Client.on_message(filters.command("members_list") & filters.group)
async def members_list_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active team match!")
    a_names = "\n".join(f"  • {p.full_name}" for p in match.team_a.values()) or "  —"
    b_names = "\n".join(f"  • {p.full_name}" for p in match.team_b.values()) or "  —"
    await message.reply(
        f"👥  **TEAM ROSTER**\n\n"
        f"🔴  **Team A** ({len(match.team_a)}):\n{a_names}\n\n"
        f"🔵  **Team B** ({len(match.team_b)}):\n{b_names}"
    )

@Client.on_message(filters.command("recreate_teams") & filters.group)
async def recreate_teams_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match or message.from_user.id != match.host_id:
        return await message.reply("🔒  Only Host can recreate teams!")
    match.team_a.clear()
    match.team_b.clear()
    match.phase = GamePhase.JOINING
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔴 Join Team A", callback_data=f"joinA_{message.chat.id}"),
        InlineKeyboardButton("🔵 Join Team B", callback_data=f"joinB_{message.chat.id}"),
    ]])
    msg = await message.reply(
        "🔄  **Teams reset! Joining reopened.**\n\n"
        "🔴  **Team A** — 0 players\n"
        "🔵  **Team B** — 0 players\n\n"
        "Tap below to join! 👇",
        reply_markup=kb
    )
    match.join_a_msg_id = msg.id

# ── Captain Selection & Toss ──────────────────────────────────────────────────

@Client.on_message(filters.command("choose_caps") & filters.group)
async def choose_caps_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match or message.from_user.id != match.host_id:
        return await message.reply("🔒  Only Host can select captains!")
    if len(match.team_a) == 0 or len(match.team_b) == 0:
        return await message.reply("⚠️  Both teams need at least 1 player!")

    # Auto-assign first player as captain if not set
    if not match.cap_a:
        match.cap_a = next(iter(match.team_a))
    if not match.cap_b:
        match.cap_b = next(iter(match.team_b))

    cap_a_name = match.team_a[match.cap_a].full_name
    cap_b_name = match.team_b[match.cap_b].full_name

    await message.reply(
        f"👑  **Captains Selected!**\n\n"
        f"🔴  Team A Captain: **{cap_a_name}**\n"
        f"🔵  Team B Captain: **{cap_b_name}**\n\n"
        f"💡  Use `/change_cap` (reply to player) to change.\n\n"
        f"Now doing the toss... 🪙"
    )
    await asyncio.sleep(1)
    await do_toss(client, message.chat.id)

async def do_toss(client: Client, chat_id: int):
    match = team_matches.get(chat_id)
    if not match:
        return

    toss_winner_side = random.choice(["A", "B"])
    match.toss_winner = toss_winner_side
    winner_name = match.team_a[match.cap_a].full_name if toss_winner_side == "A" else match.team_b[match.cap_b].full_name

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏏 Bat", callback_data=f"toss_bat_{chat_id}_{toss_winner_side}"),
        InlineKeyboardButton("🎯 Bowl", callback_data=f"toss_bowl_{chat_id}_{toss_winner_side}"),
    ]])
    await client.send_message(
        chat_id,
        f"🪙  **TOSS!**\n\n"
        f"🎲  The coin spins...\n\n"
        f"🏆  **{winner_name}** (Team {toss_winner_side}) wins the toss!\n\n"
        f"Choose to **Bat** or **Bowl** first 👇",
        reply_markup=kb
    )

@Client.on_callback_query(filters.regex("^toss_(bat|bowl)_"))
async def toss_choice_callback(client: Client, cb: CallbackQuery):
    parts = cb.data.split("_")
    choice = parts[1]          # "bat" or "bowl"
    chat_id = int(parts[2])
    toss_winner_side = parts[3]  # "A" or "B"

    match = team_matches.get(chat_id)
    if not match:
        return await cb.answer("Match no longer active!", show_alert=True)

    # Only the toss winner captain can choose
    winner_cap = match.cap_a if toss_winner_side == "A" else match.cap_b
    if cb.from_user.id != winner_cap:
        return await cb.answer("🔒 Only the toss winner can choose!", show_alert=True)

    if choice == "bat":
        match.batting_team = toss_winner_side
        match.bowling_team = "B" if toss_winner_side == "A" else "A"
    else:
        match.bowling_team = toss_winner_side
        match.batting_team = "B" if toss_winner_side == "A" else "A"

    bat_name  = match.team_a[match.cap_a].full_name if match.batting_team == "A" else match.team_b[match.cap_b].full_name
    bowl_name = match.team_a[match.cap_a].full_name if match.bowling_team == "A" else match.team_b[match.cap_b].full_name

    await cb.message.edit_text(
        f"✅  **Toss result locked!**\n\n"
        f"🏏  **Batting first:** Team {match.batting_team} ({bat_name})\n"
        f"🎯  **Bowling first:** Team {match.bowling_team} ({bowl_name})\n\n"
        f"🎯  Bowling captain, type `/bowling` (reply to your bowler)\n"
        f"📏  Then batting captain, type `/set_overs <number>`"
    )
    await cb.answer()

@Client.on_message(filters.command("set_overs") & filters.group)
async def set_overs_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active team match!")

    bat_cap = match.cap_a if match.batting_team == "A" else match.cap_b
    if message.from_user.id != bat_cap:
        return await message.reply("🔒  Only the batting captain can set overs!")

    if len(message.command) < 2:
        return await message.reply("⚠️  Usage: `/set_overs <number>`\nExample: `/set_overs 6`")

    try:
        overs = int(message.command[1])
        if overs < 1 or overs > 50:
            raise ValueError
    except ValueError:
        return await message.reply("⚠️  Please enter a valid number (1–50)!")

    match.overs = overs * 6  # store as total balls
    match.phase = GamePhase.BATTING

    await send_match_start_gif(client, message.chat.id)
    await message.reply(
        f"📏  **{overs} overs set!**\n\n"
        f"🏏  **{('🔴 Team A' if match.batting_team == 'A' else '🔵 Team B')}** bats first!\n\n"
        f"Batting captain: use `/batting` (reply to your opener)\n"
        f"Bowling captain: use `/bowling` (reply to your bowler)\n\n"
        f"⚠️  *Bowler must start the bot in DM first!*"
    )
