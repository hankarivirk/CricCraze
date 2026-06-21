# 🏏 Cosmic Cricket Bot

A fully-featured Telegram Cricket bot with Solo, Team, and Tournament modes.

---

## 🚀 Setup Guide

### 1. Get Your Credentials

| What | Where |
|------|-------|
| `API_ID` & `API_HASH` | https://my.telegram.org → My Applications |
| `BOT_TOKEN` | Talk to @BotFather on Telegram |
| `ADMIN_ID` | Send a message to @userinfobot |
| `MONGO_URI` | https://cloud.mongodb.com (Free tier works!) |

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in all values
```

### 3. Install & Run

```bash
pip install -r requirements.txt
python main.py
```

### 4. Deploy on Railway (Recommended)

1. Push code to GitHub
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Add environment variables (API_ID, API_HASH, BOT_TOKEN, ADMIN_ID, MONGO_URI)
4. Deploy!

---

## 🎮 Game Modes

### 🧍 Solo Match
- Everyone bats one by one
- Bowler sends number secretly in **DM**
- Batter types 1-6 in the **group**
- Same number = WICKET | Different = Runs

### 👥 Team Match
- Two teams, captains, toss system
- Full innings with batting/bowling order
- Target chase in 2nd innings
- Hat-trick & century alerts

### 🏆 Tournament
- Round-robin tournament with 3 teams
- Standings & point table

---

## 📋 All Commands

| Command | Description |
|---------|-------------|
| `/start` | Start menu (group) or welcome (DM) |
| `/help` | Help menu |
| `/join_solo` | Join solo match |
| `/solo_list` | See joined players |
| `/solo_score` | Live scorecard |
| `/score` | Team match scorecard |
| `/stats` | Your cricket stats |
| `/leaderboard` | Top players |
| `/tournament` | Start tournament |

---

## ⚠️ Important Notes

- **Bowlers MUST start the bot in DM** (`/start` the bot privately) before playing, otherwise their secret bowl number won't reach the bot
- Bot needs **Admin permissions** in the group to function properly
- MongoDB Atlas free tier is enough for personal use

---

## 🐛 What Was Fixed

1. **`member.status` comparison** — Changed `"administrator"` string check to `member.status.value` to match Pyrogram's enum
2. **`client.listen()` crashes** — Added proper try/except for `asyncio.TimeoutError` and `None` checks after re-fetching match state
3. **Race conditions** — After every `await`, the match state is re-fetched from the dict before use
4. **`solo_matches.pop()` instead of `del`** — Prevents `KeyError` crashes on match cleanup
5. **Bot name** — Updated to **Cosmic Cricket 🏏** throughout
6. **Toss system** — Fixed missing toss callback handler that prevented team matches from starting
