import os

import requests
from flask import Flask, request, jsonify
from parser import search_kleinanzeigen

# =========================
# Конфигурация
# =========================
from config import BOT_TOKEN, BACKEND_URL, CHATGPT_URL

app = Flask(__name__)

# =========================
# Простая память для FSM
# =========================
users_state = {}  # chat_id: current_step
users_data = {}   # chat_id: {item, location, max_price, keywords}

# =========================
# Отправка сообщений
# =========================
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

# =========================
# Webhook
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.json
    if "message" not in update:
        return jsonify({"ok": True})

    chat_id = update["message"]["chat"]["id"]
    text = update["message"].get("text", "")

    # -----------------------------
    # /start
    # -----------------------------
    if text == "/start":
        users_state[chat_id] = "item"
        users_data[chat_id] = {}
        send_message(chat_id, "Привет! Что вы хотите найти? (Например: Ноутбук, ПК, RTX 3060)")
        return jsonify({"ok": True})

    # -----------------------------
    # Проверка состояния пользователя
    # -----------------------------
    state = users_state.get(chat_id)
    if not state:
        send_message(chat_id, "Нажмите /start для начала поиска.")
        return jsonify({"ok": True})

    # -----------------------------
    # Пошаговый диалог
    # -----------------------------
    try:
        if state == "item":
            users_data[chat_id]["item"] = text
            users_state[chat_id] = "location"
            send_message(chat_id, "Укажите город и радиус поиска. Пример: 'Бремен +15 км'")
        elif state == "location":
            users_data[chat_id]["location"] = text
            users_state[chat_id] = "max_price"
            send_message(chat_id, "Укажите максимальную цену (например: 200)")
        elif state == "max_price":
            users_data[chat_id]["max_price"] = text
            users_state[chat_id] = "keywords"
            send_message(chat_id, "Укажите дополнительные ключевые слова (например: новая, без повреждений)")
        elif state == "keywords":
            users_data[chat_id]["keywords"] = text
            users_state.pop(chat_id)
            query_json = users_data.pop(chat_id)

            send_message(chat_id, "Ищу объявления… 🔍")

            try:
                # Формируем поисковый запрос
                search_query = (
                    f"{query_json['item']} "
                    f"{query_json['location']} "
                    f"до {query_json['max_price']} евро "
                    f"{query_json['keywords']}"
                )

                # Выполняем парсинг
                results = search_kleinanzeigen(search_query)

                # Отправляем JSON-результаты пользователю
                send_message(
                    chat_id,
                    f"Найденные результаты:\n```\n{results}\n```",
                    parse_mode="Markdown"
                )

            except Exception as e:
                print("Parser error:", e)
                send_message(chat_id, "Произошла ошибка при поиске на Kleinanzeigen.")

    except Exception as e:
        print("Error in processing update:", e)
        send_message(chat_id, "Произошла внутренняя ошибка. Попробуйте снова.")

    return jsonify({"ok": True})

# =========================
# Локальный запуск
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
