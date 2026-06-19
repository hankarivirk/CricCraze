import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from utils.state import team_matches, GamePhase
from utils.ui import team_scorecard, team_result_card, bat_prompt, bowl_prompt, dot_ball_msg, century_msg, innings_break_msg
from utils.gifs import send_run_gif, send_wicket_gif, send_bowling_prompt_gif, send_trophy_gif
from database.stats import update_batting_stats, update_bowling_stats, update_motm

def get_team_dict(match, side: str):
    return match.team_a if side == "A" else match.team_b

def get_cap_id(match, side: str):
    return match.cap_a if side == "A" else match.cap_b

# ── Bowler & Batter Selection (by Captain) ───────────────────────────────────

@Client.on_message(filters.command("bowling") & filters.group)
async def bowling_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active match!")
    bowl_cap_id = get_cap_id(match, match.bowling_team)
    if message.from_user.id != bowl_cap_id:
        return await message.reply("🔒  Only the bowling captain can choose the bowler!")
    if not message.reply_to_message:
        return await message.reply("⚠️  Reply to the player you want to bowl!")

    bowler_id = message.reply_to_message.from_user.id
    bowling_team_dict = get_team_dict(match, match.bowling_team)
    if bowler_id not in bowling_team_dict:
        return await message.reply("⚠️  That player isn't in the bowling team!")

    match.current_bowler = bowler_id
    await message.reply(f"🎯  **{bowling_team_dict[bowler_id].full_name}** will bowl this over!")

    # If batters not yet set, prompt captain
    batting_team_dict = get_team_dict(match, match.batting_team)
    if match.striker is None:
        bat_cap_id = get_cap_id(match, match.batting_team)
        await client.send_message(
            message.chat.id,
            f"🏏  **{batting_team_dict[bat_cap_id].full_name}**, choose your opening batter!\nUse `/batting` (reply to player)"
        )
    else:
        await start_over(client, message.chat.id)

@Client.on_message(filters.command("batting") & filters.group)
async def batting_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active match!")
    bat_cap_id = get_cap_id(match, match.batting_team)
    if message.from_user.id != bat_cap_id:
        return await message.reply("🔒  Only the batting captain can choose the batter!")
    if not message.reply_to_message:
        return await message.reply("⚠️  Reply to the player you want to bat!")

    batter_id = message.reply_to_message.from_user.id
    batting_team_dict = get_team_dict(match, match.batting_team)
    if batter_id not in batting_team_dict:
        return await message.reply("⚠️  That player isn't in the batting team!")
    if batting_team_dict[batter_id].is_out:
        return await message.reply("⚠️  That player is already out!")

    if match.striker is None:
        match.striker = batter_id
    elif match.non_striker is None and batter_id != match.striker:
        match.non_striker = batter_id
    else:
        match.striker = batter_id

    await message.reply(f"🏏  **{batting_team_dict[batter_id].full_name}** is on strike!")

    if match.current_bowler:
        await start_over(client, message.chat.id)

@Client.on_message(filters.command("score") & filters.group)
async def score_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active match!")
    await message.reply(team_scorecard(match))

@Client.on_message(filters.command("change_cap") & filters.group)
async def change_cap_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match or message.from_user.id != match.host_id:
        return await message.reply("🔒  Only the Host can transfer captaincy!")
    if not message.reply_to_message:
        return await message.reply("⚠️  Reply to the new captain's message!")
    new_cap = message.reply_to_message.from_user.id
    if new_cap in match.team_a:
        match.cap_a = new_cap
        await message.reply(f"👑  **{match.team_a[new_cap].full_name}** is now Team A Captain!")
    elif new_cap in match.team_b:
        match.cap_b = new_cap
        await message.reply(f"👑  **{match.team_b[new_cap].full_name}** is now Team B Captain!")
    else:
        await message.reply("⚠️  Player not found in any team!")

@Client.on_message(filters.command("change_host") & filters.group)
async def change_host_cmd(client: Client, message: Message):
    match = team_matches.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active match!")
    if not message.reply_to_message:
        return await message.reply("⚠️  Reply to the proposed new host!")
    await message.reply(
        f"🗳️  **Host change requested!**\n\n"
        f"Proposed new host: **{message.reply_to_message.from_user.full_name}**\n"
        f"Group admins, please confirm with `/end_match` + restart if approved."
    )

# Note: /end_match is handled centrally in admin.py (end_match_admin), which
# covers solo, team, and tournament matches and allows bot-owner override.

