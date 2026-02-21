from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.config import config
from keyboards.inline import admin_menu, admin_coins, admin_back
from database.storage import users_db, get_user, format_balance, save_data, add_vip, get_bot_stats

router = Router()

class AdminStates(StatesGroup):
    waiting_uid = State()
    waiting_amount = State()
    waiting_broadcast = State()
    waiting_days = State()

def is_admin(uid): return uid in config.admin_ids

@router.message(Command("admin"))
async def cmd_admin(msg: Message):
    if not is_admin(msg.from_user.id): return
    s = get_bot_stats()
    await msg.answer(f"👑 <b>АДМИН</b>\n\n👥 {s['total_users']} | 🚫 {s['blocked_users']} | 📅 +{s['new_today']}", reply_markup=admin_menu(), parse_mode="HTML")

@router.callback_query(F.data == "admin:menu")
async def admin_menu_cb(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    s = get_bot_stats()
    await cb.message.edit_text(f"👑 <b>АДМИН</b>\n\n👥 {s['total_users']} | 🚫 {s['blocked_users']}", reply_markup=admin_menu(), parse_mode="HTML")

@router.callback_query(F.data == "admin:coins")
async def admin_coins_cb(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    await cb.message.edit_text("💰 Монеты:", reply_markup=admin_coins())

@router.callback_query(F.data == "admin:give")
async def admin_give(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return
    await state.set_state(AdminStates.waiting_uid)
    await state.update_data(action="give")
    await cb.message.edit_text("Отправь ID:")

@router.callback_query(F.data == "admin:take")
async def admin_take(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return
    await state.set_state(AdminStates.waiting_uid)
    await state.update_data(action="take")
    await cb.message.edit_text("Отправь ID:")

@router.callback_query(F.data == "admin:dc")
async def admin_dc(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return
    await state.set_state(AdminStates.waiting_uid)
    await state.update_data(action="dc")
    await cb.message.edit_text("💎 Выдать DC\nОтправь ID:")

@router.callback_query(F.data == "admin:vip")
async def admin_vip(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return
    await state.set_state(AdminStates.waiting_uid)
    await state.update_data(action="vip")
    await cb.message.edit_text("👑 Выдать VIP\nОтправь ID:")

@router.callback_query(F.data == "admin:bans")
async def admin_bans(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return
    await state.set_state(AdminStates.waiting_uid)
    await state.update_data(action="ban")
    await cb.message.edit_text("🔨 Бан\nОтправь ID:")

@router.callback_query(F.data == "admin:stats")
async def admin_stats(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    s = get_bot_stats()
    coins = sum(u.get("coins", 0) for u in users_db.values())
    wagered = sum(u.get("total_wagered", 0) for u in users_db.values())
    won = sum(u.get("total_won", 0) for u in users_db.values())
    donated = sum(u.get("total_donated", 0) for u in users_db.values())
    await cb.message.edit_text(f"📊 <b>СТАТА</b>\n\n👥 {s['total_users']}\n🪙 {format_balance(coins)}\n💵 ${donated}\n📈 Ставок: {format_balance(wagered)}\n📉 Выиграно: {format_balance(won)}\n💰 Профит: {format_balance(wagered-won)}", reply_markup=admin_back(), parse_mode="HTML")

@router.callback_query(F.data == "admin:broadcast")
async def admin_bc(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return
    await state.set_state(AdminStates.waiting_broadcast)
    await cb.message.edit_text(f"🚀 Отправь текст ({len(users_db)}):")

@router.message(AdminStates.waiting_uid)
async def admin_uid(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    try: uid = int(msg.text.strip())
    except: return await msg.answer("❌ ID!")
    data = await state.get_data()
    action = data.get("action")
    user = get_user(uid)
    await state.update_data(uid=uid)
    if action in ["give", "take"]:
        await state.set_state(AdminStates.waiting_amount)
        await msg.answer(f"✅ {format_balance(user['coins'])}\nСколько?")
    elif action == "dc":
        await state.set_state(AdminStates.waiting_amount)
        await msg.answer(f"✅ {user.get('donate_coins', 0)} DC\nСколько DC?")
    elif action == "vip":
        await state.set_state(AdminStates.waiting_days)
        await msg.answer("Сколько дней?")
    elif action == "ban":
        user["is_banned"] = not user.get("is_banned", False)
        save_data()
        await state.clear()
        await msg.answer(f"{'🔨 Забанен' if user['is_banned'] else '✅ Разбанен'}!", reply_markup=admin_back())

@router.message(AdminStates.waiting_amount)
async def admin_amount(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    try: amount = int(msg.text.strip())
    except: return await msg.answer("❌!")
    data = await state.get_data()
    user = get_user(data["uid"])
    if data["action"] == "give":
        user["coins"] += amount
    elif data["action"] == "take":
        user["coins"] = max(0, user["coins"] - amount)
    elif data["action"] == "dc":
        user["donate_coins"] = user.get("donate_coins", 0) + amount
    save_data()
    await state.clear()
    await msg.answer(f"✅ Готово!\n🪙 {format_balance(user['coins'])}\n💎 {user.get('donate_coins', 0)} DC", reply_markup=admin_back())

@router.message(AdminStates.waiting_days)
async def admin_days(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    try: days = int(msg.text.strip())
    except: return await msg.answer("❌!")
    data = await state.get_data()
    user = get_user(data["uid"])
    add_vip(user, days)
    await state.clear()
    await msg.answer(f"✅ VIP +{days}д!", reply_markup=admin_back())

@router.message(AdminStates.waiting_broadcast)
async def admin_bc_send(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    import asyncio
    from database.storage import mark_user_blocked
    from main import bot
    text = msg.text
    ok = err = 0
    for uid in list(users_db.keys()):
        if users_db[uid].get("is_blocked"): continue
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
            ok += 1
        except:
            mark_user_blocked(uid)
            err += 1
        await asyncio.sleep(0.05)
    await state.clear()
    await msg.answer(f"✅ {ok} | ❌ {err}")

@router.message(Command("cancel"))
async def cmd_cancel(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    await state.clear()
    await msg.answer("✅", reply_markup=admin_menu())