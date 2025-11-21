import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

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
    """Приём webhook от Telegram"""
    data = request.get_json()
    print("[WEBHOOK UPDATE]", json.dumps(data, ensure_ascii=False))
    if not data:
        return {"ok": True}

    message = data.get("message") or data.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    # Обработка команды /start
    if text.startswith("/start"):
        send_message(chat_id, "Привет! Я минимальный тестовый бот. ✅")
        return {"ok": True}

    # Ответ на любое другое сообщение
    send_message(chat_id, f"Вы написали: {text}")
    return {"ok": True}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Listening on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
