import os
import json
import requests
from flask import Flask, request
from parser import search_kleinanzeigen  # твой парсер

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # обязательно установи в Render
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# Хранение состояний пользователей
users_state = {}
users_data = {}

def send_message(chat_id, text):
    """Отправка сообщения пользователю Telegram"""
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(BASE_URL + "sendMessage", json=payload)
        print(f"[SEND_MESSAGE] chat_id={chat_id}, status={r.status_code}")
    except Exception as e:
        print(f"[ERROR] send_message: {e}")

def handle_message(chat_id, text):
    """Обработка состояния пользователя и логика опроса"""
    state = users_state.get(chat_id)
    try:
        if state is None:
            users_state[chat_id] = "item"
            send_message(chat_id, "Привет! Что вы ищете? (например: Ноутбук, Настольный ПК)")
            return

        if state == "item":
            users_data.setdefault(chat_id, {})["item"] = text
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
            query_data = users_data.pop(chat_id)

            send_message(chat_id, "Ищу объявления… 🔍")

            # Формируем поисковый запрос
            query_string = f"{query_data['item']} {query_data.get('keywords','')}".strip()

            # Вызываем парсер
            resp = search_kleinanzeigen(query_string, max_items=5)
            method = resp.get("method", "none")
            results = resp.get("results", [])

            # Формируем сообщение пользователю
            if not results:
                send_message(chat_id, f"Метод: {method}\nНичего не найдено 😕")
            else:
                payload_text = json.dumps(results, ensure_ascii=False, indent=2)
                if len(payload_text) <= 3500:
                    send_message(chat_id, f"Метод: {method}\nНайденные результаты:\n```{payload_text}```")
                else:
                    send_message(chat_id, f"Метод: {method}\nНайдено {len(results)} объявлений. Отправляю по одному...")
                    for i, ad in enumerate(results, start=1):
                        txt = f"#{i}\n*{ad.get('title','Без названия')}*\n💶 Цена: {ad.get('price','-')}\n🔗 {ad.get('link','-')}\n📝 {ad.get('description','-')}"
                        send_message(chat_id, txt)

    except Exception as e:
        send_message(chat_id, f"Произошла внутренняя ошибка: {str(e)}")
        print(f"[ERROR] handle_message: {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook для Telegram"""
    data = request.get_json()
    print("[WEBHOOK UPDATE]", json.dumps(data, ensure_ascii=False))
    if not data:
        return {"ok": True}

    # Получаем сообщение
    message = data.get("message") or data.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    # Обработка команды /start
    if text.startswith("/start"):
        users_state[chat_id] = None
        send_message(chat_id, "Привет! Я бот для поиска на Kleinanzeigen. Что вы ищете?")
        return {"ok": True}

    handle_message(chat_id, text)
    return {"ok": True}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
