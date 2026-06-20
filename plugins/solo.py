import asyncio
import random
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from utils.state import solo_matches, SoloMatch, PlayerScore, GamePhase
import utils.state as state
from utils.ui import (
    solo_scorecard, solo_result_card, bat_prompt, bowl_prompt,
    dot_ball_msg, century_msg
)
from utils.gifs import (
    send_run_gif, send_wicket_gif, send_bowling_prompt_gif,
    send_match_start_gif, send_trophy_gif
)
from database.stats import update_batting_stats, update_bowling_stats, update_motm
from database.users import add_user, add_group

# ── /start callback for choosing Solo ────────────────────────────────────────

@Client.on_message(filters.command("start") & filters.group)
async def group_start_menu(client: Client, message: Message):
    chat_id = message.chat.id
    user = message.from_user

    await add_user(user.id, user.username or "", user.full_name)
    await add_group(chat_id, message.chat.title)

    if state.maintenance_mode and user.id != Config.ADMIN_ID:
        return await message.reply(
            "🔧  **Maintenance Mode**\n\n"
            "Bot abhi maintenance par hai. Thodi der baad aana! 🙏"
        )

    if chat_id in solo_matches or chat_id in state.team_matches:
        return await message.reply("⚠️  Ek match already chal raha hai is group mein!")

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🧍 Solo Match", callback_data=f"mode_solo_{message.from_user.id}"),
        InlineKeyboardButton("👥 Team Match", callback_data=f"mode_team_{message.from_user.id}"),
    ]])
    await message.reply(
        "🏏  **Choose Your Battle!**\n\n"
        "🧍  **Solo Match** — Every man for himself.\n"
        "👥  **Team Match** — Two sides, one champion.",
        reply_markup=kb
    )


@Client.on_callback_query(filters.regex("^mode_solo_"))
async def choose_solo_mode(client: Client, cb: CallbackQuery):
    host_id = int(cb.data.split("_")[-1])
    if cb.from_user.id != host_id:
        return await cb.answer("🔒 Sirf match starter choose kar sakta hai!", show_alert=True)

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("3 Balls/Over", callback_data=f"soloovers_3_{host_id}"),
        InlineKeyboardButton("6 Balls/Over", callback_data=f"soloovers_6_{host_id}"),
    ]])
    await cb.message.edit_text("🧍  **Solo Match**\n\nChoose balls per over 👇", reply_markup=kb)
    await cb.answer()

@Client.on_callback_query(filters.regex("^soloovers_"))
async def solo_set_overs(client: Client, cb: CallbackQuery):
    _, overs, host_id = cb.data.split("_")
    overs, host_id = int(overs), int(host_id)
    if cb.from_user.id != host_id:
        return await cb.answer("🔒 Sirf match starter choose kar sakta hai!", show_alert=True)

    chat_id = cb.message.chat.id
    match = SoloMatch(chat_id=chat_id, host_id=host_id, overs=overs, phase=GamePhase.JOINING)
    solo_matches[chat_id] = match

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🙋 Join Match", callback_data=f"joinsolo_{chat_id}")]])
    msg = await cb.message.edit_text(
        f"🧍  **SOLO MATCH STARTING!**\n\n"
        f"🎯  {overs} Ball{'s' if overs > 1 else ''}/Over\n"
        f"👥  Min {Config.MIN_PLAYERS_SOLO} — Max {Config.MAX_PLAYERS_SOLO} players\n\n"
        f"⏱️  Joining closes in **2 minutes**\n"
        f"Type `/join_solo` or tap below to join!",
        reply_markup=kb
    )
    match.join_msg_id = msg.id
    await cb.answer()

    asyncio.create_task(auto_start_timer(client, chat_id))

async def auto_start_timer(client: Client, chat_id: int):
    await asyncio.sleep(Config.JOIN_TIMEOUT)
    match = solo_matches.get(chat_id)
    if match and match.phase == GamePhase.JOINING:
        if len(match.players) >= Config.MIN_PLAYERS_SOLO:
            await begin_solo_match(client, chat_id)
        else:
            await client.send_message(
                chat_id,
                f"⚠️  **Match Cancelled!**\n\nNot enough players joined (need min {Config.MIN_PLAYERS_SOLO})."
            )
            solo_matches.pop(chat_id, None)

