# 🏏 CricketMania Bot

> *Where legends are born.* Real ball-by-ball cricket — straight in your Telegram group.

---

## ✨ Features

- 🧍 **Solo Match** — Every man for himself
- 👥 **Team Match** — Two sides, one champion (Host can join & play too!)
- 🏆 **Tournament Mode** — Multi-team round robin (A, B, C)
- 🎯 Live ball-by-ball gameplay, real-time scorecards
- 🪙 Toss, overs, captains, hat-tricks, century alerts
- 📊 Stats & Leaderboard — runs, wickets, SR, economy, MOTM
- 🎬 GIFs for every event (runs, wickets, sixes, trophy, etc.)
- ⚙️ Admin panel — broadcast, maintenance mode, match control

---

## 📁 Project Structure

```
CricketManiaBot/
├── main.py                 # Entry point
├── config.py                # All environment variables
├── requirements.txt
├── Procfile                 # Railway/Heroku start command
├── railway.json              # Railway deploy config
├── nixpacks.toml             # Python version for Railway
├── .env.example
├── database/
│   ├── __init__.py          # MongoDB connection
│   ├── users.py              # User & group operations
│   └── stats.py               # Stats tracking
├── utils/
│   ├── state.py               # In-memory match state
│   ├── ui.py                   # Message templates / scorecards
│   └── gifs.py                  # GIF fetching & sending
└── plugins/
    ├── start.py                # /start, /help
    ├── admin.py                 # Admin commands
    ├── stats.py                  # /stats, /leaderboard
    ├── solo.py                    # Solo match gameplay
    ├── team_setup.py               # Team joining, captains, toss
    ├── team_gameplay.py             # Team match ball-by-ball
    └── tournament.py                 # Tournament mode
```

---

## 🚀 Setup

### 1. Get Credentials

| Variable | Where to get it |
|---|---|
| `API_ID` / `API_HASH` | [my.telegram.org/apps](https://my.telegram.org/apps) |
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `ADMIN_ID` | [@userinfobot](https://t.me/userinfobot) → your Telegram ID |
| `MONGO_URI` | [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) → free cluster connection string |

### 2. Configure Environment

Copy `.env.example` → `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
API_ID=12345678
API_HASH=abcd1234efgh5678
BOT_TOKEN=123456:ABC-DEF...
ADMIN_ID=987654321
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/
PLAYZONE_LINK=https://t.me/your_playzone_group
SUPPORT_LINK=https://t.me/your_support_group
```

> 💡 GIF links are already wired in `config.py` from the `@assetshaibkl` channel.
> Bot username is auto-detected — no need to set it manually.

### 3. Install & Run Locally

```bash
pip install -r requirements.txt
python3 main.py
```

---

## 🚂 Deploy on Railway

1. Push this code to a **GitHub repo**.
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
3. Select your repo.
4. Go to **Variables** tab → add all the ENV variables from `.env.example`.
5. Railway auto-detects `nixpacks.toml` + `Procfile` and deploys.
6. Check **Deployments → Logs** to confirm: `✅ @YourBot is LIVE!`

### MongoDB Atlas — IP Whitelist
Railway uses dynamic IPs. In Atlas → Network Access → add:
```
0.0.0.0/0
```
(Allow access from anywhere — required since Railway IPs change.)

---

## 🐙 Deploy on GitHub (Push Instructions)

```bash
git init
git add .
git commit -m "🏏 Initial commit - CricketMania Bot"
git branch -M main
git remote add origin https://github.com/<your-username>/CricketManiaBot.git
git push -u origin main
```

> ⚠️ `.env` is git-ignored — never commit real tokens! Use `.env.example` as reference only.

---

## 🎮 Quick Command Reference

| Mode | Start Command |
|---|---|
| Solo Match | `/start` → tap **Solo Match** |
| Team Match | `/start` → tap **Team Match** → `/create_teams` |
| Tournament | `/tournament` |
| Full Help | `/help` |

---

## ⚠️ Important Notes

- Bowler **must** `/start` the bot in **DM** at least once, or they won't receive bowling prompts.
- Bot needs to be added to the group with permission to **delete/manage messages** (for smooth gameplay).
- Each group can run **only one active match** at a time (Solo / Team / Tournament).

---

🏏 **Built with Pyrogram + MongoDB.** Ready to deploy. Pure cricket, no drama.
