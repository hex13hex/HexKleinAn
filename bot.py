import os
import requests
import asyncio
import nest_asyncio
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

# =========================
# Настройка
# =========================
from config import BOT_TOKEN, BACKEND_URL, CHATGPT_URL

nest_asyncio.apply()  # разрешаем вложенные event loops
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = Flask(__name__)

# =========================
# FSM для пошагового диалога
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
    print("Received update:", update)  # логируем все входящие обновления

    if "message" not in update:
        return jsonify({"ok": True})

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")
    user_id = chat_id  # используем chat_id как идентификатор FSM

    async def process_update():
        try:
            ctx = FSMContext(storage=dp.storage, chat=user_id, user=user_id, bot=bot)
            state = await ctx.storage.get_state(chat=user_id, user=user_id)

            if text == "/start":
                await ctx.set_state(SearchState.item)
                send_message(chat_id, "Что вы хотите найти? (Например: Ноутбук, ПК, RTX 3060)")
                return

            if state is None:
                send_message(chat_id, "Нажмите /start для начала поиска.")
                return

            try:
                data = await ctx.get_data() or {}
            except Exception as e:
                print("FSM get_data error:", e)
                data = {}

            # -----------------------------
            # FSM переходы
            # -----------------------------
            if state == SearchState.item.state:
                await ctx.update_data(item=text)
                await ctx.set_state(SearchState.location)
                send_message(chat_id, "Укажите город и радиус поиска. Пример: 'Бремен +15 км'")
            elif state == SearchState.location.state:
                await ctx.update_data(location=text)
                await ctx.set_state(SearchState.max_price)
                send_message(chat_id, "Укажите максимальную цену (например: 200)")
            elif state == SearchState.max_price.state:
                await ctx.update_data(max_price=text)
                await ctx.set_state(SearchState.keywords)
                send_message(chat_id, "Укажите дополнительные ключевые слова (например: новая, без повреждений)")
            elif state == SearchState.keywords.state:
                await ctx.update_data(keywords=text)
                await ctx.clear()
                query_json = {
                    "item": data.get("item"),
                    "location": data.get("location"),
                    "max_price": data.get("max_price"),
                    "keywords": text
                }
                send_message(chat_id, "Ищу объявления… 🔍")

                # -----------------------------
                # Отправка на backend
                # -----------------------------
                try:
                    resp = requests.post(BACKEND_URL, json=query_json)
                    ads = resp.json().get("ads", [])
                except Exception as e:
                    send_message(chat_id, f"Ошибка соединения с сервером: {e}")
                    return

                if not ads:
                    send_message(chat_id, "Ничего не найдено 😕")
                    return

                # -----------------------------
                # Отправка в ChatGPT
                # -----------------------------
                try:
                    gpt_resp = requests.post(CHATGPT_URL, json={"ads": ads})
                    best = gpt_resp.json().get("best_option", "Ошибка анализа.")
                except Exception as e:
                    best = f"Ошибка отправки в ChatGPT: {e}"

                send_message(chat_id, best)

        except Exception as e:
            print("Error in process_update:", e)
            send_message(chat_id, "Произошла внутренняя ошибка. Попробуйте снова.")

    asyncio.run(process_update())
    return jsonify({"ok": True})

# =========================
# Локальный запуск для теста
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
