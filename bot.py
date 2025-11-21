import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# Получаем токен из переменных окружения Render
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

def send_message(chat_id, text):
    """Отправка сообщения пользователю Telegram"""
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(BASE_URL + "sendMessage", json=payload)
        print(f"[SEND_MESSAGE] chat_id={chat_id}, status={r.status_code}")
    except Exception as e:
        print(f"[ERROR] send_message: {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    """Обработка POST-запроса от Telegram"""
    try:
        # Telegram шлёт JSON
        data = request.get_json(force=True)
        print("[WEBHOOK UPDATE]", json.dumps(data, ensure_ascii=False))

        message = data.get("message")
        if not message:
            return {"ok": True}

        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text.startswith("/start"):
            send_message(chat_id, "Привет! Бот работает ✅")
        else:
            send_message(chat_id, f"Вы написали: {text}")

    except Exception as e:
        print(f"[ERROR webhook]: {e}")
    return {"ok": True}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Listening on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
