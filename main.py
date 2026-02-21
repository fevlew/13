import asyncio
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.config import config
from keyboards.inline import *
from games.all_games import *
from database.storage import *
from handlers import admin, cryptobot

bot = Bot(token=config.token)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(admin.router)
dp.include_router(cryptobot.router)


class GS(StatesGroup):
    dice_type = State()
    dice_num = State()
    roulette_type = State()
    roulette_num = State()
    crash_mult = State()
    coinflip_choice = State()


def apply_win(user, bet, base_m):
    m = get_multiplier_bonus(user)
    win = int(bet * base_m * m)
    crit = False
    if get_crit_chance(user) > 0 and random.random() < get_crit_chance(user):
        win = int(win * get_crit_mult(user))
        crit = True
    user["coins"] += win
    user["total_wins"] += 1
    user["total_won"] += win
    add_win_streak(user)
    save_data()
    return win, crit


def apply_loss(user, bet):
    if has_god_mode(user):
        use_god_mode(user)
        user["coins"] += bet
        return True, False
    add_session_loss(user, bet)
    reset_win_streak(user)
    save_data()
    return False, user.get("reroll_count", 0) > 0


def buffs_text(user):
    b = []
    for bf, nm in [("luck", "🍀"), ("multiplier", "⚡"), ("crit", "⚔️"), ("streak", "🔥"), ("cashback", "💸"), ("jackpot", "🎰")]:
        if check_buff(user, bf):
            b.append(f"{nm} {int(get_buff_power(user, bf)*100)}% ({get_buff_remaining(user, bf)})")
    if user.get("reroll_count", 0) > 0:
        b.append(f"🔄 {user['reroll_count']}")
    if user.get("god_mode_games", 0) > 0:
        b.append(f"👑 {user['god_mode_games']} игр")
    return "\n".join(b) if b else "Нет"


@dp.message(CommandStart())
async def cmd_start(msg: Message):
    user = get_user(msg.from_user.id, msg.from_user.username)
    mark_user_unblocked(msg.from_user.id)
    if user["is_banned"]:
        return await msg.answer("❌ Вы забанены!")
    vip = "👑 " if check_vip(user) else ""
    await msg.answer(
        f"🔥 <b>ERAFOX CASINO</b>\n\n"
        f"{vip}🪙 {format_balance(user['coins'])} | 💎 {user.get('donate_coins', 0)} DC\n"
        f"🔥 Стрик: {user.get('win_streak', 0)}\n\n"
        f"💸 /pay @user сумма — перевод",
        reply_markup=main_menu(user["coins"]),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "menu")
async def menu(cb: CallbackQuery):
    user = get_user(cb.from_user.id, cb.from_user.username)
    vip = "👑 " if check_vip(user) else ""
    await cb.message.edit_text(
        f"🔥 <b>МЕНЮ</b>\n\n"
        f"{vip}🪙 {format_balance(user['coins'])} | 💎 {user.get('donate_coins', 0)} DC",
        reply_markup=main_menu(user["coins"]),
        parse_mode="HTML"
    )
    await cb.answer()


