
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
from bs4 import BeautifulSoup
import os

URL = "https://virastisad.ru/stock/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌱 STOCK SEED", callback_data='seed')],
        [InlineKeyboardButton("⚙️ STOCK GEAR", callback_data='gear')],
        [InlineKeyboardButton("🧘 ZEN EVENT", callback_data='zen')],
        [InlineKeyboardButton("☁️ WEATHER", callback_data='weather')],
        [InlineKeyboardButton("🥚 EGG STOCK", callback_data='egg')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📋 Главное меню:", reply_markup=reply_markup)

def fetch_html():
    resp = requests.get(URL)
    return BeautifulSoup(resp.text, "html.parser")

def parse_section(soup, header):
    ul = soup.find("h2", string=lambda t: t and header in t).find_next_sibling("ul")
    return [li.get_text(strip=True) for li in ul.find_all("li")] if ul else []

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    soup = fetch_html()

    if query.data == 'seed':
        seeds = parse_section(soup, "SEED STOCK")
        text = "🌱 <b>Семена в наличии:</b>

"
        for s in seeds:
            name, qty = s.rsplit(' ', 1)
            qty_int = int(qty[1:])
            status = "✅ [IN STOCK]" if qty_int > 0 else "❌ [OUT STOCK]"
            text += f"• {name} {status} [{qty}]
"
        await query.edit_message_text(text, parse_mode="HTML")

    elif query.data == 'gear':
        gear = parse_section(soup, "GEAR STOCK")
        text = "⚙️ <b>Предметы в наличии:</b>

"
        for g in gear:
            name, qty = g.rsplit(' ', 1)
            qty_int = int(qty[1:])
            status = "✅ [IN STOCK]" if qty_int > 0 else "❌ [OUT STOCK]"
            text += f"• {name} {status} [{qty}]
"
        await query.edit_message_text(text, parse_mode="HTML")

    elif query.data == 'zen':
        keyboard = [
            [InlineKeyboardButton("📊 Статус ивента", callback_data='zen_status'),
             InlineKeyboardButton("🎁 STOCK EVENT", callback_data='zen_stock')]
        ]
        await query.edit_message_text("🧘 <b>ZEN EVENT:</b>
Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif query.data == 'zen_status':
        event_block = soup.find("h2", string=lambda t: t and "ZEN EVENT" in t)
        status_text = event_block.find_next_sibling("p").get_text(strip=True) if event_block else "Нет данных"
        active = "✅ <b>АКТИВЕН!</b>" if "active" in status_text.lower() else "❌ <b>ЗАКОНЧИЛСЯ</b>"
        await query.edit_message_text(f"🧘 <b>Статус ZEN Event:</b>

{active}
🕒 {status_text}", parse_mode="HTML")

    elif query.data == 'zen_stock':
        zen_items = parse_section(soup, "ZEN EVENT")
        text = "🎁 <b>Предметы ZEN ивента:</b>

"
        for item in zen_items:
            if "Event" not in item:
                name, qty = item.rsplit(' ', 1)
                text += f"• {name} [{qty}]
"
        await query.edit_message_text(text, parse_mode="HTML")

    elif query.data == 'weather':
        weather_block = soup.find("h2", string=lambda t: t and "WEATHER" in t)
        weather_text = weather_block.find_next_sibling("p").get_text(strip=True) if weather_block else "Нет данных"
        await query.edit_message_text(f"☁️ <b>Текущая погода:</b>

{weather_text}", parse_mode="HTML")

    elif query.data == 'egg':
        eggs = parse_section(soup, "EGG STOCK")
        text = "🥚 <b>Яйца в наличии:</b>

"
        for egg in eggs:
            name, qty = egg.rsplit(' ', 1)
            qty_int = int(qty[1:])
            status = "✅ [IN STOCK]" if qty_int > 0 else "❌ [OUT STOCK]"
            text += f"• {name} {status} [{qty}]
"
        await query.edit_message_text(text, parse_mode="HTML")

def main():
    from telegram.ext import Defaults
    TOKEN = os.getenv("TG_BOT_TOKEN")  # Вставь сюда токен, если не хочешь использовать переменные окружения
    application = Application.builder().token(TOKEN).defaults(Defaults(parse_mode="HTML")).build()
    application.add_handler(CommandHandler("main", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

main()
