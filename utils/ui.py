from typing import List, Optional

# ── Scorecard Builders ────────────────────────────────────────────────────────

def sr(runs, balls):
    return round((runs / balls) * 100, 1) if balls > 0 else 0.0

def eco(runs, balls):
    overs = balls / 6
    return round(runs / overs, 1) if overs > 0 else 0.0

def bold(text): return f"**{text}**"

def solo_scorecard(players_data: list, overs: int) -> str:
    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        f"🏏  **LIVE SCORECARD**  •  {overs} Over{'s' if overs > 1 else ''}/Player",
        "━━━━━━━━━━━━━━━━━━━━",
    ]
    for i, p in enumerate(players_data, 1):
        status = "✅" if not p["is_out"] else "❌"
        log_str = " • ".join(str(b) for b in p["ball_log"]) if p["ball_log"] else "—"
        lines.append(
            f"{i}. {status}  **{p['full_name']}**\n"
            f"┣  {p['runs']}({p['balls']})  SR:{sr(p['runs'], p['balls'])}  {p['wickets']}W\n"
            f"┣  {log_str}\n"
            f"┗  Eco: {eco(p['runs_given'], p['balls_bowled'])}"
        )
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def solo_result_card(players_data: list, overs: int,
                     best_batter: str, best_bowler: str, motm: str) -> str:
    lines = [
        f"🏏  **Solo Match Result**",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"🎯  {overs} Ball{'s' if overs > 1 else ''}/Over  •  👥  {len(players_data)} Players",
        "━━━━━━━━━━━━━━━━━━━━",
    ]
    for i, p in enumerate(players_data, 1):
        status = "✅" if not p["is_out"] else "❌"
        log_str = " • ".join(str(b) if b != "W" else "W" for b in p["ball_log"]) if p["ball_log"] else "—"
        lines.append(
            f"{i}. {status}  **{p['full_name']}**\n"
            f"┣  {p['runs']}({p['balls']})  SR:{sr(p['runs'], p['balls'])}  {p['wickets']}W\n"
            f"┣  {log_str}\n"
            f"┗  Eco: {eco(p['runs_given'], p['balls_bowled'])}"
        )
    lines += [
        "━━━━━━━━━━━━━━━━━━━━",
        f"🏆  **Best Batter:** {best_batter}",
        f"🎯  **Best Bowler:** {best_bowler}",
        f"⭐️  **Player of the Match:** {motm}",
        "━━━━━━━━━━━━━━━━━━━━",
    ]
    return "\n".join(lines)

