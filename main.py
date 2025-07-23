import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, executor, types
from bs4 import BeautifulSoup
import requests

API_TOKEN = '7918239240:AAFMiTPq8mut9W1-xmxxi69xoNyHFB_zAoE'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

URL = "https://virastisad.ru/stock/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_data():
    resp = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(resp.text, 'html.parser')
    blocks = soup.find_all("div", class_="stock-block")

    data = {"seed": [], "gear": [], "egg": [], "zen_stock": [], "weather": "", "zen_status": ""}
    for block in blocks:
        title = block.find("div", class_="stock-title").text.strip()
        items = block.find_all("div", class_="stock-item")
        if "Seed" in title:
            for i in items:
                name = i.find("span", class_="stock-name").text.strip()
                status = i.find("span", class_="stock-status").text.strip()
                qty = i.find("span", class_="stock-qty")
                data["seed"].append(f"🌱 {name} [{status}] {'[' + qty.text.strip() + ']' if qty else ''}")
        elif "Gear" in title:
            for i in items:
                name = i.find("span", class_="stock-name").text.strip()
                status = i.find("span", class_="stock-status").text.strip()
                qty = i.find("span", class_="stock-qty")
                data["gear"].append(f"⚙️ {name} [{status}] {'[' + qty.text.strip() + ']' if qty else ''}")
        elif "Egg" in title:
            for i in items:
                name = i.find("span", class_="stock-name").text.strip()
                status = i.find("span", class_="stock-status").text.strip()
                qty = i.find("span", class_="stock-qty")
                data["egg"].append(f"🥚 {name} [{status}] {'[' + qty.text.strip() + ']' if qty else ''}")
        elif "ZEN Event Items" in title:
            for i in items:
                name = i.find("span", class_="stock-name").text.strip()
                status = i.find("span", class_="stock-status").text.strip()
                data["zen_stock"].append(f"🧘 {name} [{status}]")

    event_status = soup.find("div", id="zen-status")
    if event_status:
        data["zen_status"] = event_status.text.strip()

    weather = soup.find("div", id="weather-status")
    if weather:
        data["weather"] = f"☁️ Текущая погода: {weather.text.strip()}"

    return data

@dp.message_handler(commands=["start", "main"])
async def start_cmd(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🌱 STOCK SEED", callback_data="stock_seed"),
        types.InlineKeyboardButton("⚙️ STOCK GEAR", callback_data="stock_gear"),
    )
    keyboard.add(
        types.InlineKeyboardButton("🥚 EGG STOCK", callback_data="stock_egg"),
        types.InlineKeyboardButton("🧘 ZEN EVENT", callback_data="zen_event")
    )
    keyboard.add(types.InlineKeyboardButton("☁️ WEATHER", callback_data="weather"))
    await message.answer("Выбери категорию:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data in ["stock_seed", "stock_gear", "stock_egg", "zen_event", "weather"])
async def handle_callback(callback_query: types.CallbackQuery):
    data = fetch_data()
    action = callback_query.data
    if action == "stock_seed":
        text = "🌱 <b>Семена в наличии:"</b>
" + "
.join(data["seed"]) if data["seed"] else "Нет семян."
    elif action == "stock_gear":
        text = "⚙️ <b>Предметы Gear в наличии:"</b>
" + "
.join(data["gear"]) if data["gear"] else "Нет Gear."
    elif action == "stock_egg":
        text = "🥚Яйца в наличии:"</b>
" + "
.join(data["egg"]) if data["egg"] else "Нет яиц."
    elif action == "zen_event":
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("🧘 Статус ивента", callback_data="zen_status"),
            types.InlineKeyboardButton("📦 Сток ивента", callback_data="zen_stock")
        )
        await callback_query.message.edit_text("🧘 ZEN EVENT:", reply_markup=kb)
        return
    elif action == "weather":
        text = data["weather"] or "Нет информации о погоде."

    await callback_query.message.edit_text(text, parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data in ["zen_status", "zen_stock"])
async def zen_sub(callback_query: types.CallbackQuery):
    data = fetch_data()
    if callback_query.data == "zen_status":
        await callback_query.message.edit_text(f"🧘 Статус ZEN ивента:"
{data['zen_status']})
    else:
        text = "📦Сток ZEN ивента:"</b>
" + "
.join(data["zen_stock"]) if data["zen_stock"] else "Пусто."
        await callback_query.message.edit_text(text, parse_mode="HTML")

if __name__ == '__main__':
    asyncio.run(dp.start_polling())
