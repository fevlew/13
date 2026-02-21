import json
import os
from datetime import datetime, timedelta
from app.config import config

DATA_FILE = "database/users_data.json"
STATS_FILE = "database/bot_stats.json"

users_db = {}
bot_stats = {"total_users": 0, "blocked_users": 0, "daily_joins": {}}
pending_invoices = {}


def _dt_to_str(dt): return dt.isoformat() if dt else None
def _str_to_dt(s):
    try: return datetime.fromisoformat(s) if s else None
    except: return None


def load_data():
    global users_db, bot_stats
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            users_db = {}
            for uid_str, u in raw.items():
                uid = int(uid_str)
                for f in ["last_daily", "created_at", "vip_until", "last_active",
                          "buff_luck_until", "buff_multiplier_until", "buff_crit_until",
                          "buff_streak_until", "buff_cashback_until", "buff_jackpot_until"]:
                    u[f] = _str_to_dt(u.get(f))
                users_db[uid] = u
            print(f"✅ Загружено {len(users_db)} юзеров")
        except Exception as e:
            print(f"❌ {e}")
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                bot_stats = json.load(f)
        except: pass


def save_data():
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        sd = {}
        for uid, u in users_db.items():
            sd[str(uid)] = {
                "coins": u.get("coins", 5000),
                "donate_coins": u.get("donate_coins", 0),
                "username": u.get("username"),
                "total_games": u.get("total_games", 0),
                "total_wins": u.get("total_wins", 0),
                "total_wagered": u.get("total_wagered", 0),
                "total_won": u.get("total_won", 0),
                "is_vip": u.get("is_vip", False),
                "vip_until": _dt_to_str(u.get("vip_until")),
                "is_banned": u.get("is_banned", False),
                "is_blocked": u.get("is_blocked", False),
                "last_daily": _dt_to_str(u.get("last_daily")),
                "last_active": _dt_to_str(u.get("last_active")),
                "daily_multiplier": u.get("daily_multiplier", 1),
                "win_streak": u.get("win_streak", 0),
                "session_losses": u.get("session_losses", 0),
                "reroll_count": u.get("reroll_count", 0),
                "god_mode_games": u.get("god_mode_games", 0),
                "created_at": _dt_to_str(u.get("created_at")),
                "total_donated": u.get("total_donated", 0),
                "buff_luck_until": _dt_to_str(u.get("buff_luck_until")),
                "buff_luck_power": u.get("buff_luck_power", 0),
                "buff_multiplier_until": _dt_to_str(u.get("buff_multiplier_until")),
                "buff_multiplier_power": u.get("buff_multiplier_power", 0),
                "buff_crit_until": _dt_to_str(u.get("buff_crit_until")),
                "buff_crit_power": u.get("buff_crit_power", 0),
                "buff_streak_until": _dt_to_str(u.get("buff_streak_until")),
                "buff_streak_power": u.get("buff_streak_power", 0),
                "buff_cashback_until": _dt_to_str(u.get("buff_cashback_until")),
                "buff_cashback_power": u.get("buff_cashback_power", 0),
                "buff_jackpot_until": _dt_to_str(u.get("buff_jackpot_until")),
                "buff_jackpot_power": u.get("buff_jackpot_power", 0),
            }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(sd, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ {e}")


def save_stats():
    try:
        os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(bot_stats, f, ensure_ascii=False, indent=2)
    except: pass


def get_user(user_id, username=None):
    now = datetime.now()
    if user_id not in users_db:
        users_db[user_id] = {
            "coins": config.welcome_bonus, "donate_coins": 0, "username": username,
            "total_games": 0, "total_wins": 0, "total_wagered": 0, "total_won": 0,
            "is_vip": False, "vip_until": None, "is_banned": False, "is_blocked": False,
            "last_daily": None, "last_active": now, "daily_multiplier": 1,
            "win_streak": 0, "session_losses": 0, "reroll_count": 0, "god_mode_games": 0,
            "created_at": now, "total_donated": 0,
            "buff_luck_until": None, "buff_luck_power": 0,
            "buff_multiplier_until": None, "buff_multiplier_power": 0,
            "buff_crit_until": None, "buff_crit_power": 0,
            "buff_streak_until": None, "buff_streak_power": 0,
            "buff_cashback_until": None, "buff_cashback_power": 0,
            "buff_jackpot_until": None, "buff_jackpot_power": 0,
        }
        date_key = now.strftime("%Y-%m-%d")
        bot_stats["total_users"] = len(users_db)
        bot_stats.setdefault("daily_joins", {})[date_key] = bot_stats.get("daily_joins", {}).get(date_key, 0) + 1
        save_stats(); save_data()
    
    user = users_db[user_id]
    if username: user["username"] = username
    user["last_active"] = now
    if user.get("vip_until") and user["vip_until"] < now:
        user["is_vip"] = False; user["vip_until"] = None
    return user


def get_user_by_username(username):
    uname = username.lower().lstrip("@")
    for uid, u in users_db.items():
        if u.get("username") and u["username"].lower() == uname:
            return uid, u
    return None, None


def mark_user_blocked(uid):
    if uid in users_db:
        users_db[uid]["is_blocked"] = True
        bot_stats["blocked_users"] = sum(1 for u in users_db.values() if u.get("is_blocked"))
        save_data(); save_stats()

def mark_user_unblocked(uid):
    if uid in users_db:
        users_db[uid]["is_blocked"] = False
        save_data()


def check_vip(user):
    if not user.get("is_vip"): return False
    if not user.get("vip_until"): return user.get("is_vip", False)
    return user["vip_until"] > datetime.now()

def get_vip_remaining(user):
    if not user.get("is_vip") or not user.get("vip_until"): return "Нет"
    r = user["vip_until"] - datetime.now()
    if r.days > 3650: return "♾️"
    if r.days > 0: return f"{r.days}д"
    return f"{r.seconds // 3600}ч"

def add_vip(user, days):
    user["is_vip"] = True
    now = datetime.now()
    if user.get("vip_until") and user["vip_until"] > now:
        user["vip_until"] += timedelta(days=days)
    else:
        user["vip_until"] = now + timedelta(days=days)
    save_data()


def check_buff(user, buff):
    f = f"buff_{buff}_until"
    return user.get(f) and user[f] > datetime.now()

def get_buff_power(user, buff):
    return user.get(f"buff_{buff}_power", 0) if check_buff(user, buff) else 0

def get_buff_remaining(user, buff):
    f = f"buff_{buff}_until"
    if not user.get(f) or user[f] < datetime.now(): return "Нет"
    r = user[f] - datetime.now()
    if r.days > 0: return f"{r.days}д"
    return f"{r.seconds // 3600}ч"

def add_buff(user, buff, hours, power):
    f = f"buff_{buff}_until"
    pf = f"buff_{buff}_power"
    now = datetime.now()
    if power >= user.get(pf, 0): user[pf] = power
    if hours > 0:
        if user.get(f) and user[f] > now:
            user[f] += timedelta(hours=hours)
        else:
            user[f] = now + timedelta(hours=hours)
    save_data()


def get_luck_bonus(user): return min(get_buff_power(user, "luck"), 0.50)

def get_multiplier_bonus(user):
    m = 1.0
    if check_vip(user): m += 0.5
    m += get_buff_power(user, "multiplier")
    if check_buff(user, "streak"):
        m += min(get_buff_power(user, "streak") * user.get("win_streak", 0), 1.5)
    return min(m, 4.0)

def get_crit_chance(user): return get_buff_power(user, "crit")
def get_crit_mult(user):
    p = get_buff_power(user, "crit")
    if p >= 0.40: return 4
    if p >= 0.25: return 3
    return 2

def get_jackpot_boost(user): return get_buff_power(user, "jackpot") if check_buff(user, "jackpot") else 1.0
def get_cashback_rate(user): return get_buff_power(user, "cashback")

def add_session_loss(user, amount): user["session_losses"] = user.get("session_losses", 0) + amount

def claim_cashback(user):
    rate = get_cashback_rate(user)
    cb = int(user.get("session_losses", 0) * rate)
    user["session_losses"] = 0
    if cb > 0: user["coins"] += cb; save_data()
    return cb

def use_reroll(user):
    if user.get("reroll_count", 0) > 0:
        user["reroll_count"] -= 1; save_data(); return True
    return False

def has_god_mode(user): return user.get("god_mode_games", 0) > 0
def use_god_mode(user):
    if user.get("god_mode_games", 0) > 0:
        user["god_mode_games"] -= 1; save_data(); return True
    return False

def add_win_streak(user): user["win_streak"] = user.get("win_streak", 0) + 1; save_data()
def reset_win_streak(user): user["win_streak"] = 0; save_data()

def can_claim_daily(user):
    if not user.get("last_daily"): return True
    return datetime.now() - user["last_daily"] >= timedelta(days=1)

def format_balance(c):
    if c >= 1_000_000_000: return f"{c/1_000_000_000:.2f}B"
    if c >= 1_000_000: return f"{c/1_000_000:.1f}M"
    if c >= 1_000: return f"{c/1_000:.1f}K"
    return str(c)

def get_bot_stats():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    return {
        "total_users": len(users_db),
        "blocked_users": sum(1 for u in users_db.values() if u.get("is_blocked")),
        "active_users": len(users_db) - sum(1 for u in users_db.values() if u.get("is_blocked")),
        "new_today": bot_stats.get("daily_joins", {}).get(today, 0),
    }

load_data()