# ── Over / Ball Flow ──────────────────────────────────────────────────────────

async def start_over(client: Client, chat_id: int):
    match = team_matches.get(chat_id)
    if not match:
        return
    match.ball_count = 0
    bowling_team_dict = get_team_dict(match, match.bowling_team)
    bowler = bowling_team_dict[match.current_bowler]

    await send_bowling_prompt_gif(client, chat_id)
    await client.send_message(chat_id, bowl_prompt(bowler.full_name, 1, 6))
    asyncio.create_task(wait_for_team_bowl(client, chat_id))

async def wait_for_team_bowl(client: Client, chat_id: int):
    match = team_matches.get(chat_id)
    if not match:
        return
    bowler_id = match.current_bowler

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
            return await wait_for_team_bowl(client, chat_id)
        match.bowler_number = number
        await bowl_msg.reply("✅  Got it! Ball is bowled... 🎯")
    except asyncio.TimeoutError:
        bowling_team_dict = get_team_dict(match, match.bowling_team)
        bowler_name = bowling_team_dict[bowler_id].full_name
        await client.send_message(chat_id, f"⏱️  **Time's up!** {bowler_name} didn't bowl — dot ball!")
        match.bowler_number = None

    await prompt_team_batter(client, chat_id)

async def prompt_team_batter(client: Client, chat_id: int):
    match = team_matches.get(chat_id)
    if not match:
        return
    batting_team_dict = get_team_dict(match, match.batting_team)
    striker = batting_team_dict[match.striker]

    await client.send_message(chat_id, bat_prompt(striker.full_name, match.ball_count + 1))
    asyncio.create_task(wait_for_team_bat(client, chat_id))

async def wait_for_team_bat(client: Client, chat_id: int):
    match = team_matches.get(chat_id)
    if not match:
        return
    striker_id = match.striker

    try:
        bat_msg: Message = await client.listen(
            chat_id=chat_id,
            filters=filters.text & filters.user(striker_id),
            timeout=Config.BAT_TIMEOUT
        )
        try:
            number = int(bat_msg.text.strip())
            if not (1 <= number <= 6):
                raise ValueError
        except ValueError:
            return await wait_for_team_bat(client, chat_id)
        await resolve_team_ball(client, chat_id, number, timed_out=False)
    except asyncio.TimeoutError:
        await resolve_team_ball(client, chat_id, None, timed_out=True)

async def resolve_team_ball(client: Client, chat_id: int, bat_number, timed_out: bool):
    match = team_matches.get(chat_id)
    if not match:
        return

    batting_team_dict = get_team_dict(match, match.batting_team)
    bowling_team_dict = get_team_dict(match, match.bowling_team)
    striker = batting_team_dict[match.striker]
    bowler  = bowling_team_dict[match.current_bowler]
    bowl_number = match.bowler_number

    match.ball_count += 1
    bowler.balls_bowled += 1

    is_wicket = False
    if timed_out:
        is_wicket = True
        await client.send_message(chat_id, "⏱️  **Time's up!** Auto OUT!")
        await send_wicket_gif(client, chat_id, striker.full_name)
    elif bowl_number is not None and bat_number == bowl_number:
        is_wicket = True
        await send_wicket_gif(client, chat_id, striker.full_name)
    else:
        runs = bat_number
        striker.runs += runs
        striker.balls += 1
        if runs == 4:
            striker.fours += 1
        elif runs == 6:
            striker.sixes += 1
        bowler.runs_given += runs

        if match.batting_team == "A":
            match.team_a_score += runs
        else:
            match.team_b_score += runs

        if runs == 0:
            await client.send_message(chat_id, dot_ball_msg(striker.full_name))
        else:
            await send_run_gif(client, chat_id, runs, striker.full_name)

        if striker.runs in (50, 100):
            await client.send_message(chat_id, century_msg(striker.full_name, striker.runs))

        # Odd runs → swap strike
        if runs % 2 == 1 and match.non_striker:
            match.striker, match.non_striker = match.non_striker, match.striker

    if is_wicket:
        striker.is_out = True
        bowler.wickets += 1
        if match.batting_team == "A":
            match.team_a_wickets += 1
        else:
            match.team_b_wickets += 1

        match.last_3_wickets.append(match.current_bowler)
        if len(match.last_3_wickets) >= 3 and len(set(match.last_3_wickets[-3:])) == 1:
            await client.send_message(chat_id, f"🎩  **HAT-TRICK!!!** {bowler.full_name} is on fire! 🔥")

        # Promote non-striker or need new batter
        if match.non_striker:
            match.striker = match.non_striker
            match.non_striker = None
        else:
            match.striker = None

    match.bowler_number = None

    # Check target chase win
    if match.innings == 2 and match.target is not None:
        current_score = match.team_a_score if match.batting_team == "A" else match.team_b_score
        if current_score >= match.target:
            return await finish_team_match(client, chat_id)

    # Check innings/over completion
    wickets_count = match.team_a_wickets if match.batting_team == "A" else match.team_b_wickets
    team_size = len(get_team_dict(match, match.batting_team))
    all_out = wickets_count >= max(team_size - 1, 1)
    overs_done = match.ball_count >= match.overs

    if all_out or overs_done:
        if all_out and not match.striker:
            pass
        await end_innings_or_over(client, chat_id, all_out)
        return

    if match.striker is None:
        bat_cap_id = get_cap_id(match, match.batting_team)
        await client.send_message(
            chat_id,
            f"🏏  **{batting_team_dict[bat_cap_id].full_name}**, choose your next batter!\nUse `/batting` (reply to player)"
        )
    else:
        await prompt_team_batter(client, chat_id)

