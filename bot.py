from flask import Flask, request
import os
from parser import search_kleinanzeigen
import requests
import json

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

users_state = {}
users_data = {}

def send_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(BASE_URL + "sendMessage", json=payload)

def handle_message(chat_id, text):
    state = users_state.get(chat_id)
    try:
        if state is None:
            users_state[chat_id] = "item"
            send_message(chat_id, "Что вы ищете? (например: Ноутбук, Настольный ПК)")
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
            query_string = f"{query_data['item']} {query_data.get('keywords','')}".strip()
            resp = search_kleinanzeigen(query_string, max_items=5)
            method = resp.get("method", "none")
            results = resp.get("results", [])
            if not results:
                send_message(chat_id, f"Метод: {method}\nНичего не найдено 😕")
            else:
                payload = json.dumps(results, ensure_ascii=False, indent=2)
                if len(payload) <= 3500:
                    send_message(chat_id, f"Метод: {method}\nНайденные результаты:\n```{payload}```")
                else:
                    send_message(chat_id, f"Метод: {method}\nНайдено {len(results)} объявлений. Отправляю по одному...")
                    for i, ad in enumerate(results, start=1):
                        txt = f"#{i}\n{ad.get('title')}\n{ad.get('price')}\n{ad.get('link')}\n{ad.get('description')}"
                        send_message(chat_id, txt)
    except Exception as e:
        send_message(chat_id, f"Произошла внутренняя ошибка: {str(e)}")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data or "message" not in data:
        return {"ok": True}
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")
    handle_message(chat_id, text)
    return {"ok": True}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
