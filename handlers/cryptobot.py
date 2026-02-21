import aiohttp
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from app.config import config
from database.storage import get_user, save_data, format_balance, pending_invoices
from keyboards.inline import back_btn

router = Router()

API = "https://pay.crypt.bot/api"
HEADERS = {"Crypto-Pay-API-Token": config.cryptobot_token}


def crypto_menu():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    for pid, p in config.crypto_packages.items():
        b.row(InlineKeyboardButton(text=f"💵 ${p['usd']} → {p['name']}", callback_data=f"crypto:buy:{pid}"))
    b.row(InlineKeyboardButton(text="◀️ Назад", callback_data="shop"))
    return b.as_markup()


async def api(method, params=None):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{API}/{method}", headers=HEADERS, json=params or {}) as r:
                return await r.json()
    except Exception as e:
        print(f"CryptoBot API error: {e}")
        return {"ok": False, "error": str(e)}


async def create_invoice(uid, pid):
    p = config.crypto_packages.get(pid)
    if not p:
        return None
    
    r = await api("createInvoice", {
        "currency_type": "fiat",
        "fiat": "USD",
        "amount": str(p["usd"]),
        "description": f"ERAFOX Casino: {p['name']}",
        "payload": f"{uid}:{pid}",
        "expires_in": 3600
    })
    
    if r.get("ok"):
        inv = r["result"]
        pending_invoices[inv["invoice_id"]] = {
            "user_id": uid,
            "pack_id": pid,
            "coins": p["coins"],
            "usd": p["usd"],
            "status": "pending"
        }
        return inv
    
    print(f"Create invoice error: {r}")
    return None


async def check_invoice(iid):
    r = await api("getInvoices", {"invoice_ids": iid})
    if r.get("ok") and r["result"].get("items"):
        return r["result"]["items"][0]["status"]
    return "unknown"


async def process_payment(iid):
    inv = pending_invoices.get(iid)
    if not inv or inv["status"] == "paid":
        return False
    
    user = get_user(inv["user_id"])
    user["coins"] += inv["coins"]
    user["total_donated"] = user.get("total_donated", 0) + inv["usd"]
    save_data()
    
    pending_invoices[iid]["status"] = "paid"
    return True


@router.callback_query(F.data == "shop:crypto")
async def crypto_shop(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    
    text = f"""💳 <b>ПОПОЛНЕНИЕ @CryptoBot</b>

🪙 Баланс: {format_balance(user['coins'])}
💵 Задоначено: ${user.get('total_donated', 0)}

📦 <b>Пакеты:</b>
💵 $5 → 50M монет
💵 $10 → 90M монет (+80% бонус!)
💵 $15 → 135M монет (+80% бонус!)
💵 $25 → 250M монет (+100% бонус!)
💵 $50 → 600M монет (+140% бонус!)
💵 $100 → 1.5B монет (+200% бонус!)

⚡ Оплата: USDT, TON, BTC, ETH и др."""
    
    await cb.message.edit_text(text, reply_markup=crypto_menu(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data.startswith("crypto:buy:"))
async def crypto_buy(cb: CallbackQuery):
    pid = cb.data.split(":")[2]
    p = config.crypto_packages.get(pid)
    
    if not p:
        return await cb.answer("❌ Пакет не найден!", show_alert=True)
    
    await cb.answer("⏳ Создаю счёт...")
    
    inv = await create_invoice(cb.from_user.id, pid)
    
    if not inv:
        await cb.message.answer("❌ Ошибка создания счёта. Проверьте токен CryptoBot.")
        return
    
    url = inv.get("mini_app_invoice_url") or inv.get("pay_url")
    iid = inv["invoice_id"]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить в CryptoBot", url=url)],
        [InlineKeyboardButton(text="✅ Я оплатил — проверить", callback_data=f"crypto:check:{iid}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="shop:crypto")]
    ])
    
    text = f"""💳 <b>СЧЁТ СОЗДАН</b>

📦 Пакет: <b>{p['name']}</b>
💵 К оплате: <b>${p['usd']}</b>
🪙 Получите: <b>{format_balance(p['coins'])}</b>

⏱ Счёт действителен 60 минут

👆 Нажмите <b>"Оплатить в CryptoBot"</b>
После оплаты нажмите <b>"Я оплатил"</b>"""
    
    await cb.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("crypto:check:"))
async def crypto_check(cb: CallbackQuery):
    iid = int(cb.data.split(":")[2])
    
    inv = pending_invoices.get(iid)
    if not inv:
        return await cb.answer("❌ Счёт не найден!", show_alert=True)
    
    if inv["status"] == "paid":
        return await cb.answer("✅ Уже зачислено!", show_alert=True)
    
    status = await check_invoice(iid)
    
    if status == "paid":
        success = await process_payment(iid)
        
        if success:
            user = get_user(cb.from_user.id)
            p = config.crypto_packages.get(inv["pack_id"])
            
            text = f"""✅ <b>ОПЛАТА УСПЕШНА!</b>

📦 Пакет: {p['name']}
🪙 Зачислено: <b>+{format_balance(p['coins'])}</b>

💰 Новый баланс: <b>{format_balance(user['coins'])}</b>

❤️ Спасибо за поддержку!"""
            
            await cb.message.edit_text(text, reply_markup=back_btn("menu"), parse_mode="HTML")
            await cb.answer("✅ Монеты зачислены!", show_alert=True)
        else:
            await cb.answer("⚠️ Ошибка. Напишите админу.", show_alert=True)
    
    elif status == "expired":
        await cb.answer("❌ Счёт истёк! Создайте новый.", show_alert=True)
        pending_invoices[iid]["status"] = "expired"
    
    elif status == "active":
        await cb.answer("⏳ Оплата не получена. Оплатите и попробуйте снова.", show_alert=True)
    
    else:
        await cb.answer(f"⏳ Статус: {status}", show_alert=True)


async def check_payments_bg(bot):
    """Фоновая проверка платежей каждые 30 сек"""
    while True:
        try:
            for iid, inv in list(pending_invoices.items()):
                if inv["status"] != "pending":
                    continue
                
                status = await check_invoice(iid)
                
                if status == "paid":
                    success = await process_payment(iid)
                    
                    if success:
                        user = get_user(inv["user_id"])
                        p = config.crypto_packages.get(inv["pack_id"])
                        
                        try:
                            await bot.send_message(
                                inv["user_id"],
                                f"✅ <b>Оплата получена!</b>\n\n🪙 +{format_balance(p['coins'])}\n💰 Баланс: {format_balance(user['coins'])}",
                                parse_mode="HTML"
                            )
                        except:
                            pass
                
                elif status == "expired":
                    pending_invoices[iid]["status"] = "expired"
                
                await asyncio.sleep(1)
        
        except Exception as e:
            print(f"Payment check error: {e}")
        
        await asyncio.sleep(30)


@router.message(Command("check_crypto"))
async def cmd_check_crypto(msg: Message):
    """Проверка подключения к CryptoBot (только для админов)"""
    if msg.from_user.id not in config.admin_ids:
        return
    
    r = await api("getMe")
    
    if r.get("ok"):
        app = r["result"]
        await msg.answer(f"✅ <b>CryptoBot подключён!</b>\n\n🤖 App: {app.get('name')}\n💳 ID: {app.get('app_id')}", parse_mode="HTML")
    else:
        await msg.answer(f"❌ Ошибка: {r}")