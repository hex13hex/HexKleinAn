import asyncio
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import BOT_TOKEN, BACKEND_URL, CHATGPT_URL

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ===============================
# FINITE STATE MACHINE
# ===============================
class SearchState(StatesGroup):
    item = State()
    location = State()
    max_price = State()
    keywords = State()


# ===============================
# START
# ===============================
@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await message.answer("Что вы хотите найти? (Например: Ноутбук, видеокарта HD 5770, ПК)")
    await state.set_state(SearchState.item)


# ===============================
# 1) Что ищем
# ===============================
@dp.message(SearchState.item)
async def get_item(message: Message, state: FSMContext):
    await state.update_data(item=message.text)
    await message.answer("Укажите город и радиус поиска. Пример: 'Бремен +15 км'")
    await state.set_state(SearchState.location)


# ===============================
# 2) Город и радиус
# ===============================
@dp.message(SearchState.location)
async def get_location(message: Message, state: FSMContext):
    await state.update_data(location=message.text)
    await message.answer("Укажите максимальную цену (например: 200)")
    await state.set_state(SearchState.max_price)


# ===============================
# 3) Цена
# ===============================
@dp.message(SearchState.max_price)
async def get_price(message: Message, state: FSMContext):
    await state.update_data(max_price=message.text)
    await message.answer("Укажите дополнительные ключевые слова (например: новая, без повреждений)")
    await state.set_state(SearchState.keywords)


# ===============================
# 4) Ключевые слова → формируем запрос
# ===============================
@dp.message(SearchState.keywords)
async def get_keywords(message: Message, state: FSMContext):
    await state.update_data(keywords=message.text)

    data = await state.get_data()
    await state.clear()

    # Формируем JSON-запрос
    query_json = {
        "item": data["item"],
        "location": data["location"],
        "max_price": data["max_price"],
        "keywords": data["keywords"]
    }

    await message.answer("Ищу объявления… 🔍")

    # 1) Отправка на Python backend (парсер Kleinanzeigen)
    try:
        resp = requests.post(BACKEND_URL, json=query_json)
        ads = resp.json().get("ads", [])
    except Exception as e:
        await message.answer(f"Ошибка соединения с сервером: {e}")
        return

    if not ads:
        await message.answer("Ничего не найдено 😕")
        return

    # 2) Отправка объявлений в ChatGPT (ты выбираешь лучший вариант)
    try:
        gpt_resp = requests.post(CHATGPT_URL, json={"ads": ads})
        best = gpt_resp.json().get("best_option", "Ошибка анализа.")
    except Exception as e:
        best = f"Ошибка отправки в ChatGPT: {e}"

    # 3) Вывод пользователю
    await message.answer(best)


# ===============================
# RUN
# ===============================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())