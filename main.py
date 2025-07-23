import logging
import json
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, CallbackContext
)

TOKEN = "7918239240:AAFMiTPq8mut9W1-xmxxi69xoNyHFB_zAoE"

logging.basicConfig(level=logging.INFO)

URL = "https://virastisad.ru/stock/"
FAV_FILE = "favorites.json"

# — Утилиты —
def fetch_html():
    return requests.get(URL).text

def parse_lines(keyword):
    soup = BeautifulSoup(fetch_html(), "html.parser")
    lines = []
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if keyword in text:
            lines.append(text)
    return lines

def get_all_stock_items():
    return [li.get_text(strip=True) 
            for li in BeautifulSoup(fetch_html(), "html.parser").find_all("li")
            if "[" in li.get_text()]

# — Избранное —
def load_favs():
    try:
        return json.load(open(FAV_FILE))
    except:
        return {}

def save_favs(d):
    json.dump(d, open(FAV_FILE, "w"), indent=2)

# — Функции меню —
def get_stock_msg(category):
    emoji = {"seed": "🌱", "gear": "⚙️", "egg": "🥚"}
    items = parse_lines(category)
    lines = []
    for text in items:
        name, qty = text.rsplit(" ", 1)
        status = "[IN STOCK ✅]" if "[IN STOCK]" in text else "[OUT STOCK ❌]"
        lines.append(f"{emoji.get(category,'')} <b>{name}</b> {status} {qty}")
    return "\n".join(lines) if lines else "Пока пусто ❌"

def get_weather():
    soup = BeautifulSoup(fetch_html(), "html.parser")
    p = soup.find("h2", string=lambda x: x and "WEATHER" in x)
    txt = p.find_next_sibling("p").get_text(strip=True) if p else ""
    return f"☁️ <b>Погода:</b>\n{txt}"

def get_zen_status():
    soup = BeautifulSoup(fetch_html(), "html.parser")
    p = soup.find("h2", string=lambda x: x and "ZEN EVENT" in x)
    txt = p.find_next_sibling("p").get_text(strip=True) if p else ""
    if "active" in txt.lower():
        return f"✅ <b>ZEN EVENT АКТИВЕН</b>\n🕒 {txt}"
    else:
        return f"❌ <b>ZEN EVENT ЗАКОНЧИЛСЯ</b>\n🕒 {txt}"

def get_zen_stock():
    soup = BeautifulSoup(fetch_html(), "html.parser")
    items = [li.get_text(strip=True) for li in soup.find("h2", string=lambda x: x and "ZEN EVENT" in x).find_next_sibling("ul").find_all("li")]
    return "\n".join(items) if items else "Нет стока."

# — Основные хендлеры —
def cmd_main(update: Update, ctx: CallbackContext):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🌱 STOCK SEED", callback_data="seed")],
                               [InlineKeyboardButton("⚙️ STOCK GEAR", callback_data="gear")],
                               [InlineKeyboardButton("🥚 EGG STOCK", callback_data="egg")],
                               [InlineKeyboardButton("☁️ WEATHER", callback_data="weather")],
                               [InlineKeyboardButton("🧘 ZEN EVENT", callback_data="zen")],
                               [InlineKeyboardButton("⭐ Избранное", callback_data="favorites")]])
    update.message.reply_text("📦 Выбери категорию:", reply_markup=kb)

def cb_query(update: Update, ctx: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data
    if data in ["seed", "gear", "egg"]:
        text = get_stock_msg(data)
        query.edit_message_text(text, parse_mode="HTML")
    elif data == "weather":
        query.edit_message_text(get_weather(), parse_mode="HTML")
    elif data == "zen":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📊 Статус", callback_data="zen_status")],
                                   [InlineKeyboardButton("📦 Сток", callback_data="zen_stock")],
                                   [InlineKeyboardButton("⬅️ Назад", callback_data="back")]])
        query.edit_message_text("🧘 ZEN EVENT:", reply_markup=kb)
    elif data == "zen_status":
        query.edit_message_text(get_zen_status(), parse_mode="HTML")
    elif data == "zen_stock":
        query.edit_message_text(get_zen_stock(), parse_mode="HTML")
    elif data == "back":
        cmd_main(update, ctx)
    elif data == "favorites":
        html = fetch_html()
        items = get_all_stock_items()
        favs = load_favs()
        uid = str(query.from_user.id)
        user_favs = favs.get(uid, [])
        kb = InlineKeyboardMarkup()
        for itm in items:
            mark = "✅" if itm in user_favs else "❌"
            kb.add(InlineKeyboardButton(f"{mark} {itm}", callback_data=f"fav|{itm}"))
        query.edit_message_text("⭐ Избранное — выбери:", reply_markup=kb)
    elif data.startswith("fav|"):
        _, itm = data.split("|",1)
        uid = str(query.from_user.id)
        favs = load_favs()
        user_favs = favs.get(uid, [])
        if itm in user_favs: user_favs.remove(itm)
        else: user_favs.append(itm)
        favs[uid] = user_favs
        save_favs(favs)
        query.answer("Обновлено")
        cb_query(update, ctx)

# — Мониторинг стока —
async def monitor(updater: Updater):
    prev = {}
    while True:
        items = get_all_stock_items()
        favs = load_favs()
        for uid, uitems in favs.items():
            for itm in uitems:
                for cur in items:
                    if itm == cur and "[IN STOCK]" in cur:
                        if prev.get(uid, {}).get(itm) != "IN":
                            updater.bot.send_message(int(uid), f"🔔 *{itm}* теперь в наличии!", parse_mode="Markdown")
                            prev.setdefault(uid, {})[itm] = "IN"
        await asyncio.sleep(300)

def main():
    bot = Updater(TOKEN, use_context=True)
    dp = bot.dispatcher
    dp.add_handler(CommandHandler("main", cmd_main))
    dp.add_handler(CallbackQueryHandler(cb_query))
    # фоновый таск
    loop = asyncio.get_event_loop()
    loop.create_task(monitor(bot))
    bot.start_polling()
    bot.idle()

if __name__ == "__main__":
    main()
