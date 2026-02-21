from dataclasses import dataclass, field

@dataclass
class Config:
    token: str = "8572545268:AAHWNybSDi__LxxBZ2JPuZgzOhEWK9fsbZA"
    admin_ids: list[int] = field(default_factory=lambda: [5963673317])
    cryptobot_token: str = "534867:AAtCAOQfdiEYBvSKLJw2jcb2wfMKtFW70fR"
    welcome_bonus: int = 5000
    daily_bonus: int = 1000
    
    min_transfer: int = 100
    transfer_fee: float = 0.05
    donate_rate: int = 10_000_000  # 10M = 1 DC
    
    # 💳 CRYPTOBOT
    crypto_packages: dict = field(default_factory=lambda: {
        "pack_5": {"usd": 5, "coins": 50_000_000, "name": "50M монет"},
        "pack_10": {"usd": 10, "coins": 90_000_000, "name": "90M монет"},
        "pack_15": {"usd": 15, "coins": 135_000_000, "name": "135M монет"},
        "pack_25": {"usd": 25, "coins": 250_000_000, "name": "250M монет"},
        "pack_50": {"usd": 50, "coins": 600_000_000, "name": "600M монет"},
        "pack_100": {"usd": 100, "coins": 1_500_000_000, "name": "1.5B монет"},
    })
    
    # 👑 VIP
    vip_prices: dict = field(default_factory=lambda: {
        "1_day": {"price": 100_000, "days": 1, "name": "1 день"},
        "1_week": {"price": 1_000_000, "days": 7, "name": "1 неделя"},
        "1_month": {"price": 3_000_000, "days": 30, "name": "1 месяц"},
        "6_months": {"price": 5_000_000, "days": 180, "name": "6 месяцев"},
        "1_year": {"price": 7_000_000, "days": 365, "name": "1 год"},
        "forever": {"price": 10_000_000, "days": 99999, "name": "Навсегда"},
    })
    
    # 🛒 БАФФЫ 7 УРОВНЕЙ
    shop_buffs: dict = field(default_factory=lambda: {
        # ЛВЛ 1 - 10K
        "luck_1": {"name": "🍀 Удача I", "desc": "+2% шанс", "price": 10_000, "hours": 1, "buff": "luck", "power": 0.02, "level": 1},
        "crit_1": {"name": "⚔️ Крит I", "desc": "5% шанс x2", "price": 10_000, "hours": 1, "buff": "crit", "power": 0.05, "level": 1},
        # ЛВЛ 2 - 100K
        "luck_2": {"name": "🍀 Удача II", "desc": "+5% шанс", "price": 100_000, "hours": 3, "buff": "luck", "power": 0.05, "level": 2},
        "crit_2": {"name": "⚔️ Крит II", "desc": "10% шанс x2", "price": 100_000, "hours": 3, "buff": "crit", "power": 0.10, "level": 2},
        "mult_2": {"name": "⚡ Множитель II", "desc": "+5% выигрыш", "price": 100_000, "hours": 3, "buff": "multiplier", "power": 0.05, "level": 2},
        # ЛВЛ 3 - 1M
        "luck_3": {"name": "🍀 Удача III", "desc": "+8% шанс", "price": 1_000_000, "hours": 6, "buff": "luck", "power": 0.08, "level": 3},
        "crit_3": {"name": "⚔️ Крит III", "desc": "15% шанс x2", "price": 1_000_000, "hours": 6, "buff": "crit", "power": 0.15, "level": 3},
        "mult_3": {"name": "⚡ Множитель III", "desc": "+10% выигрыш", "price": 1_000_000, "hours": 6, "buff": "multiplier", "power": 0.10, "level": 3},
        "streak_3": {"name": "🔥 Стрик III", "desc": "+2% за победу подряд", "price": 1_000_000, "hours": 6, "buff": "streak", "power": 0.02, "level": 3},
        # ЛВЛ 4 - 10M
        "luck_4": {"name": "🍀 Удача IV", "desc": "+12% шанс", "price": 10_000_000, "hours": 12, "buff": "luck", "power": 0.12, "level": 4},
        "crit_4": {"name": "⚔️ Крит IV", "desc": "20% шанс x2", "price": 10_000_000, "hours": 12, "buff": "crit", "power": 0.20, "level": 4},
        "mult_4": {"name": "⚡ Множитель IV", "desc": "+20% выигрыш", "price": 10_000_000, "hours": 12, "buff": "multiplier", "power": 0.20, "level": 4},
        "streak_4": {"name": "🔥 Стрик IV", "desc": "+5% за победу", "price": 10_000_000, "hours": 12, "buff": "streak", "power": 0.05, "level": 4},
        "cashback_4": {"name": "💸 Кешбек IV", "desc": "10% возврат", "price": 10_000_000, "hours": 12, "buff": "cashback", "power": 0.10, "level": 4},
        # ЛВЛ 5 - 100M
        "luck_5": {"name": "🍀 Удача V", "desc": "+18% шанс", "price": 100_000_000, "hours": 24, "buff": "luck", "power": 0.18, "level": 5},
        "crit_5": {"name": "⚔️ Крит V", "desc": "25% шанс x3", "price": 100_000_000, "hours": 24, "buff": "crit", "power": 0.25, "level": 5},
        "mult_5": {"name": "⚡ Множитель V", "desc": "+35% выигрыш", "price": 100_000_000, "hours": 24, "buff": "multiplier", "power": 0.35, "level": 5},
        "streak_5": {"name": "🔥 Стрик V", "desc": "+8% за победу", "price": 100_000_000, "hours": 24, "buff": "streak", "power": 0.08, "level": 5},
        "cashback_5": {"name": "💸 Кешбек V", "desc": "20% возврат", "price": 100_000_000, "hours": 24, "buff": "cashback", "power": 0.20, "level": 5},
        "jackpot_5": {"name": "🎰 Джекпот V", "desc": "x2 шанс джекпота", "price": 100_000_000, "hours": 24, "buff": "jackpot", "power": 2.0, "level": 5},
        # ЛВЛ 6 - 500M
        "luck_6": {"name": "🍀 Удача VI", "desc": "+25% шанс", "price": 500_000_000, "hours": 48, "buff": "luck", "power": 0.25, "level": 6},
        "crit_6": {"name": "⚔️ Крит VI", "desc": "30% шанс x3", "price": 500_000_000, "hours": 48, "buff": "crit", "power": 0.30, "level": 6},
        "mult_6": {"name": "⚡ Множитель VI", "desc": "+50% выигрыш", "price": 500_000_000, "hours": 48, "buff": "multiplier", "power": 0.50, "level": 6},
        "streak_6": {"name": "🔥 Стрик VI", "desc": "+12% за победу", "price": 500_000_000, "hours": 48, "buff": "streak", "power": 0.12, "level": 6},
        "cashback_6": {"name": "💸 Кешбек VI", "desc": "30% возврат", "price": 500_000_000, "hours": 48, "buff": "cashback", "power": 0.30, "level": 6},
        "jackpot_6": {"name": "🎰 Джекпот VI", "desc": "x3 шанс джекпота", "price": 500_000_000, "hours": 48, "buff": "jackpot", "power": 3.0, "level": 6},
        "reroll_6": {"name": "🔄 Реролл VI", "desc": "3 переигровки", "price": 500_000_000, "hours": 0, "buff": "reroll", "power": 3, "level": 6},
        # ЛВЛ 7 - 1B
        "luck_7": {"name": "🍀 Удача VII", "desc": "+35% шанс", "price": 1_000_000_000, "hours": 168, "buff": "luck", "power": 0.35, "level": 7},
        "crit_7": {"name": "⚔️ Крит VII", "desc": "40% шанс x4", "price": 1_000_000_000, "hours": 168, "buff": "crit", "power": 0.40, "level": 7},
        "mult_7": {"name": "⚡ Множитель VII", "desc": "+75% выигрыш", "price": 1_000_000_000, "hours": 168, "buff": "multiplier", "power": 0.75, "level": 7},
        "streak_7": {"name": "🔥 Стрик VII", "desc": "+15% за победу", "price": 1_000_000_000, "hours": 168, "buff": "streak", "power": 0.15, "level": 7},
        "cashback_7": {"name": "💸 Кешбек VII", "desc": "50% возврат", "price": 1_000_000_000, "hours": 168, "buff": "cashback", "power": 0.50, "level": 7},
        "jackpot_7": {"name": "🎰 Джекпот VII", "desc": "x5 шанс джекпота", "price": 1_000_000_000, "hours": 168, "buff": "jackpot", "power": 5.0, "level": 7},
        "reroll_7": {"name": "🔄 Реролл VII", "desc": "10 переигровок", "price": 1_000_000_000, "hours": 0, "buff": "reroll", "power": 10, "level": 7},
        "god_7": {"name": "👑 Режим Бога", "desc": "5 игр без проигрышей", "price": 1_000_000_000, "hours": 0, "buff": "god", "power": 5, "level": 7},
    })
    
    # 💎 ДОНАТ БАФФЫ
    donate_buffs: dict = field(default_factory=lambda: {
        "dc_luck": {"name": "💎 Мега Удача", "desc": "+50% шанс 24ч", "price": 40, "hours": 24, "buff": "luck", "power": 0.50},
        "dc_mult": {"name": "💎 Мега Множитель", "desc": "x2 выигрыш 12ч", "price": 50, "hours": 12, "buff": "multiplier", "power": 1.0},
        "dc_crit": {"name": "💎 Мега Крит", "desc": "50% шанс x5", "price": 60, "hours": 12, "buff": "crit", "power": 0.50},
        "dc_jackpot": {"name": "💎 Джекпот Мастер", "desc": "x10 джекпот 24ч", "price": 70, "hours": 24, "buff": "jackpot", "power": 10.0},
        "dc_streak": {"name": "💎 Мега Стрик", "desc": "+25% за победу 24ч", "price": 80, "hours": 24, "buff": "streak", "power": 0.25},
        "dc_cashback": {"name": "💎 Полный Кешбек", "desc": "100% возврат 6ч", "price": 90, "hours": 6, "buff": "cashback", "power": 1.0},
        "dc_god": {"name": "💎 Режим Бога+", "desc": "20 игр без проигрышей", "price": 100, "hours": 0, "buff": "god", "power": 20},
    })

config = Config()