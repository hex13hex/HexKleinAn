import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

def send_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(BASE_URL + "sendMessage", json=payload)
        print(f"[SEND_MESSAGE] chat_id={chat_id}, status={r.status_code}")
    except Exception as e:
        print(f"[ERROR] send_message: {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        print("[WEBHOOK UPDATE]", json.dumps(data, ensure_ascii=False))
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        send_message(chat_id, f"Получено сообщение: {text}")
    except Exception as e:
        print(f"[ERROR webhook]: {e}")
    return {"ok": True}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Listening on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
