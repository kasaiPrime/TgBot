import logging
import json
import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from bs4 import BeautifulSoup

API_TOKEN = '7918239240:AAFMiTPq8mut9W1-xmxxi69xoNyHFB_zAoE'  # ← ВСТАВЬ СЮДА ТОКЕН

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

URL = "https://virastisad.ru/stock/"
favourites_file = "favourites.json"

# Логгинг
logging.basicConfig(level=logging.INFO)

# Чтение избранных
def load_favourites():
    try:
        with open(favourites_file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_favourites(data):
    with open(favourites_file, "w") as f:
        json.dump(data, f, indent=2)

# Парсинг страницы
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as response:
            html = await response.text()
            return BeautifulSoup(html, "html.parser")

# Сбор всех блоков
async def get_all_blocks():
    soup = await fetch_data()

    def extract(section_id):
        block = soup.find("div", {"id": section_id})
        if not block:
            return "⚠️ Не найдено"
        items = []
        for i in block.find_all("li"):
            name = i.find("span", class_="stock-name").text.strip()
            amount = i.find("span", class_="stock-count")
            if amount:
                items.append(f"✅ {name} [{amount.text.strip()}]")
            else:
                items.append(f"❌ {name} [OUT STOCK]")
        return "\n".join(items) if items else "❌ Пусто"

    return {
        "seed": extract("seed-stock"),
        "gear": extract("gear-stock"),
        "egg": extract("egg-stock"),
        "weather": extract("weather-stock"),
        "zen": {
            "event": extract("zen-event-status"),
            "stock": extract("zen-event-stock")
        }
    }

# Команда /main
@dp.message_handler(commands=['main'])
async def main_menu(msg: types.Message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🌱 STOCK SEED", callback_data="seed"))
    kb.add(types.InlineKeyboardButton("⚙️ STOCK GEAR", callback_data="gear"))
    kb.add(types.InlineKeyboardButton("🥚 EGG STOCK", callback_data="egg"))
    kb.add(types.InlineKeyboardButton("☁️ WEATHER", callback_data="weather"))
    kb.add(types.InlineKeyboardButton("🧘 ZEN EVENT", callback_data="zen_event"))
    await msg.answer("📦 Главное меню:", reply_markup=kb)

# Коллбэки
@dp.callback_query_handler(lambda c: c.data)
async def handle_callback(call: types.CallbackQuery):
    data = await get_all_blocks()
    faves = load_favourites()
    user_id = str(call.from_user.id)

    if call.data == "zen_event":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📅 Статус", callback_data="zen_status"))
        kb.add(types.InlineKeyboardButton("📦 Сток", callback_data="zen_stock"))
        await call.message.edit_text("🧘 Выберите:", reply_markup=kb)
        return

    if call.data == "zen_status":
        await call.message.edit_text(f"🧘‍♂️ ZEN STATUS:\n\n{data['zen']['event']}")
    elif call.data == "zen_stock":
        await call.message.edit_text(f"🎁 ZEN STOCK:\n\n{data['zen']['stock']}")
    elif call.data == "seed":
        await call.message.edit_text(f"🌱 SEED STOCK:\n\n{data['seed']}")
    elif call.data == "gear":
        await call.message.edit_text(f"⚙️ GEAR STOCK:\n\n{data['gear']}")
    elif call.data == "egg":
        await call.message.edit_text(f"🥚 EGG STOCK:\n\n{data['egg']}")
    elif call.data == "weather":
        await call.message.edit_text(f"☁️ CURRENT WEATHER:\n\n{data['weather']}")

# Запуск
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
