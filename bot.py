import os
import requests
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

# =========================
# Конфигурация
# =========================
from config import BOT_TOKEN, BACKEND_URL, CHATGPT_URL

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = Flask(__name__)

# =========================
# FSM: пошаговый диалог
# =========================
class SearchState(StatesGroup):
    item = State()
    location = State()
    max_price = State()
    keywords = State()

# =========================
# Функция для отправки сообщений
# =========================
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

# =========================
# Webhook endpoint
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.json
    if "message" not in update:
        return jsonify({"ok": True})

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")
    user_id = chat_id

    async def process_update():
        state = dp.storage.get_state(chat=user_id, chat_type="private")
        ctx = FSMContext(storage=dp.storage, chat=user_id, user=user_id, bot=bot)

        if text == "/start":
            await ctx.set_state(SearchState.item)
            send_message(chat_id, "Что вы хотите найти? (Например: Ноутбук, ПК, RTX 3060)")
        else:
            current_state = await state
            if current_state is None:
                send_message(chat_id, "Нажмите /start для начала поиска.")
                return

            data = await ctx.get_data() or {}

            if current_state == SearchState.item.state:
                await ctx.update_data(item=text)
                await ctx.set_state(SearchState.location)
                send_message(chat_id, "Укажите город и радиус поиска. Пример: 'Бремен +15 км'")
            elif current_state == SearchState.location.state:
                await ctx.update_data(location=text)
                await ctx.set_state(SearchState.max_price)
                send_message(chat_id, "Укажите максимальную цену (например: 200)")
            elif current_state == SearchState.max_price.state:
                await ctx.update_data(max_price=text)
                await ctx.set_state(SearchState.keywords)
                send_message(chat_id, "Укажите дополнительные ключевые слова (например: новая, без повреждений)")
            elif current_state == SearchState.keywords.state:
                await ctx.update_data(keywords=text)
                await ctx.clear()
                query_json = {
                    "item": data.get("item"),
                    "location": data.get("location"),
                    "max_price": data.get("max_price"),
                    "keywords": text
                }
                send_message(chat_id, "Ищу объявления… 🔍")

                # Отправка на backend
                try:
                    resp = requests.post(BACKEND_URL, json=query_json)
                    ads = resp.json().get("ads", [])
                except Exception as e:
                    send_message(chat_id, f"Ошибка соединения с сервером: {e}")
                    return

                if not ads:
                    send_message(chat_id, "Ничего не найдено 😕")
                    return

                # Отправка в ChatGPT
                try:
                    gpt_resp = requests.post(CHATGPT_URL, json={"ads": ads})
                    best = gpt_resp.json().get("best_option", "Ошибка анализа.")
                except Exception as e:
                    best = f"Ошибка отправки в ChatGPT: {e}"

                send_message(chat_id, best)

    import asyncio
    asyncio.run(process_update())

    return jsonify({"ok": True})

# =========================
# Локальный запуск (для теста)
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
