import random
from dataclasses import dataclass
from enum import Enum

class DiceBetType(Enum):
    EXACT = "exact"
    MORE_THAN = "more"
    LESS_THAN = "less"
    EVEN = "even"
    ODD = "odd"

class DiceGame:
    @staticmethod
    def calculate_multiplier(bt, v):
        if bt == DiceBetType.EXACT: return 5.5
        if bt in [DiceBetType.EVEN, DiceBetType.ODD]: return 1.9
        if bt == DiceBetType.MORE_THAN:
            c = (6 - v) / 6
            return round(0.95 / c, 2) if c > 0 else 0
        if bt == DiceBetType.LESS_THAN:
            c = (v - 1) / 6
            return round(0.95 / c, 2) if c > 0 else 0
        return 0
    
    @staticmethod
    def check_win(r, bt, v):
        if bt == DiceBetType.EXACT: return r == v
        if bt == DiceBetType.EVEN: return r % 2 == 0
        if bt == DiceBetType.ODD: return r % 2 == 1
        if bt == DiceBetType.MORE_THAN: return r > v
        if bt == DiceBetType.LESS_THAN: return r < v
        return False

@dataclass
class SlotResult:
    symbols: tuple
    won: bool
    multiplier: float
    win_amount: int
    is_jackpot: bool
    description: str

class SlotsGame:
    SYMBOLS = ["🎰", "🍇", "🍋", "7️⃣"]
    PAYOUTS = {("7️⃣","7️⃣","7️⃣"): 50, ("🎰","🎰","🎰"): 25, ("🍇","🍇","🍇"): 10, ("🍋","🍋","🍋"): 5}
    
    @staticmethod
    def decode(v):
        v -= 1
        return (SlotsGame.SYMBOLS[v%4], SlotsGame.SYMBOLS[(v//4)%4], SlotsGame.SYMBOLS[(v//16)%4])
    
    @staticmethod
    def check_result(dv, bet):
        s = SlotsGame.decode(dv)
        if s[0] == s[1] == s[2]:
            m = SlotsGame.PAYOUTS.get(s, 5)
            jp = s == ("7️⃣","7️⃣","7️⃣")
            return SlotResult(s, True, m, int(bet*m), jp, "🔥 ДЖЕКПОТ!!!" if jp else f"🎉 ТРИ {s[0]}!")
        if s[0]==s[1] or s[1]==s[2] or s[0]==s[2]:
            match = s[0] if s[0]==s[1] or s[0]==s[2] else s[1]
            if match == "7️⃣": return SlotResult(s, True, 3, int(bet*3), False, "✨ Две 7!")
            if match == "🎰": return SlotResult(s, True, 2, int(bet*2), False, "✨ Два BAR!")
        return SlotResult(s, False, 0, 0, False, "😢 Не повезло...")

class RouletteBetType(Enum):
    NUMBER = "number"
    RED = "red"
    BLACK = "black"
    EVEN = "even"
    ODD = "odd"

@dataclass
class RouletteResult:
    number: int
    won: bool
    multiplier: float
    win_amount: int
    description: str

class RouletteGame:
    RED = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    PAYOUTS = {RouletteBetType.NUMBER: 35, RouletteBetType.RED: 1.9, RouletteBetType.BLACK: 1.9, RouletteBetType.EVEN: 1.9, RouletteBetType.ODD: 1.9}
    
    @staticmethod
    def spin(bet, bt, bv):
        r = random.randint(0, 36)
        won = False
        if bt == RouletteBetType.NUMBER: won = r == bv
        elif bt == RouletteBetType.RED: won = r in RouletteGame.RED
        elif bt == RouletteBetType.BLACK: won = r not in RouletteGame.RED and r != 0
        elif bt == RouletteBetType.EVEN: won = r % 2 == 0 and r != 0
        elif bt == RouletteBetType.ODD: won = r % 2 == 1
        m = RouletteGame.PAYOUTS.get(bt, 0) if won else 0
        c = "🔴" if r in RouletteGame.RED else ("⚫" if r != 0 else "🟢")
        return RouletteResult(r, won, m, int(bet*m) if won else 0, f"{c} {r}")

@dataclass
class CrashResult:
    multiplier: float
    won: bool
    win_amount: int

class CrashGame:
    @staticmethod
    def play(bet, cashout):
        r = random.random()
        if r < 0.5: crash = round(1 + random.random(), 2)
        elif r < 0.8: crash = round(2 + random.random()*3, 2)
        elif r < 0.95: crash = round(5 + random.random()*5, 2)
        else: crash = round(10 + random.random()*40, 2)
        won = cashout <= crash
        return CrashResult(crash, won, int(bet*cashout) if won else 0)

@dataclass
class CoinflipResult:
    result: str
    won: bool
    win_amount: int

class CoinflipGame:
    @staticmethod
    def flip(bet, choice):
        r = random.choice(["heads", "tails"])
        won = r == choice
        return CoinflipResult(r, won, int(bet*1.95) if won else 0)

@dataclass
class WheelResult:
    multiplier: float
    won: bool
    win_amount: int
    color: str

class WheelGame:
    SEGS = [(-2, "⬜", 0.20), (-1.5, "🟨", 0.25), (-1.2, "🟧", 0.20), (1.2, "🟥", 0.15), (1.5, "🟪", 0.10)]
    
    @staticmethod
    def spin(bet):
        r = random.random()
        c = 0
        for m, col, ch in WheelGame.SEGS:
            c += ch
            if r <= c:
                return WheelResult(m, m > 0, int(bet*m), col)
        return WheelResult(0, False, 0, "⬜")