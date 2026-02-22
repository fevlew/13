from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.config import config

def _f(p):
    if p >= 1_000_000_000: return f"{p//1_000_000_000}B"
    if p >= 1_000_000: return f"{p//1_000_000}M"
    if p >= 1_000: return f"{p//1_000}K"
    return str(p)

def main_menu(bal):
    b = InlineKeyboardBuilder()
    b.row(IKB(text="🎰 Слоты", callback_data="game:slots"), IKB(text="🎲 Кубик", callback_data="game:dice"))
    b.row(IKB(text="🎡 Рулетка", callback_data="game:roulette"), IKB(text="🚀 Краш", callback_data="game:crash"))
    b.row(IKB(text="🪙 Монетка", callback_data="game:coinflip"), IKB(text="🎡 Колесо", callback_data="game:wheel"))
    b.row(IKB(text="🏀 Баскет", callback_data="game:basketball"), IKB(text="🎯 Дартс", callback_data="game:darts"))
    b.row(IKB(text="🛒 Магазин", callback_data="shop"), IKB(text="🎁 Бонусы", callback_data="bonuses"))
    b.row(IKB(text="👤 Профиль", callback_data="profile"), IKB(text="📊 Топ", callback_data="top"))
    return b.as_markup()

def shop_menu():
    b = InlineKeyboardBuilder()
    b.row(IKB(text="💳 ПОПОЛНИТЬ БАЛАНС", callback_data="shop:crypto"))
    b.row(IKB(text="🪙 Баффы за монеты", callback_data="shop:coins"))
    b.row(IKB(text="💎 Донат баффы (DC)", callback_data="shop:donate"))
    b.row(IKB(text="💵 Купить DC", callback_data="shop:buy_dc"))
    b.row(IKB(text="📦 Мои баффы", callback_data="shop:my_buffs"))
    b.row(IKB(text="💸 Забрать кешбек", callback_data="shop:cashback"))
    b.row(IKB(text="◀️ Назад", callback_data="menu"))
    return b.as_markup()

def crypto_menu():
    b = InlineKeyboardBuilder()
    for pid, p in config.crypto_packages.items():
        b.row(IKB(text=f"💵 ${p['usd']} → {p['name']}", callback_data=f"crypto:buy:{pid}"))
    b.row(IKB(text="◀️ Назад", callback_data="shop"))
    return b.as_markup()

def shop_levels():
    b = InlineKeyboardBuilder()
    lvls = [(1, "10K"), (2, "100K"), (3, "1M"), (4, "10M"), (5, "100M"), (6, "500M"), (7, "1B")]
    for l, p in lvls:
        b.row(IKB(text=f"{'⭐'*min(l,3)}{'🌟'*(l-3) if l>3 else ''} Ур.{l} ({p})", callback_data=f"shop:level:{l}"))
    b.row(IKB(text="◀️ Назад", callback_data="shop"))
    return b.as_markup()

def shop_level_items(lvl):
    b = InlineKeyboardBuilder()
    for iid, item in config.shop_buffs.items():
        if item["level"] == lvl:
            b.row(IKB(text=f"{item['name']} — {_f(item['price'])}", callback_data=f"shop:buy:{iid}"))
    b.row(IKB(text="◀️ Назад", callback_data="shop:coins"))
    return b.as_markup()

def shop_donate_menu():
    b = InlineKeyboardBuilder()
    for iid, item in config.donate_buffs.items():
        b.row(IKB(text=f"{item['name']} — {item['price']} DC", callback_data=f"shop:dc_buy:{iid}"))
    b.row(IKB(text="◀️ Назад", callback_data="shop"))
    return b.as_markup()

def buy_dc_menu():
    b = InlineKeyboardBuilder()
    b.row(IKB(text="💎 10 DC = 100M", callback_data="buy_dc:10"))
    b.row(IKB(text="💎 50 DC = 500M", callback_data="buy_dc:50"))
    b.row(IKB(text="💎 100 DC = 1B", callback_data="buy_dc:100"))
    b.row(IKB(text="◀️ Назад", callback_data="shop"))
    return b.as_markup()

def dice_menu():
    b = InlineKeyboardBuilder()
    b.row(IKB(text="💯 Точное (x5.5)", callback_data="dice:exact"))
    b.row(IKB(text="📈 Больше", callback_data="dice:more"), IKB(text="📉 Меньше", callback_data="dice:less"))
    b.row(IKB(text="2️⃣4️⃣6️⃣ Чёт", callback_data="dice:even"), IKB(text="1️⃣3️⃣5️⃣ Нечёт", callback_data="dice:odd"))
    b.row(IKB(text="◀️ Назад", callback_data="menu"))
    return b.as_markup()

def dice_numbers(bt):
    b = InlineKeyboardBuilder()
    for i in range(1, 7): b.add(IKB(text=str(i), callback_data=f"dice_num:{bt}:{i}"))
    b.adjust(3)
    b.row(IKB(text="◀️ Назад", callback_data="game:dice"))
    return b.as_markup()