# ====== МАГАЗИН ======
@dp.callback_query(F.data == "shop")
async def shop(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    cb_amt = int(user.get("session_losses", 0) * get_cashback_rate(user))
    await cb.message.edit_text(
        f"🛒 <b>МАГАЗИН</b>\n\n"
        f"🪙 {format_balance(user['coins'])} | 💎 {user.get('donate_coins', 0)} DC\n"
        f"💸 Кешбек: {format_balance(cb_amt)}",
        reply_markup=shop_menu(),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data == "shop:cashback")
async def shop_cashback(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    if not check_buff(user, "cashback"):
        return await cb.answer("❌ Нужен бафф Кешбек!", show_alert=True)
    amt = claim_cashback(user)
    if amt > 0:
        await cb.message.edit_text(
            f"💸 <b>Кешбек получен!</b>\n\n"
            f"+{format_balance(amt)}\n"
            f"🪙 {format_balance(user['coins'])}",
            reply_markup=back_btn("shop"),
            parse_mode="HTML"
        )
        await cb.answer(f"💸 +{format_balance(amt)}!")
    else:
        await cb.answer("❌ Нечего возвращать!", show_alert=True)


@dp.callback_query(F.data == "shop:coins")
async def shop_coins(cb: CallbackQuery):
    await cb.message.edit_text(
        "🪙 <b>БАФФЫ ЗА МОНЕТЫ</b>\n\nВыбери уровень:",
        reply_markup=shop_levels(),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("shop:level:"))
async def shop_level(cb: CallbackQuery):
    lvl = int(cb.data.split(":")[2])
    prices = {1: "10K", 2: "100K", 3: "1M", 4: "10M", 5: "100M", 6: "500M", 7: "1B"}
    await cb.message.edit_text(
        f"⭐ <b>Уровень {lvl}</b> ({prices.get(lvl, '')})",
        reply_markup=shop_level_items(lvl),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("shop:buy:"))
async def shop_buy(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    iid = cb.data.split(":")[2]
    item = config.shop_buffs.get(iid)
    if not item:
        return await cb.answer("❌ Не найден!", show_alert=True)
    if user["coins"] < item["price"]:
        return await cb.answer(f"❌ Нужно {format_balance(item['price'])}", show_alert=True)
    
    user["coins"] -= item["price"]
    
    if item["buff"] == "reroll":
        user["reroll_count"] = user.get("reroll_count", 0) + int(item["power"])
    elif item["buff"] == "god":
        user["god_mode_games"] = user.get("god_mode_games", 0) + int(item["power"])
    else:
        add_buff(user, item["buff"], item["hours"], item["power"])
    
    save_data()
    await cb.message.edit_text(
        f"✅ <b>Куплено!</b>\n\n"
        f"{item['name']}\n"
        f"🪙 {format_balance(user['coins'])}",
        reply_markup=back_btn("shop"),
        parse_mode="HTML"
    )
    await cb.answer("✅ Куплено!")


@dp.callback_query(F.data == "shop:donate")
async def shop_donate(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"💎 <b>ДОНАТ БАФФЫ</b>\n\n"
        f"💎 У вас: {user.get('donate_coins', 0)} DC",
        reply_markup=shop_donate_menu(),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("shop:dc_buy:"))
async def shop_dc_buy(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    iid = cb.data.split(":")[2]
    item = config.donate_buffs.get(iid)
    if not item:
        return await cb.answer("❌ Не найден!", show_alert=True)
    if user.get("donate_coins", 0) < item["price"]:
        return await cb.answer(f"❌ Нужно {item['price']} DC", show_alert=True)
    
    user["donate_coins"] -= item["price"]
    
    if item["buff"] == "god":
        user["god_mode_games"] = user.get("god_mode_games", 0) + int(item["power"])
    else:
        add_buff(user, item["buff"], item["hours"], item["power"])
    
    save_data()
    await cb.message.edit_text(
        f"✅ <b>Куплено!</b>\n\n"
        f"{item['name']}\n"
        f"💎 {user['donate_coins']} DC",
        reply_markup=back_btn("shop"),
        parse_mode="HTML"
    )
    await cb.answer("✅ Куплено!")


@dp.callback_query(F.data == "shop:buy_dc")
async def shop_buy_dc_menu(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"💵 <b>Купить DC за монеты</b>\n\n"
        f"🪙 {format_balance(user['coins'])}\n\n"
        f"Курс: 10M = 1 DC",
        reply_markup=buy_dc_menu(),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("buy_dc:"))
async def buy_dc(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    amt = int(cb.data.split(":")[1])
    cost = amt * config.donate_rate
    if user["coins"] < cost:
        return await cb.answer(f"❌ Нужно {format_balance(cost)}", show_alert=True)
    
    user["coins"] -= cost
    user["donate_coins"] = user.get("donate_coins", 0) + amt
    save_data()
    
    await cb.message.edit_text(
        f"✅ <b>Куплено {amt} DC!</b>\n\n"
        f"💎 {user['donate_coins']} DC\n"
        f"🪙 {format_balance(user['coins'])}",
        reply_markup=back_btn("shop"),
        parse_mode="HTML"
    )
    await cb.answer(f"✅ +{amt} DC!")


@dp.callback_query(F.data == "shop:my_buffs")
async def my_buffs(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"📦 <b>МОИ БАФФЫ</b>\n\n"
        f"{buffs_text(user)}\n\n"
        f"📊 Удача: +{int(get_luck_bonus(user)*100)}%\n"
        f"⚡ Множитель: x{get_multiplier_bonus(user):.2f}\n"
        f"⚔️ Крит: {int(get_crit_chance(user)*100)}%\n"
        f"💸 Кешбек: {int(get_cashback_rate(user)*100)}%",
        reply_markup=back_btn("shop"),
        parse_mode="HTML"
    )
    await cb.answer()


# ====== СЛОТЫ ======
@dp.callback_query(F.data == "game:slots")
async def slots_menu(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"🎰 <b>СЛОТЫ</b>\n\n"
        f"🪙 {format_balance(user['coins'])}\n"
        f"🔥 Стрик: {user.get('win_streak', 0)}",
        reply_markup=bet_menu("slots"),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("bet:slots:"))
async def play_slots(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    bet = int(cb.data.split(":")[2])
    
    if user["coins"] < bet:
        return await cb.answer("❌ Мало монет!", show_alert=True)
    
    user["coins"] -= bet
    user["total_games"] += 1
    user["total_wagered"] += bet
    
    dice = await cb.message.answer_dice(emoji="🎰")
    await asyncio.sleep(3)
    
    r = SlotsGame.check_result(dice.dice.value, bet)
    
    if r.won:
        win, crit = apply_win(user, bet, r.multiplier)
        crit_text = "\n⚔️ <b>КРИТ!</b>" if crit else ""
        text = f"[ {' | '.join(r.symbols)} ]\n\n{r.description}{crit_text}\n\n🎉 +{format_balance(win)}"
        kb = play_again("slots")
    else:
        god, reroll = apply_loss(user, bet)
        if god:
            text = f"[ {' | '.join(r.symbols)} ]\n\n👑 Режим Бога защитил!"
        else:
            text = f"[ {' | '.join(r.symbols)} ]\n\n😢 -{format_balance(bet)}"
        kb = play_again_reroll("slots", bet) if reroll else play_again("slots")
    
    text += f"\n🪙 {format_balance(user['coins'])}"
    await cb.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await cb.answer()


@dp.callback_query(F.data.startswith("reroll:"))
async def reroll(cb: CallbackQuery):
    parts = cb.data.split(":")
    game, bet = parts[1], int(parts[2])
    user = get_user(cb.from_user.id)
    
    if not use_reroll(user):
        return await cb.answer("❌ Нет реролов!", show_alert=True)
    
    user["coins"] += bet
    save_data()
    
    await cb.answer(f"🔄 Реролл! (осталось {user.get('reroll_count', 0)})")
    
    cb.data = f"bet:{game}:{bet}"
    if game == "slots":
        await play_slots(cb)
    elif game == "dice":
        await play_dice(cb, None)
    elif game == "roulette":
        await play_roulette(cb, None)
    elif game == "crash":
        await play_crash(cb, None)
    elif game == "coinflip":
        await play_coinflip(cb, None)


# ====== КУБИК ======
@dp.callback_query(F.data == "game:dice")
async def dice_menu_cb(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"🎲 <b>КУБИК</b>\n\n🪙 {format_balance(user['coins'])}",
        reply_markup=dice_menu(),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("dice:"))
async def dice_type(cb: CallbackQuery, state: FSMContext):
    t = cb.data.split(":")[1]
    await state.update_data(dice_type=t)
    
    if t in ["even", "odd"]:
        await cb.message.edit_text(f"🎲 x1.9", reply_markup=bet_menu(f"dice_{t}"))
    else:
        await cb.message.edit_text("🎲 Выбери число:", reply_markup=dice_numbers(t))
    await cb.answer()


@dp.callback_query(F.data.startswith("dice_num:"))
async def dice_num(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split(":")
    t, n = parts[1], int(parts[2])
    await state.update_data(dice_type=t, dice_num=n)
    
    type_map = {"exact": DiceBetType.EXACT, "more": DiceBetType.MORE_THAN, "less": DiceBetType.LESS_THAN}
    mult = DiceGame.calculate_multiplier(type_map[t], n)
    
    await cb.message.edit_text(f"🎲 x{mult}", reply_markup=bet_menu(f"dice_{t}_{n}"))
    await cb.answer()


@dp.callback_query(F.data.startswith("bet:dice"))
async def play_dice(cb: CallbackQuery, state: FSMContext):
    user = get_user(cb.from_user.id)
    bet = int(cb.data.split(":")[-1])
    
    if user["coins"] < bet:
        return await cb.answer("❌ Мало монет!", show_alert=True)
    
    data = await state.get_data() if state else {}
    t = data.get("dice_type", "even")
    n = data.get("dice_num", 0)
    
    type_map = {
        "exact": DiceBetType.EXACT,
        "more": DiceBetType.MORE_THAN,
        "less": DiceBetType.LESS_THAN,
        "even": DiceBetType.EVEN,
        "odd": DiceBetType.ODD
    }
    bt = type_map.get(t, DiceBetType.EVEN)
    
    user["coins"] -= bet
    user["total_games"] += 1
    user["total_wagered"] += bet
    
    dice = await cb.message.answer_dice(emoji="🎲")
    await asyncio.sleep(2.5)
    
    result = dice.dice.value
    
    if DiceGame.check_win(result, bt, n):
        mult = DiceGame.calculate_multiplier(bt, n)
        win, crit = apply_win(user, bet, mult)
        crit_text = "\n⚔️ <b>КРИТ!</b>" if crit else ""
        text = f"🎲 Выпало: <b>{result}</b>{crit_text}\n\n🎉 +{format_balance(win)}"
        kb = play_again("dice")
    else:
        god, reroll = apply_loss(user, bet)
        if god:
            text = f"🎲 Выпало: <b>{result}</b>\n\n👑 Режим Бога защитил!"
        else:
            text = f"🎲 Выпало: <b>{result}</b>\n\n😢 -{format_balance(bet)}"
        kb = play_again_reroll("dice", bet) if reroll else play_again("dice")
    
    text += f"\n🪙 {format_balance(user['coins'])}"
    await cb.message.answer(text, reply_markup=kb, parse_mode="HTML")
    if state:
        await state.clear()
    await cb.answer()


# ====== РУЛЕТКА ======
@dp.callback_query(F.data == "game:roulette")
async def roulette_menu_cb(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"🎡 <b>РУЛЕТКА</b>\n\n🪙 {format_balance(user['coins'])}",
        reply_markup=roulette_menu(),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("roulette:"))
async def roulette_type(cb: CallbackQuery, state: FSMContext):
    t = cb.data.split(":")[1]
    await state.update_data(roulette_type=t)
    
    if t == "number":
        await cb.message.edit_text("🎡 Выбери число 0-36:", reply_markup=roulette_numbers())
    else:
        await cb.message.edit_text(f"🎡 x1.9", reply_markup=bet_menu(f"roulette_{t}"))
    await cb.answer()


@dp.callback_query(F.data.startswith("roulette_num:"))
async def roulette_num(cb: CallbackQuery, state: FSMContext):
    n = int(cb.data.split(":")[1])
    await state.update_data(roulette_num=n)
    await cb.message.edit_text(f"🎡 Число {n} x35", reply_markup=bet_menu(f"roulette_number_{n}"))
    await cb.answer()


@dp.callback_query(F.data.startswith("bet:roulette"))
async def play_roulette(cb: CallbackQuery, state: FSMContext):
    user = get_user(cb.from_user.id)
    bet = int(cb.data.split(":")[-1])
    
    if user["coins"] < bet:
        return await cb.answer("❌ Мало монет!", show_alert=True)
    
    data = await state.get_data() if state else {}
    t = data.get("roulette_type", "red")
    n = data.get("roulette_num", 0)
    
    type_map = {
        "number": RouletteBetType.NUMBER,
        "red": RouletteBetType.RED,
        "black": RouletteBetType.BLACK,
        "even": RouletteBetType.EVEN,
        "odd": RouletteBetType.ODD
    }
    bt = type_map.get(t, RouletteBetType.RED)
    
    user["coins"] -= bet
    user["total_games"] += 1
    user["total_wagered"] += bet
    
    await cb.message.answer("🎡 Крутим рулетку...")
    await asyncio.sleep(2)
    
    r = RouletteGame.spin(bet, bt, n if bt == RouletteBetType.NUMBER else None)
    
    if r.won:
        win, crit = apply_win(user, bet, r.multiplier)
        crit_text = "\n⚔️ <b>КРИТ!</b>" if crit else ""
        text = f"🎡 {r.description}{crit_text}\n\n🎉 +{format_balance(win)}"
        kb = play_again("roulette")
    else:
        god, reroll = apply_loss(user, bet)
        if god:
            text = f"🎡 {r.description}\n\n👑 Режим Бога защитил!"
        else:
            text = f"🎡 {r.description}\n\n😢 -{format_balance(bet)}"
        kb = play_again_reroll("roulette", bet) if reroll else play_again("roulette")
    
    text += f"\n🪙 {format_balance(user['coins'])}"
    await cb.message.answer(text, reply_markup=kb, parse_mode="HTML")
    if state:
        await state.clear()
    await cb.answer()


# ====== КРАШ ======
@dp.callback_query(F.data == "game:crash")
async def crash_menu_cb(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"🚀 <b>КРАШ</b>\n\n🪙 {format_balance(user['coins'])}\n\nВыбери множитель для вывода:",
        reply_markup=crash_menu(),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("crash:"))
async def crash_mult(cb: CallbackQuery, state: FSMContext):
    m = float(cb.data.split(":")[1])
    await state.update_data(crash_mult=m)
    await cb.message.edit_text(f"🚀 Вывод на x{m}", reply_markup=bet_menu(f"crash_{m}"))
    await cb.answer()


@dp.callback_query(F.data.startswith("bet:crash"))
async def play_crash(cb: CallbackQuery, state: FSMContext):
    user = get_user(cb.from_user.id)
    bet = int(cb.data.split(":")[-1])
    
    if user["coins"] < bet:
        return await cb.answer("❌ Мало монет!", show_alert=True)
    
    data = await state.get_data() if state else {}
    cashout = data.get("crash_mult", 2.0)
    
    user["coins"] -= bet
    user["total_games"] += 1
    user["total_wagered"] += bet
    
    await cb.message.answer("🚀 Ракета стартует...")
    await asyncio.sleep(1.5)
    
    r = CrashGame.play(bet, cashout)
    
    if r.won:
        win, crit = apply_win(user, bet, cashout)
        crit_text = "\n⚔️ <b>КРИТ!</b>" if crit else ""
        text = f"🚀 Краш на x{r.multiplier}{crit_text}\n\n🎉 Успел! +{format_balance(win)}"
        kb = play_again("crash")
    else:
        god, reroll = apply_loss(user, bet)
        if god:
            text = f"🚀 💥 Краш на x{r.multiplier}\n\n👑 Режим Бога защитил!"
        else:
            text = f"🚀 💥 Краш на x{r.multiplier}\n\n😢 Не успел! -{format_balance(bet)}"
        kb = play_again_reroll("crash", bet) if reroll else play_again("crash")
    
    text += f"\n🪙 {format_balance(user['coins'])}"
    await cb.message.answer(text, reply_markup=kb, parse_mode="HTML")
    if state:
        await state.clear()
    await cb.answer()


# ====== МОНЕТКА ======
@dp.callback_query(F.data == "game:coinflip")
async def coinflip_menu_cb(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"🪙 <b>МОНЕТКА</b> x1.95\n\n🪙 {format_balance(user['coins'])}",
        reply_markup=coinflip_menu(),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("coinflip:"))
async def coinflip_choice(cb: CallbackQuery, state: FSMContext):
    choice = cb.data.split(":")[1]
    await state.update_data(coinflip_choice=choice)
    name = "🦅 Орёл" if choice == "heads" else "🪙 Решка"
    await cb.message.edit_text(f"🪙 {name}", reply_markup=bet_menu(f"coinflip_{choice}"))
    await cb.answer()


@dp.callback_query(F.data.startswith("bet:coinflip"))
async def play_coinflip(cb: CallbackQuery, state: FSMContext):
    user = get_user(cb.from_user.id)
    bet = int(cb.data.split(":")[-1])
    
    if user["coins"] < bet:
        return await cb.answer("❌ Мало монет!", show_alert=True)
    
    data = await state.get_data() if state else {}
    choice = data.get("coinflip_choice", "heads")
    
    user["coins"] -= bet
    user["total_games"] += 1
    user["total_wagered"] += bet
    
    r = CoinflipGame.flip(bet, choice)
    emoji = "🦅" if r.result == "heads" else "🪙"
    name = "Орёл" if r.result == "heads" else "Решка"
    
    if r.won:
        win, crit = apply_win(user, bet, 1.95)
        crit_text = "\n⚔️ <b>КРИТ!</b>" if crit else ""
        text = f"{emoji} {name}{crit_text}\n\n🎉 +{format_balance(win)}"
        kb = play_again("coinflip")
    else:
        god, reroll = apply_loss(user, bet)
        if god:
            text = f"{emoji} {name}\n\n👑 Режим Бога защитил!"
        else:
            text = f"{emoji} {name}\n\n😢 -{format_balance(bet)}"
        kb = play_again_reroll("coinflip", bet) if reroll else play_again("coinflip")
    
    text += f"\n🪙 {format_balance(user['coins'])}"
    await cb.message.answer(text, reply_markup=kb, parse_mode="HTML")
    if state:
        await state.clear()
    await cb.answer()


# ====== КОЛЕСО ======
@dp.callback_query(F.data == "game:wheel")
async def wheel_menu_cb(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"🎡 <b>КОЛЕСО ФОРТУНЫ</b>\n\n"
        f"🪙 {format_balance(user['coins'])}\n\n"
        f"⬜x-2 🟨x-1.5 🟧x-1.2 🟥x1.2 🟪x1.5",
        reply_markup=bet_menu("wheel"),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("bet:wheel:"))
async def play_wheel(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    bet = int(cb.data.split(":")[2])
    
    if user["coins"] < bet:
        return await cb.answer("❌ Мало монет!", show_alert=True)
    
    user["coins"] -= bet
    user["total_games"] += 1
    user["total_wagered"] += bet
    
    r = WheelGame.spin(bet)
    
    if r.won:
        win, crit = apply_win(user, bet, r.multiplier)
        crit_text = "\n⚔️ <b>КРИТ!</b>" if crit else ""
        text = f"🎡 {r.color} x{r.multiplier}{crit_text}\n\n🎉 +{format_balance(win)}"
    else:
        god, reroll = apply_loss(user, bet)
        if god:
            text = f"🎡 ⬜ Мимо!\n\n👑 Режим Бога защитил!"
        else:
            text = f"🎡 ⬜ Мимо!\n\n😢 -{format_balance(bet)}"
    
    text += f"\n🪙 {format_balance(user['coins'])}"
    await cb.message.answer(text, reply_markup=play_again("wheel"), parse_mode="HTML")
    await cb.answer()


# ====== СПОРТ ======
@dp.callback_query(F.data.startswith("game:basketball") | F.data.startswith("game:darts"))
async def sport_menu(cb: CallbackQuery):
    game = cb.data.split(":")[1]
    user = get_user(cb.from_user.id)
    emoji = "🏀" if game == "basketball" else "🎯"
    name = "БАСКЕТБОЛ" if game == "basketball" else "ДАРТС"
    desc = "Попади в корзину! (4-5 = WIN)" if game == "basketball" else "Попади в центр! (6 = WIN)"
    
    await cb.message.edit_text(
        f"{emoji} <b>{name}</b>\n\n"
        f"🪙 {format_balance(user['coins'])}\n\n"
        f"{desc}",
        reply_markup=bet_menu(game),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("bet:basketball:") | F.data.startswith("bet:darts:"))
async def play_sport(cb: CallbackQuery):
    parts = cb.data.split(":")
    game, bet = parts[1], int(parts[2])
    user = get_user(cb.from_user.id)
    
    if user["coins"] < bet:
        return await cb.answer("❌ Мало монет!", show_alert=True)
    
    emoji = "🏀" if game == "basketball" else "🎯"
    
    user["coins"] -= bet
    user["total_games"] += 1
    user["total_wagered"] += bet
    
    dice = await cb.message.answer_dice(emoji=emoji)
    await asyncio.sleep(3)
    
    result = dice.dice.value
    won = (result in [4, 5]) if game == "basketball" else (result == 6)
    mult = 2.5 if game == "basketball" else 5.0
    
    if won:
        win, crit = apply_win(user, bet, mult)
        crit_text = "\n⚔️ <b>КРИТ!</b>" if crit else ""
        text = f"{emoji} Результат: {result}{crit_text}\n\n🎉 Попал! +{format_balance(win)}"
    else:
        god, reroll = apply_loss(user, bet)
        if god:
            text = f"{emoji} Результат: {result}\n\n👑 Режим Бога защитил!"
        else:
            text = f"{emoji} Результат: {result}\n\n😢 Мимо! -{format_balance(bet)}"
    
    text += f"\n🪙 {format_balance(user['coins'])}"
    await cb.message.answer(text, reply_markup=play_again(game), parse_mode="HTML")
    await cb.answer()


# ====== БОНУСЫ ======
@dp.callback_query(F.data == "bonuses")
async def bonuses(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    daily = can_claim_daily(user)
    mult = user.get("daily_multiplier", 1)
    
    await cb.message.edit_text(
        f"🎁 <b>БОНУСЫ</b>\n\n"
        f"⏰ Ежедневный: {'✅ Доступен!' if daily else '⏳ Уже получен'}\n"
        f"💰 Награда: {format_balance(config.daily_bonus * mult)} (x{mult})",
        reply_markup=bonuses_menu(daily),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data == "bonus:daily")
async def daily_bonus(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    
    if not can_claim_daily(user):
        return await cb.answer("⏳ Уже получен!", show_alert=True)
    
    mult = user.get("daily_multiplier", 1)
    bonus = config.daily_bonus * mult
    
    user["coins"] += bonus
    user["last_daily"] = datetime.now()
    user["daily_multiplier"] = 1
    save_data()
    
    await cb.message.edit_text(
        f"🎁 <b>Бонус получен!</b>\n\n"
        f"+{format_balance(bonus)}\n"
        f"🪙 {format_balance(user['coins'])}",
        reply_markup=back_btn("bonuses"),
        parse_mode="HTML"
    )
    await cb.answer(f"🎁 +{format_balance(bonus)}!")


# ====== VIP ======
@dp.callback_query(F.data == "vip:menu")
async def vip_menu_cb(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    status = f"✅ ({get_vip_remaining(user)})" if check_vip(user) else "❌ Нет"
    
    await cb.message.edit_text(
        f"👑 <b>VIP СТАТУС</b>\n\n"
        f"Ваш VIP: {status}\n\n"
        f"🎁 Бонусы VIP:\n"
        f"• +50% к выигрышам\n"
        f"• Приоритетная поддержка",
        reply_markup=vip_menu(),
        parse_mode="HTML"
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("vip:buy:"))
async def buy_vip(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    key = cb.data.split(":")[2]
    vip_data = config.vip_prices.get(key)
    
    if not vip_data:
        return await cb.answer("❌ Ошибка!", show_alert=True)
    
    if user["coins"] < vip_data["price"]:
        return await cb.answer(f"❌ Нужно {format_balance(vip_data['price'])}", show_alert=True)
    
    user["coins"] -= vip_data["price"]
    add_vip(user, vip_data["days"])
    save_data()
    
    await cb.message.edit_text(
        f"👑 <b>VIP активирован!</b>\n\n"
        f"📅 Период: {vip_data['name']}\n"
        f"🪙 {format_balance(user['coins'])}",
        reply_markup=back_btn("bonuses"),
        parse_mode="HTML"
    )
    await cb.answer(f"👑 VIP на {vip_data['name']}!")


# ====== ПРОФИЛЬ ======
@dp.callback_query(F.data == "profile")
async def profile(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    wr = (user["total_wins"] / user["total_games"] * 100) if user["total_games"] > 0 else 0
    
    await cb.message.edit_text(
        f"👤 <b>ПРОФИЛЬ</b>\n\n"
        f"🪙 {format_balance(user['coins'])} | 💎 {user.get('donate_coins', 0)} DC\n"
        f"👑 VIP: {get_vip_remaining(user)}\n"
        f"💵 Задоначено: ${user.get('total_donated', 0)}\n\n"
        f"🎮 Игр: {user['total_games']}\n"
        f"🏆 Побед: {user['total_wins']}\n"
        f"📊 Винрейт: {wr:.1f}%\n"
        f"🔥 Стрик: {user.get('win_streak', 0)}\n\n"
        f"📦 <b>Баффы:</b>\n{buffs_text(user)}",
        reply_markup=back_btn(),
        parse_mode="HTML"
    )
    await cb.answer()


# ====== ТОП ======
@dp.callback_query(F.data == "top")
async def top(cb: CallbackQuery):
    sorted_users = sorted(users_db.items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:10]
    
    text = "📊 <b>ТОП-10</b>\n\n"
    
    for i, (uid, u) in enumerate(sorted_users, 1):
        # Медаль
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."
        
        # VIP
        vip = "👑 " if u.get("is_vip") else ""
        
        # Имя
        if u.get("username"):
            name = f"@{u['username']}"
        else:
            name = f"Игрок #{str(uid)[-4:]}"
        
        # Баланс
        coins = format_balance(u.get('coins', 0))
        
        text += f"{medal} {vip}{name} — {coins}\n"
    
    await cb.message.edit_text(text, reply_markup=back_btn(), parse_mode="HTML")
    await cb.answer()


# ====== ПЕРЕВОД ======
@dp.message(Command("pay"))
async def cmd_pay(msg: Message):
    user = get_user(msg.from_user.id, msg.from_user.username)
    args = msg.text.split()[1:]
    
    if len(args) < 2:
        return await msg.answer(
            "💸 <b>Перевод монет</b>\n\n"
            "Использование: /pay @username сумма\n"
            "Пример: /pay @friend 10000\n\n"
            f"Комиссия: {int(config.transfer_fee * 100)}%",
            parse_mode="HTML"
        )
    
    target = args[0].lstrip("@")
    
    try:
        amount = int(args[1])
    except:
        return await msg.answer("❌ Неверная сумма!")
    
    if amount < config.min_transfer:
        return await msg.answer(f"❌ Минимум: {format_balance(config.min_transfer)}")
    
    fee = int(amount * config.transfer_fee)
    total = amount + fee
    
    if user["coins"] < total:
        return await msg.answer(f"❌ Нужно {format_balance(total)} (с комиссией)")
    
    target_id, target_user = get_user_by_username(target)
    
    if not target_id:
        return await msg.answer("❌ Пользователь не найден!")
    
    if target_id == msg.from_user.id:
        return await msg.answer("❌ Нельзя переводить себе!")
    
    user["coins"] -= total
    target_user["coins"] += amount
    save_data()
    
    await msg.answer(
        f"✅ <b>Перевод выполнен!</b>\n\n"
        f"📤 Отправлено: {format_balance(amount)}\n"
        f"👤 Получатель: @{target}\n"
        f"💸 Комиссия: {format_balance(fee)}\n\n"
        f"🪙 Ваш баланс: {format_balance(user['coins'])}",
        parse_mode="HTML"
    )
    
    try:
        await bot.send_message(
            target_id,
            f"💰 <b>Вам перевели монеты!</b>\n\n"
            f"📥 Сумма: {format_balance(amount)}\n"
            f"👤 От: @{msg.from_user.username or 'Аноним'}\n\n"
            f"🪙 Ваш баланс: {format_balance(target_user['coins'])}",
            parse_mode="HTML"
        )
    except:
        pass


@dp.callback_query(F.data == "noop")
async def noop(cb: CallbackQuery):
    await cb.answer()


async def main():
    print(f"🎰 ERAFOX CASINO STARTED")
    print(f"💾 Загружено: {len(users_db)} юзеров")
    
    # Фоновая проверка платежей CryptoBot
    asyncio.create_task(cryptobot.check_payments_bg(bot))
    
    me = await bot.get_me()
    print(f"🤖 Bot: @{me.username}")
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())