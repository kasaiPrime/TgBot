import requests
import json
import asyncio
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

TOKEN = "ТВОЙ_ТОКЕН_СЮДА"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

URL = "https://virastisad.ru/stock/"
FAV_FILE = "favorites.json"

# Загрузка/сохранение избранного
def load_favorites():
    try:
        with open(FAV_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_favorites(favs):
    with open(FAV_FILE, "w") as f:
        json.dump(favs, f)

# Парсинг сайта
def fetch_data():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text()

# Парсеры по категориям
def parse_seeds(text):
    return [line.strip() for line in text.splitlines() if "seed" in line.lower() and "[" in line]

def parse_gear(text):
    return [line.strip() for line in text.splitlines() if "gear" in line.lower() and "[" in line]

def parse_eggs(text):
    return [line.strip() for line in text.splitlines() if "egg" in line.lower() and "[" in line]

def parse_weather(text):
    for line in text.splitlines():
        if "Current weather" in line:
            return f"☁️ Текущая погода: *{line.split(':')[-1].strip()}*"
    return "☁️ Погода не найдена"

def parse_zen_event(text):
    if "ZEN EVENT ACTIVE" in text:
        return "✅ ZEN Ивент активен!\n🕒 До конца: [уточняется на сайте]"
    elif "ZEN EVENT ENDED" in text:
        return "❌ ZEN Ивент завершён.\n⏳ Следующий ивент: [будет позже]"
    return "ℹ️ Статус ивента неизвестен."

def parse_zen_stock(text):
    return "\n".join([line.strip() for line in text.splitlines() if "ZEN" in line])

def get_all_items(text):
    return [line.strip() for line in text.splitlines() if any(word in line.lower() for word in ["seed", "gear", "egg"]) and "[" in line]

# /main
@dp.message_handler(commands=['main'])
async def send_main_menu(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🌱 STOCK SEED", callback_data="seeds"),
        InlineKeyboardButton("⚙️ STOCK GEAR", callback_data="gear"),
        InlineKeyboardButton("🧘 ZEN EVENT", callback_data="zen"),
        InlineKeyboardButton("☁️ WEATHER", callback_data="weather"),
        InlineKeyboardButton("🥚 EGG STOCK", callback_data="eggs"),
        InlineKeyboardButton("⭐ ИЗБРАННОЕ", callback_data="favorites")
    )
    await message.reply("📊 Главное меню Grow a Garden:", reply_markup=kb)

# /favorites
@dp.message_handler(commands=["favorites"])
async def show_favorites_menu(message: types.Message):
    data = fetch_data()
    all_items = get_all_items(data)

    favs = load_favorites()
    user_id = str(message.from_user.id)
    user_favs = favs.get(user_id, [])

    kb = InlineKeyboardMarkup(row_width=1)
    for item in all_items:
        mark = "✅" if item in user_favs else "❌"
        kb.add(InlineKeyboardButton(f"{mark} {item}", callback_data=f"fav_toggle|{item}"))
    await message.reply("⭐ Выбери предметы для уведомлений:", reply_markup=kb)

# Обработка инлайн-кнопок
@dp.callback_query_handler(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery):
    data = fetch_data()
    user_id = str(callback_query.from_user.id)

    if callback_query.data == "seeds":
        seeds = parse_seeds(data)
        await bot.send_message(callback_query.from_user.id, "🌱 *Семена в наличии:*\n" + "\n".join(seeds), parse_mode="Markdown")
    elif callback_query.data == "gear":
        gear = parse_gear(data)
        await bot.send_message(callback_query.from_user.id, "⚙️ *Снаряжение:*\n" + "\n".join(gear), parse_mode="Markdown")
    elif callback_query.data == "eggs":
        eggs = parse_eggs(data)
        await bot.send_message(callback_query.from_user.id, "🥚 *Яйца:*\n" + "\n".join(eggs), parse_mode="Markdown")
    elif callback_query.data == "weather":
        weather = parse_weather(data)
        await bot.send_message(callback_query.from_user.id, weather, parse_mode="Markdown")
    elif callback_query.data == "zen":
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✅ Статус ZEN", callback_data="zen_status"),
            InlineKeyboardButton("📦 Сток ZEN", callback_data="zen_stock")
        )
        await bot.send_message(callback_query.from_user.id, "🧘 *ZEN EVENT:*", reply_markup=kb, parse_mode="Markdown")
    elif callback_query.data == "zen_status":
        zen_status = parse_zen_event(data)
        await bot.send_message(callback_query.from_user.id, f"🧘 *Статус ZEN:*\n{zen_status}", parse_mode="Markdown")
    elif callback_query.data == "zen_stock":
        zen_stock = parse_zen_stock(data)
        await bot.send_message(callback_query.from_user.id, "📦 *Предметы ZEN EVENT:*\n" + zen_stock, parse_mode="Markdown")
    elif callback_query.data == "favorites":
        await show_favorites_menu(callback_query.message)
    elif callback_query.data.startswith("fav_toggle"):
        _, item = callback_query.data.split("|", 1)
        favs = load_favorites()
        user_favs = favs.get(user_id, [])

        if item in user_favs:
            user_favs.remove(item)
        else:
            user_favs.append(item)

        favs[user_id] = user_favs
        save_favorites(favs)

        await callback_query.answer("Изменено!")
        await show_favorites_menu(callback_query.message)

# Мониторинг
async def monitor_stock():
    prev_stock = {}
    while True:
        try:
            text = fetch_data()
            current = get_all_items(text)
            favs = load_favorites()

            for user_id, items in favs.items():
                for item in items:
                    if item in current and "[IN STOCK]" in item:
                        if prev_stock.get(user_id, {}).get(item) != "IN":
                            await bot.send_message(int(user_id), f"🔔 *{item}* теперь доступен!", parse_mode="Markdown")
                            prev_stock.setdefault(user_id, {})[item] = "IN"
                    elif "[OUT STOCK]" in item:
                        prev_stock.setdefault(user_id, {})[item] = "OUT"
        except Exception as e:
            print("Ошибка в мониторинге:", e)

        await asyncio.sleep(300)  # каждые 5 минут

# Запуск
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(monitor_stock())
    print("✅ Бот запущен!")
    executor.start_polling(dp, skip_updates=True)
