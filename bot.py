import os
import time
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

offset = 0

def send_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text}
    requests.post(BASE_URL + "/sendMessage", json=payload)

while True:
    try:
        r = requests.get(BASE_URL + "/getUpdates", params={"offset": offset, "timeout": 30}).json()
        for update in r.get("result", []):
            offset = max(offset, update["update_id"] + 1)
            message = update.get("message")
            if not message:
                continue
            chat_id = message["chat"]["id"]
            text = message.get("text", "")
            if text.startswith("/start"):
                send_message(chat_id, "Привет! Бот работает ✅")
            else:
                send_message(chat_id, f"Вы написали: {text}")
    except Exception as e:
        print("Ошибка polling:", e)
    time.sleep(1)
