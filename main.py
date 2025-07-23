import logging
import requests
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, CallbackContext
)

# 🔐 ЗАМЕНИ на свой токен
TOKEN = "7918239240:AAFMiTPq8mut9W1-xmxxi69xoNyHFB_zAoE"

logging.basicConfig(level=logging.INFO)

def fetch_stock(category):
    url = "https://virastisad.ru/stock/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    items = soup.select(f"#{category} .stock__item")
    output = []

    for item in items:
        name = item.select_one(".stock__name").get_text(strip=True)
        count_el = item.select_one(".stock__count")
        count = count_el.get_text(strip=True) if count_el else "0"
        in_stock = "[IN STOCK ✅]" if "stock__count" in str(count_el) else "[OUT STOCK ❌]"
        emoji = "🥕" if category == "seeds" else "⚙️" if category == "gear" else "🥚"
        output.append(f"{emoji} <b>{name}</b> {in_stock} [{count}]")

    return "\n".join(output) or "Пока пусто ❌"

def fetch_weather():
    response = requests.get("https://virastisad.ru/stock/")
    soup = BeautifulSoup(response.text, "html.parser")
    weather_el = soup.select_one(".weather__block")
    if weather_el:
        return f"☁️ <b>Текущая погода:</b>\n{weather_el.get_text(strip=True)}"
    return "⚠️ Погода не найдена."

def fetch_zen_event():
    response = requests.get("https://virastisad.ru/stock/")
    soup = BeautifulSoup(response.text, "html.parser")
    block = soup.find("div", class_="event")
    if not block:
        return "❌ ZEN ивент не активен."

    active = block.select_one(".event__status")
    if "ACTIVE" in active.text:
        time_left = block.select_one(".event__timer").text.strip()
        return f"✅ <b>ZEN ивент активен!</b>\n🕒 До конца: {time_left}"
    else:
        next_time = block.select_one(".event__next").text.strip()
        return f"❌ ZEN ивент закончился.\n📅 Следующий: {next_time}"

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🌱 STOCK SEED", callback_data='stock_seed')],
        [InlineKeyboardButton("⚙️ STOCK GEAR", callback_data='stock_gear')],
        [InlineKeyboardButton("🥚 EGG STOCK", callback_data='egg_stock')],
        [InlineKeyboardButton("🧘 ZEN EVENT", callback_data='zen_menu')],
        [InlineKeyboardButton("☁️ WEATHER", callback_data='weather')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📦 Выбери категорию:", reply_markup=reply_markup)

def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "stock_seed":
        query.edit_message_text(fetch_stock("seeds"), parse_mode="HTML")
    elif query.data == "stock_gear":
        query.edit_message_text(fetch_stock("gear"), parse_mode="HTML")
    elif query.data == "egg_stock":
        query.edit_message_text(fetch_stock("eggs"), parse_mode="HTML")
    elif query.data == "weather":
        query.edit_message_text(fetch_weather(), parse_mode="HTML")
    elif query.data == "zen_menu":
        keyboard = [
            [InlineKeyboardButton("📊 Статус ивента", callback_data="zen_status")],
            [InlineKeyboardButton("📦 Сток ивента", callback_data="zen_stock")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
        ]
        query.edit_message_text("🧘 <b>ZEN EVENT меню:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "zen_status":
        query.edit_message_text(fetch_zen_event(), parse_mode="HTML")
    elif query.data == "zen_stock":
        query.edit_message_text(fetch_stock("zen"), parse_mode="HTML")
    elif query.data == "back_main":
        start(update, context)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("main", start))
    dp.add_handler(CallbackQueryHandler(handle_callback))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