@Client.on_callback_query(filters.regex("^joinsolo_"))
async def join_solo_callback(client: Client, cb: CallbackQuery):
    chat_id = int(cb.data.split("_")[1])
    await _join_solo(client, chat_id, cb.from_user, cb)

@Client.on_message(filters.command("join_solo") & filters.group)
async def join_solo_cmd(client: Client, message: Message):
    await _join_solo(client, message.chat.id, message.from_user, message)

async def _join_solo(client, chat_id, user, ctx):
    match = solo_matches.get(chat_id)
    is_cb = isinstance(ctx, CallbackQuery)

    if not match or match.phase != GamePhase.JOINING:
        msg = "⚠️  No joining window open right now!"
        return await ctx.answer(msg, show_alert=True) if is_cb else await ctx.reply(msg)

    if user.id in match.players:
        msg = "✅ Tu already joined hai!"
        return await ctx.answer(msg, show_alert=True) if is_cb else await ctx.reply(msg)

    if len(match.players) >= Config.MAX_PLAYERS_SOLO:
        msg = "⚠️  Match full hai!"
        return await ctx.answer(msg, show_alert=True) if is_cb else await ctx.reply(msg)

    match.players[user.id] = PlayerScore(user_id=user.id, full_name=user.full_name)
    match.order.append(user.id)

    names = "\n".join(f"  {i+1}. {p.full_name}" for i, p in enumerate(match.players.values()))
    text = (
        f"🧍  **SOLO MATCH — JOINING**\n\n"
        f"👥  **Players ({len(match.players)}):**\n{names}\n\n"
        f"⏱️  Type `/join_solo` to join!"
    )
    try:
        await client.edit_message_text(
            chat_id, match.join_msg_id, text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🙋 Join Match", callback_data=f"joinsolo_{chat_id}")]])
        )
    except Exception:
        pass

    if is_cb:
        await ctx.answer("✅ Joined!")
    else:
        await ctx.reply(f"✅  **{user.full_name}** joined the match!")

@Client.on_message(filters.command("leave_solo") & filters.group)
async def leave_solo_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    match = solo_matches.get(chat_id)
    if not match or match.phase != GamePhase.JOINING:
        return await message.reply("⚠️  No joining window open!")
    uid = message.from_user.id
    if uid not in match.players:
        return await message.reply("⚠️  Tu joined nahi hai!")
    del match.players[uid]
    match.order.remove(uid)
    await message.reply(f"👋  **{message.from_user.full_name}** left the match.")

@Client.on_message(filters.command("solo_list") & filters.group)
async def solo_list_cmd(client: Client, message: Message):
    match = solo_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active solo match!")
    names = "\n".join(f"  {i+1}. {p.full_name}" for i, p in enumerate(match.players.values()))
    await message.reply(f"👥  **Joined Players ({len(match.players)}):**\n{names or 'None yet'}")