async def end_innings_or_over(client: Client, chat_id: int, all_out: bool):
    match = team_matches.get(chat_id)
    if not match:
        return

    if all_out or match.ball_count >= match.overs:
        if match.innings == 1:
            # Switch innings
            score = match.team_a_score if match.batting_team == "A" else match.team_b_score
            match.target = score + 1
            match.innings = 2
            old_batting, old_bowling = match.batting_team, match.bowling_team
            match.batting_team, match.bowling_team = old_bowling, old_batting
            match.striker = None
            match.non_striker = None
            match.current_bowler = None
            match.ball_count = 0

            await client.send_message(
                chat_id,
                innings_break_msg(
                    get_team_dict(match, old_batting)[get_cap_id(match, old_batting)].full_name,
                    score,
                    match.team_a_wickets if old_batting == "A" else match.team_b_wickets,
                    match.target
                )
            )
            bowl_cap_id = get_cap_id(match, match.bowling_team)
            await client.send_message(
                chat_id,
                f"🎯  **{get_team_dict(match, match.bowling_team)[bowl_cap_id].full_name}**, choose your bowler!\nUse `/bowling`"
            )
        else:
            await finish_team_match(client, chat_id)
    else:
        # Just an over change — same innings continues, new bowler needed
        bowl_cap_id = get_cap_id(match, match.bowling_team)
        match.current_bowler = None
        await client.send_message(
            chat_id,
            f"📋  **Over complete!**\n\n"
            f"🎯  **{get_team_dict(match, match.bowling_team)[bowl_cap_id].full_name}**, choose next bowler!\nUse `/bowling`"
        )

async def finish_team_match(client: Client, chat_id: int):
    match = team_matches.get(chat_id)
    if not match:
        return
    match.phase = GamePhase.FINISHED

    if match.team_a_score > match.team_b_score:
        winner = "🔴 Team A"
        winning_dict = match.team_a
    elif match.team_b_score > match.team_a_score:
        winner = "🔵 Team B"
        winning_dict = match.team_b
    else:
        winner = "🤝 Match Tied"
        winning_dict = {**match.team_a, **match.team_b}

    all_players = {**match.team_a, **match.team_b}
    if all_players:
        motm = max(all_players.values(), key=lambda p: p.runs + p.wickets * 15)
    else:
        motm = None

    text = team_result_card(match, winner, motm.full_name if motm else "N/A")
    await client.send_message(chat_id, text)
    if motm:
        await send_trophy_gif(client, chat_id, f"⭐️  **Player of the Match:** {motm.full_name}")

    won_team = "A" if "Team A" in winner else ("B" if "Team B" in winner else None)
    for side, team_dict in [("A", match.team_a), ("B", match.team_b)]:
        for p in team_dict.values():
            await update_batting_stats(
                p.user_id, p.full_name, p.runs, p.balls, p.fours, p.sixes,
                p.is_out, won=(side == won_team)
            )
            if p.balls_bowled > 0:
                await update_bowling_stats(p.user_id, p.full_name, p.wickets, p.runs_given, p.balls_bowled, p.wickets >= 3)

    if motm:
        await update_motm(motm.user_id, motm.full_name)

    del team_matches[chat_id]