def team_scorecard(match) -> str:
    def team_block(team_dict, team_name, score, wickets):
        lines = [f"**{team_name}**  —  {score}/{wickets}"]
        for p in team_dict.values():
            status = "out" if p.is_out else "not out"
            lines.append(
                f"  **{p.full_name}**  {p.runs}({p.balls})  [{status}]"
            )
        return "\n".join(lines)

    return (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📊  **LIVE SCORECARD**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        + team_block(match.team_a, "🔴 Team A", match.team_a_score, match.team_a_wickets) + "\n\n"
        + team_block(match.team_b, "🔵 Team B", match.team_b_score, match.team_b_wickets) + "\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

def team_result_card(match, winner: str, motm_name: str) -> str:
    return (
        f"🏆  **MATCH OVER!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉  **Winner:** {winner}\n\n"
        f"🔴  **Team A:** {match.team_a_score}/{match.team_a_wickets}\n"
        f"🔵  **Team B:** {match.team_b_score}/{match.team_b_wickets}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐️  **Player of the Match:** {motm_name}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

def bat_prompt(batter_name: str, ball_num: int) -> str:
    return (
        f"🏏  **Ball {ball_num}**\n"
        f"**{batter_name}** send your number **1 to 6** in the group!\n"
        f"⏱️  1 minute on the clock..."
    )

def bowl_prompt(bowler_name: str, ball_num: int, total_balls: int) -> str:
    return (
        f"🎯  **Bowling! ({ball_num}/{total_balls})**\n"
        f"**{bowler_name}** send your number in the bot's **DM!**\n"
        f"⏱️  1 minute remaining..."
    )

def dot_ball_msg(batter_name: str) -> str:
    return f"⚫  **Dot ball!** — Defended well, no run! — **{batter_name}**"

def hat_trick_msg(bowler_name: str) -> str:
    return (
        f"🎩  **HAT-TRICK!!!**\n"
        f"🔥  **{bowler_name}** takes 3 wickets in a row — absolutely unstoppable!"
    )

def century_msg(batter_name: str, runs: int) -> str:
    if runs >= 100:
        return f"💯  **CENTURY!** — **{batter_name}** reaches **{runs}** — what a knock!"
    return f"🏅  **HALF-CENTURY!** — **{batter_name}** reaches **{runs}** — brilliant batting!"

def toss_msg(winner_name: str, choice: str) -> str:
    return (
        f"🪙  **TOSS TIME!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎲  The coin is in the air...\n\n"
        f"🏆  **{winner_name}** wins the toss!\n"
        f"➡️  Chose to **{choice}** first.\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

def over_summary(over_num: int, runs_this_over: int, bowler_name: str) -> str:
    return (
        f"📋  **End of Over {over_num}**\n"
        f"🏏  Runs this over: **{runs_this_over}**\n"
        f"🎯  Bowled by: **{bowler_name}**"
    )

def innings_break_msg(batting_team: str, score: int, wickets: int, target: int) -> str:
    return (
        f"🔄  **INNINGS BREAK!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"**{batting_team}** scored **{score}/{wickets}**\n\n"
        f"🎯  Target: **{target}** runs\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

def stats_card(user_name: str, s: dict) -> str:
    balls = s.get("balls_faced", 0)
    runs  = s.get("runs", 0)
    balled = s.get("balls_bowled", 0)
    wkts  = s.get("wickets_taken", 0)
    rc    = s.get("runs_conceded", 0)

    strike_rate = sr(runs, balls)
    economy     = eco(rc, balled)

    return (
        f"📊  **{user_name}'s Stats**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏏  **Batting**\n"
        f"┣  Matches:       **{s.get('matches', 0)}**\n"
        f"┣  Runs:          **{runs}**\n"
        f"┣  Balls Faced:   **{balls}**\n"
        f"┣  Strike Rate:   **{strike_rate}**\n"
        f"┣  Highest Score: **{s.get('highest_score', 0)}**\n"
        f"┣  Centuries:     **{s.get('centuries', 0)}**\n"
        f"┣  Half-Centuries:**{s.get('half_centuries', 0)}**\n"
        f"┣  Fours:         **{s.get('fours', 0)}**\n"
        f"┗  Sixes:         **{s.get('sixes', 0)}**\n\n"
        f"🎯  **Bowling**\n"
        f"┣  Wickets:       **{wkts}**\n"
        f"┣  Balls Bowled:  **{balled}**\n"
        f"┣  Runs Conceded: **{rc}**\n"
        f"┣  Economy:       **{economy}**\n"
        f"┗  Hat-Tricks:    **{s.get('hat_tricks', 0)}**\n\n"
        f"🏆  **Honours**\n"
        f"┣  Wins:          **{s.get('wins', 0)}**\n"
        f"┗  Player of Match:**{s.get('motm', 0)}**\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

def leaderboard_card(title: str, players: list, key: str, label: str) -> str:
    medals = ["🥇", "🥈", "🥉"]
    lines  = [
        f"🏆  **{title}**",
        "━━━━━━━━━━━━━━━━━━━━",
    ]
    for i, p in enumerate(players):
        medal = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{medal}  **{p.get('full_name', 'Unknown')}** — {p.get(key, 0)} {label}")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)