@Client.on_message(filters.command("start_solo") & filters.group)
async def force_start_solo(client: Client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await message.reply("🔒  Only group admins can force-start!")
    match = solo_matches.get(message.chat.id)
    if not match or match.phase != GamePhase.JOINING:
        return await message.reply("⚠️  No joining window open!")
    if len(match.players) < Config.MIN_PLAYERS_SOLO:
        return await message.reply(f"⚠️  Need min {Config.MIN_PLAYERS_SOLO} players!")
    await begin_solo_match(client, message.chat.id)

@Client.on_message(filters.command("extend_solo") & filters.group)
async def extend_solo_cmd(client: Client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await message.reply("🔒  Only group admins can extend!")
    match = solo_matches.get(message.chat.id)
    if not match or match.phase != GamePhase.JOINING:
        return await message.reply("⚠️  No joining window open!")
    await message.reply("⏱️  **Joining time extended by 30 seconds!**")
    asyncio.create_task(extend_timer(client, message.chat.id))

async def extend_timer(client, chat_id):
    await asyncio.sleep(30)
    match = solo_matches.get(chat_id)
    if match and match.phase == GamePhase.JOINING:
        if len(match.players) >= Config.MIN_PLAYERS_SOLO:
            await begin_solo_match(client, chat_id)
        else:
            await client.send_message(chat_id, "⚠️  **Match Cancelled!** Not enough players.")
            solo_matches.pop(chat_id, None)

@Client.on_message(filters.command("resume_solo") & filters.group)
async def resume_solo_cmd(client: Client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await message.reply("🔒  Only group admins can resume!")
    match = solo_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No interrupted match found!")
    await message.reply("▶️  **Resuming match...**")
    await next_ball(client, message.chat.id)

@Client.on_message(filters.command("end_solo") & filters.group)
async def end_solo_cmd(client: Client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await message.reply("🔒  Only group admins can end the match!")
    chat_id = message.chat.id
    if chat_id in solo_matches:
        del solo_matches[chat_id]
        await message.reply("🛑  **Solo match ended!**")
    else:
        await message.reply("⚠️  No active solo match!")

@Client.on_message(filters.command("solo_score") & filters.group)
async def solo_score_cmd(client: Client, message: Message):
    match = solo_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active solo match!")
    players_data = [vars(p) for p in match.players.values()]
    await message.reply(solo_scorecard(players_data, match.overs))

# ── Core Match Flow ───────────────────────────────────────────────────────────

async def begin_solo_match(client: Client, chat_id: int):
    match = solo_matches[chat_id]
    match.phase = GamePhase.BOWLING
    random.shuffle(match.order)

    await send_match_start_gif(client, chat_id)
    await client.send_message(
        chat_id,
        f"🏏  **MATCH STARTED!**\n\n"
        f"👥  {len(match.players)} players ready to battle!\n"
        f"🎯  {match.overs} ball{'s' if match.overs > 1 else ''} per over\n\n"
        f"Let the game begin! 🔥"
    )
    await next_ball(client, chat_id)

async def next_ball(client: Client, chat_id: int):
    match = solo_matches.get(chat_id)
    if not match:
        return

    remaining = [uid for uid in match.order if not match.players[uid].is_out]
    if not remaining:
        return await finish_solo_match(client, chat_id)

    batter_id = remaining[0]
    batter = match.players[batter_id]

    bowler_candidates = [uid for uid in match.order if uid != batter_id]
    if not bowler_candidates:
        bowler_id = batter_id
    else:
        bowler_id = bowler_candidates[match.current_bowler_idx % len(bowler_candidates)]

    bowler = match.players[bowler_id]
    match.bowl_number += 1

    match.phase = GamePhase.BOWLING
    await send_bowling_prompt_gif(client, chat_id)
    await client.send_message(chat_id, bowl_prompt(bowler.full_name, match.bowl_number, match.overs))

    asyncio.create_task(wait_for_bowl(client, chat_id, bowler_id, batter_id))

async def wait_for_bowl(client: Client, chat_id: int, bowler_id: int, batter_id: int):
    match = solo_matches.get(chat_id)
    if not match:
        return

    try:
        bowl_msg: Message = await client.listen(
            chat_id=bowler_id,
            filters=filters.text & filters.private,
            timeout=Config.BOWL_TIMEOUT
        )
        try:
            number = int(bowl_msg.text.strip())
            if not (1 <= number <= 6):
                raise ValueError
        except ValueError:
            await bowl_msg.reply("⚠️  Send a number between 1-6!")
            return await wait_for_bowl(client, chat_id, bowler_id, batter_id)

        match.bowler_number = number
        await bowl_msg.reply("✅  Got it! Ball is bowled... 🎯")

    except asyncio.TimeoutError:
        bowler = match.players.get(bowler_id)
        if bowler:
            bowler.consecutive_penalties += 1
            bowler.runs_given -= 6
        await client.send_message(
            chat_id,
            f"⏱️  **Time's up!** Bowler didn't bowl in time — dot ball + penalty!"
        )
        match.bowler_number = None

    await prompt_batter(client, chat_id, batter_id, bowler_id)

async def prompt_batter(client: Client, chat_id: int, batter_id: int, bowler_id: int):
    match = solo_matches.get(chat_id)
    if not match:
        return
    batter = match.players[batter_id]
    match.phase = GamePhase.BATTING

    await client.send_message(chat_id, bat_prompt(batter.full_name, match.bowl_number))
    asyncio.create_task(wait_for_bat(client, chat_id, batter_id, bowler_id))

async def wait_for_bat(client: Client, chat_id: int, batter_id: int, bowler_id: int):
    match = solo_matches.get(chat_id)
    if not match:
        return

    try:
        bat_msg: Message = await client.listen(
            chat_id=chat_id,
            filters=filters.text & filters.user(batter_id),
            timeout=Config.BAT_TIMEOUT
        )
        try:
            number = int(bat_msg.text.strip())
            if not (1 <= number <= 6):
                raise ValueError
        except ValueError:
            return await wait_for_bat(client, chat_id, batter_id, bowler_id)

        await resolve_ball(client, chat_id, batter_id, bowler_id, number, timed_out=False)

    except asyncio.TimeoutError:
        await resolve_ball(client, chat_id, batter_id, bowler_id, None, timed_out=True)

async def resolve_ball(client: Client, chat_id: int, batter_id: int, bowler_id: int,
                       bat_number, timed_out: bool):
    match = solo_matches.get(chat_id)
    if not match:
        return

    batter = match.players[batter_id]
    bowler = match.players[bowler_id]
    bowl_number = match.bowler_number

    bowler.balls_bowled += 1

    if timed_out:
        batter.is_out = True
        batter.ball_log.append("W")
        bowler.wickets += 1
        await client.send_message(chat_id, "⏱️  **Time's up!** Auto OUT!")
        await send_wicket_gif(client, chat_id, batter.full_name)
    elif bowl_number is not None and bat_number == bowl_number:
        batter.is_out = True
        batter.ball_log.append("W")
        bowler.wickets += 1
        await send_wicket_gif(client, chat_id, batter.full_name)
    else:
        runs = bat_number if bat_number is not None else 0
        batter.runs += runs
        batter.balls += 1
        batter.ball_log.append(runs)
        bowler.runs_given += runs
        if runs == 4:
            batter.fours += 1
        elif runs == 6:
            batter.sixes += 1

        if runs == 0:
            await client.send_message(chat_id, dot_ball_msg(batter.full_name))
        else:
            await send_run_gif(client, chat_id, runs, batter.full_name)

        if batter.runs in (50, 100):
            await client.send_message(chat_id, century_msg(batter.full_name, batter.runs))

    match.bowler_number = None

    if not batter.is_out and batter.balls >= match.overs:
        batter.is_out = True

    match.current_bowler_idx += 1

    remaining = [uid for uid in match.order if not match.players[uid].is_out]
    if not remaining:
        await finish_solo_match(client, chat_id)
    else:
        await next_ball(client, chat_id)

async def finish_solo_match(client: Client, chat_id: int):
    match = solo_matches.get(chat_id)
    if not match:
        return
    match.phase = GamePhase.FINISHED

    players_data = [vars(p) for p in match.players.values()]
    if not players_data:
        solo_matches.pop(chat_id, None)
        return

    best_batter = max(match.players.values(), key=lambda p: p.runs)
    best_bowler = max(match.players.values(), key=lambda p: p.wickets)
    motm = max(match.players.values(), key=lambda p: p.runs + p.wickets * 15)

    text = solo_result_card(
        players_data, match.overs,
        best_batter.full_name, best_bowler.full_name, motm.full_name
    )
    await client.send_message(chat_id, text)
    await send_trophy_gif(client, chat_id, f"⭐️  **Player of the Match:** {motm.full_name}")

    for p in match.players.values():
        try:
            await update_batting_stats(
                p.user_id, p.full_name, p.runs, p.balls, p.fours, p.sixes,
                p.is_out, won=(p.user_id == best_batter.user_id)
            )
            if p.balls_bowled > 0:
                hat_trick = p.wickets >= 3
                await update_bowling_stats(p.user_id, p.full_name, p.wickets, p.runs_given, p.balls_bowled, hat_trick)
        except Exception:
            pass

    try:
        await update_motm(motm.user_id, motm.full_name)
    except Exception:
        pass

    solo_matches.pop(chat_id, None)
