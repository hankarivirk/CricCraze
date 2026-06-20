import itertools
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message
from config import Config
from utils.state import tournaments, Tournament, TournamentTeam, GamePhase
from utils.gifs import send_trophy_gif

@Client.on_message(filters.command("tournament") & filters.group)
async def tournament_start_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id in tournaments:
        return await message.reply("⚠️  Ek tournament already chal raha hai is group mein!")

    t = Tournament(chat_id=chat_id, host_id=message.from_user.id, phase=GamePhase.JOINING)
    t.teams["A"] = TournamentTeam(name="Team A")
    t.teams["B"] = TournamentTeam(name="Team B")
    t.teams["C"] = TournamentTeam(name="Team C")
    tournaments[chat_id] = t

    await message.reply(
        f"🏆  **TOURNAMENT MODE STARTED!**\n\n"
        f"👑  **Host:** {message.from_user.full_name}\n"
        f"👥  3 Teams — A, B, C ({Config.TOURNAMENT_TEAM_SIZE} players each)\n\n"
        f"➡️  Use `/t_join_A`, `/t_join_B`, `/t_join_C` to join a team!\n"
        f"💡  *Host can join too and play!*\n\n"
        f"Host types `/t_start` once teams are full."
    )

async def _join_tournament_team(client, message: Message, team_key: str):
    match = tournaments.get(message.chat.id)
    if not match or match.phase != GamePhase.JOINING:
        return await message.reply("⚠️  No tournament joining open!")
    user = message.from_user

    for key, team in match.teams.items():
        if user.id in team.players:
            return await message.reply(f"✅  Tu already **Team {key}** mein hai!")

    team = match.teams[team_key]
    if len(team.players) >= Config.TOURNAMENT_TEAM_SIZE:
        return await message.reply(f"⚠️  Team {team_key} full hai! (Max {Config.TOURNAMENT_TEAM_SIZE})")

    team.players[user.id] = user.full_name
    await message.reply(f"✅  **{user.full_name}** joined **Team {team_key}**! ({len(team.players)}/{Config.TOURNAMENT_TEAM_SIZE})")

@Client.on_message(filters.command("t_join_A") & filters.group)
async def t_join_a(client: Client, message: Message):
    await _join_tournament_team(client, message, "A")

@Client.on_message(filters.command("t_join_B") & filters.group)
async def t_join_b(client: Client, message: Message):
    await _join_tournament_team(client, message, "B")

@Client.on_message(filters.command("t_join_C") & filters.group)
async def t_join_c(client: Client, message: Message):
    await _join_tournament_team(client, message, "C")

@Client.on_message(filters.command("t_score") & filters.group)
async def t_score_cmd(client: Client, message: Message):
    match = tournaments.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active tournament!")

    lines = ["🏆  **TOURNAMENT STANDINGS**", "━━━━━━━━━━━━━━━━━━━━"]
    sorted_teams = sorted(match.teams.values(), key=lambda t: t.points, reverse=True)
    for i, team in enumerate(sorted_teams, 1):
        players = ", ".join(team.players.values()) or "—"
        lines.append(f"{i}. **{team.name}** — {team.points} pts ({team.wins} wins)\n     {players}")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    await message.reply("\n".join(lines))

@Client.on_message(filters.command("t_start") & filters.group)
async def t_start_cmd(client: Client, message: Message):
    match = tournaments.get(message.chat.id)
    if not match or message.from_user.id != match.host_id:
        return await message.reply("🔒  Only the Host can start the tournament!")

    team_keys = list(match.teams.keys())
    fixtures = list(itertools.combinations(team_keys, 2))
    match.fixtures = fixtures
    match.phase = GamePhase.WAITING

    fixture_text = "\n".join(f"  • {match.teams[a].name} 🆚 {match.teams[b].name}" for a, b in fixtures)
    await message.reply(
        f"🏆  **TOURNAMENT FIXTURES (Round Robin)**\n\n{fixture_text}\n\n"
        f"➡️  Each match will be played as a **Team Match**.\n"
        f"Host, start the first fixture using regular `/start` → Team Match\n"
        f"and manually assign players from the tournament teams.\n\n"
        f"📊  Use `/t_score` to check standings after each match.\n"
        f"📝  Use `/t_result <A/B/C> <A/B/C> <winner>` to log a result.\n"
        f"   Example: `/t_result A B A` (A beat B)"
    )

@Client.on_message(filters.command("t_result") & filters.group)
async def t_result_cmd(client: Client, message: Message):
    match = tournaments.get(message.chat.id)
    if not match or message.from_user.id != match.host_id:
        return await message.reply("🔒  Only the Host can log results!")
    if len(message.command) < 4:
        return await message.reply("⚠️  Usage: `/t_result <TeamA> <TeamB> <Winner>`")

    t1, t2, winner = message.command[1].upper(), message.command[2].upper(), message.command[3].upper()
    if winner not in match.teams:
        return await message.reply("⚠️  Invalid winner team!")

    match.teams[winner].wins += 1
    match.teams[winner].points += 2
    match.results.append((t1, t2, winner))

    await message.reply(
        f"✅  **Result Logged!**\n\n"
        f"{match.teams[t1].name} 🆚 {match.teams[t2].name} → 🏆 **{match.teams[winner].name}** wins!"
    )

    if len(match.results) >= len(match.fixtures):
        await announce_tournament_winner(client, message.chat.id)

async def announce_tournament_winner(client: Client, chat_id: int):
    match = tournaments.get(chat_id)
    if not match:
        return
    sorted_teams = sorted(match.teams.values(), key=lambda t: t.points, reverse=True)
    champion = sorted_teams[0]

    await client.send_message(
        chat_id,
        f"🏆🏆🏆  **TOURNAMENT CHAMPIONS!**  🏆🏆🏆\n\n"
        f"🥇  **{champion.name}** — {champion.points} points!\n\n"
        f"Players: {', '.join(champion.players.values())}\n\n"
        f"🎉  Congratulations, legends! 🏏"
    )
    await send_trophy_gif(client, chat_id, f"🏆 {champion.name} are the Tournament Champions!")

@Client.on_message(filters.command("t_end") & filters.group)
async def t_end_cmd(client: Client, message: Message):
    match = tournaments.get(message.chat.id)
    if not match:
        return await message.reply("⚠️  No active tournament!")
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    is_grp_admin = member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    if message.from_user.id != match.host_id and message.from_user.id != Config.ADMIN_ID and not is_grp_admin:
        return await message.reply("🔒  Only the Host or admin can end the tournament!")
    del tournaments[message.chat.id]
    await message.reply("🛑  **Tournament ended!**")
