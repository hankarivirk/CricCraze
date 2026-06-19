from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

class GamePhase(Enum):
    WAITING    = "waiting"
    JOINING    = "joining"
    BATTING    = "batting"
    BOWLING    = "bowling"
    INNINGS_BREAK = "innings_break"
    FINISHED   = "finished"

class MatchType(Enum):
    SOLO       = "solo"
    TEAM       = "team"
    TOURNAMENT = "tournament"

# ── Solo Match State ──────────────────────────────────────────────────────────

@dataclass
class PlayerScore:
    user_id:    int
    full_name:  str
    runs:       int   = 0
    balls:      int   = 0
    fours:      int   = 0
    sixes:      int   = 0
    is_out:     bool  = False
    wickets:    int   = 0       # as bowler
    runs_given: int   = 0       # as bowler
    balls_bowled: int = 0
    ball_log:   List  = field(default_factory=list)
    consecutive_penalties: int = 0

@dataclass
class SoloMatch:
    chat_id:        int
    host_id:        int
    overs:          int
    phase:          GamePhase       = GamePhase.JOINING
    players:        Dict[int, PlayerScore] = field(default_factory=dict)
    order:          List[int]       = field(default_factory=list)
    current_batter_idx: int         = 0
    current_bowler_idx: int         = 0
    bowl_number:    int             = 0   # current over ball number
    bowler_number:  Optional[int]   = None
    join_msg_id:    Optional[int]   = None
    score_msg_id:   Optional[int]   = None
    timer_task      = None

# ── Team Match State ──────────────────────────────────────────────────────────

@dataclass
class TeamPlayer:
    user_id:   int
    full_name: str
    runs:      int  = 0
    balls:     int  = 0
    fours:     int  = 0
    sixes:     int  = 0
    is_out:    bool = False
    wickets:   int  = 0
    runs_given: int = 0
    balls_bowled: int = 0
    ball_log:  List = field(default_factory=list)

@dataclass
class TeamMatch:
    chat_id:         int
    host_id:         int
    phase:           GamePhase        = GamePhase.JOINING
    team_a:          Dict[int, TeamPlayer] = field(default_factory=dict)
    team_b:          Dict[int, TeamPlayer] = field(default_factory=dict)
    cap_a:           Optional[int]    = None
    cap_b:           Optional[int]    = None
    overs:           int              = 0
    toss_winner:     Optional[str]    = None
    batting_team:    Optional[str]    = None
    bowling_team:    Optional[str]    = None
    innings:         int              = 1
    team_a_score:    int              = 0
    team_b_score:    int              = 0
    team_a_wickets:  int              = 0
    team_b_wickets:  int              = 0
    current_batter:  Optional[int]    = None
    current_bowler:  Optional[int]    = None
    striker:         Optional[int]    = None
    non_striker:     Optional[int]    = None
    ball_count:      int              = 0
    over_count:      int              = 0
    bowler_number:   Optional[int]    = None
    target:          Optional[int]    = None
    last_3_wickets:  List[int]        = field(default_factory=list)
    timer_task       = None
    join_a_msg_id:   Optional[int]    = None
    join_b_msg_id:   Optional[int]    = None

# ── Tournament State ──────────────────────────────────────────────────────────

@dataclass
class TournamentTeam:
    name:    str
    players: Dict[int, str] = field(default_factory=dict)  # user_id: full_name
    wins:    int = 0
    points:  int = 0

@dataclass
class Tournament:
    chat_id:    int
    host_id:    int
    phase:      GamePhase = GamePhase.JOINING
    teams:      Dict[str, TournamentTeam] = field(default_factory=dict)
    fixtures:   List      = field(default_factory=list)
    current_match: Optional[dict] = None
    results:    List      = field(default_factory=list)

# ── Global State ─────────────────────────────────────────────────────────────

solo_matches:       Dict[int, SoloMatch]  = {}
team_matches:       Dict[int, TeamMatch]  = {}
tournaments:        Dict[int, Tournament] = {}
maintenance_mode:   bool = False