def bet_menu(g):
    b = InlineKeyboardBuilder()
    for a in [100, 500, 1000]: b.add(IKB(text=f"🪙{a}", callback_data=f"bet:{g}:{a}"))
    b.adjust(3)
    for a in [5000, 10000, 50000]: b.add(IKB(text=f"💰{a//1000}K", callback_data=f"bet:{g}:{a}"))
    b.adjust(3)
    for a in [100000, 500000, 1000000]: b.add(IKB(text=f"💎{a//1000}K", callback_data=f"bet:{g}:{a}"))
    b.adjust(3)
    for a in [5000000, 10000000, 50000000]: b.add(IKB(text=f"🔥{a//1000000}M", callback_data=f"bet:{g}:{a}"))
    b.adjust(3)
    for a in [500000000, 1000000000, 5000000000]: b.add(IKB(text=f"🔥{a//10000000}M", callback_data=f"bet:{g}:{a}"))
    b.adjust(3)
    for a in [5000000000, 10000000000, 50000000000]: b.add(IKB(text=f"🔥{a//100000000}M", callback_data=f"bet:{g}:{a}"))
    b.adjust(3)
    b.row(IKB(text="◀️ Назад", callback_data="menu"))
    return b.as_markup()

def roulette_menu():
    b = InlineKeyboardBuilder()
    b.row(IKB(text="🔢 Число (x35)", callback_data="roulette:number"))
    b.row(IKB(text="🔴 Красное", callback_data="roulette:red"), IKB(text="⚫ Чёрное", callback_data="roulette:black"))
    b.row(IKB(text="2️⃣ Чётное", callback_data="roulette:even"), IKB(text="1️⃣ Нечётное", callback_data="roulette:odd"))
    b.row(IKB(text="◀️ Назад", callback_data="menu"))
    return b.as_markup()

def roulette_numbers():
    b = InlineKeyboardBuilder()
    for i in range(0, 37): b.add(IKB(text=str(i), callback_data=f"roulette_num:{i}"))
    b.adjust(6)
    b.row(IKB(text="◀️ Назад", callback_data="game:roulette"))
    return b.as_markup()

def crash_menu():
    b = InlineKeyboardBuilder()
    for m in [1.5, 2, 3, 5, 10]: b.add(IKB(text=f"x{m}", callback_data=f"crash:{m}"))
    b.adjust(3)
    b.row(IKB(text="◀️ Назад", callback_data="menu"))
    return b.as_markup()

def coinflip_menu():
    b = InlineKeyboardBuilder()
    b.row(IKB(text="🦅 Орёл", callback_data="coinflip:heads"))
    b.row(IKB(text="🪙 Решка", callback_data="coinflip:tails"))
    b.row(IKB(text="◀️ Назад", callback_data="menu"))
    return b.as_markup()

def bonuses_menu(can_daily):
    b = InlineKeyboardBuilder()
    b.row(IKB(text="🎁 Ежедневный" if can_daily else "⏳ Получен", callback_data="bonus:daily" if can_daily else "noop"))
    b.row(IKB(text="👑 Купить VIP", callback_data="vip:menu"))
    b.row(IKB(text="◀️ Назад", callback_data="menu"))
    return b.as_markup()

def vip_menu():
    b = InlineKeyboardBuilder()
    for k, v in config.vip_prices.items():
        b.row(IKB(text=f"{v['name']} — {_f(v['price'])}", callback_data=f"vip:buy:{k}"))
    b.row(IKB(text="◀️ Назад", callback_data="bonuses"))
    return b.as_markup()

def back_btn(to="menu"): return IKM(inline_keyboard=[[IKB(text="◀️ Назад", callback_data=to)]])

def play_again(g):
    b = InlineKeyboardBuilder()
    b.row(IKB(text="🚀 Ещё!", callback_data=f"game:{g}"), IKB(text="🏠 Меню", callback_data="menu"))
    return b.as_markup()

def play_again_reroll(g, bet):
    b = InlineKeyboardBuilder()
    b.row(IKB(text="🔄 Реролл", callback_data=f"reroll:{g}:{bet}"))
    b.row(IKB(text="🚀 Ещё!", callback_data=f"game:{g}"), IKB(text="🏠 Меню", callback_data="menu"))
    return b.as_markup()

def admin_menu():
    b = InlineKeyboardBuilder()
    b.row(IKB(text="💰 Монеты", callback_data="admin:coins"), IKB(text="❌ Баны", callback_data="admin:bans"))
    b.row(IKB(text="👑 VIP", callback_data="admin:vip"), IKB(text="💎 DC", callback_data="admin:dc"))
    b.row(IKB(text="📊 Стата", callback_data="admin:stats"))
    b.row(IKB(text="🚀 Рассылка", callback_data="admin:broadcast"))
    return b.as_markup()

def admin_coins():
    b = InlineKeyboardBuilder()
    b.row(IKB(text="💰 Выдать", callback_data="admin:give"))
    b.row(IKB(text="💸 Забрать", callback_data="admin:take"))
    b.row(IKB(text="◀️ Назад", callback_data="admin:menu"))
    return b.as_markup()

def admin_back(): return IKM(inline_keyboard=[[IKB(text="◀️ Админка", callback_data="admin:menu")]])