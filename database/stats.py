from database import stats_col

# ── Initialize Stats ──────────────────────────────────────────────────────────

async def init_stats(user_id: int, full_name: str):
    await stats_col.update_one(
        {"_id": user_id},
        {"$setOnInsert": {
            "_id": user_id,
            "full_name": full_name,
            "matches": 0,
            "wins": 0,
            "runs": 0,
            "balls_faced": 0,
            "wickets_taken": 0,
            "balls_bowled": 0,
            "runs_conceded": 0,
            "centuries": 0,
            "half_centuries": 0,
            "hat_tricks": 0,
            "motm": 0,
            "fours": 0,
            "sixes": 0,
            "highest_score": 0,
            "best_bowling": None
        }},
        upsert=True
    )

# ── Get Stats ─────────────────────────────────────────────────────────────────

async def get_stats(user_id: int):
    return await stats_col.find_one({"_id": user_id})

async def get_leaderboard(sort_by: str = "runs", limit: int = 10):
    return await stats_col.find().sort(sort_by, -1).limit(limit).to_list(length=limit)

# ── Update Stats ──────────────────────────────────────────────────────────────

async def update_batting_stats(user_id: int, full_name: str, runs: int, balls: int,
                                fours: int, sixes: int, is_out: bool, won: bool):
    await init_stats(user_id, full_name)
    update = {
        "$inc": {
            "matches": 1,
            "runs": runs,
            "balls_faced": balls,
            "fours": fours,
            "sixes": sixes,
            "wins": 1 if won else 0
        }
    }
    if runs >= 100:
        update["$inc"]["centuries"] = 1
    elif runs >= 50:
        update["$inc"]["half_centuries"] = 1

    await stats_col.update_one({"_id": user_id}, update)

    # Update highest score
    stat = await get_stats(user_id)
    if stat and runs > stat.get("highest_score", 0):
        await stats_col.update_one({"_id": user_id}, {"$set": {"highest_score": runs}})

async def update_bowling_stats(user_id: int, full_name: str, wickets: int,
                                runs_conceded: int, balls_bowled: int, hat_trick: bool):
    await init_stats(user_id, full_name)
    update = {
        "$inc": {
            "wickets_taken": wickets,
            "runs_conceded": runs_conceded,
            "balls_bowled": balls_bowled,
            "hat_tricks": 1 if hat_trick else 0
        }
    }
    await stats_col.update_one({"_id": user_id}, update)

async def update_motm(user_id: int, full_name: str):
    await init_stats(user_id, full_name)
    await stats_col.update_one({"_id": user_id}, {"$inc": {"motm": 1}})

async def reset_stats(user_id: int):
    await stats_col.delete_one({"_id": user_id})
