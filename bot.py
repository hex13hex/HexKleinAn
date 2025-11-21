import requests
from parser import search_kleinanzeigen  # твой парсер

BOT_TOKEN = "YOUR_BOT_TOKEN"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# Хранение состояний и данных пользователей
users_state = {}
users_data = {}

def send_message(chat_id, text):
    """Отправка сообщения пользователю Telegram"""
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(BASE_URL + "sendMessage", json=payload)
        print(f"[SEND_MESSAGE] chat_id={chat_id}, status={r.status_code}")
    except Exception as e:
        print(f"[ERROR] send_message: {e}")

def handle_message(chat_id, text):
    """Обработка состояния пользователя и логика пошагового опроса"""
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

            # Вызываем парсер Kleinanzeigen
            resp = search_kleinanzeigen(query_string, max_items=5)
            method = resp.get("method", "unknown")
            results = resp.get("results", [])

            # Формируем сообщение пользователю
            if not results:
                send_message(chat_id, f"Метод: {method}\nНичего не найдено 😕")
            else:
                payload_text = "\n\n".join(
                    [f"{i+1}. {r['title']} - {r.get('price','-')} €\n{r['link']}\n{r.get('description','')}"
                     for i, r in enumerate(results)]
                )
                send_message(chat_id, f"Метод: {method}\nНайденные результаты:\n{payload_text}")

    except Exception as e:
        send_message(chat_id, f"Произошла внутренняя ошибка: {str(e)}")
        print(f"[ERROR] handle_message: {e}")

# -------------------------
# Пример цикла polling (для теста, работает на Render Free)
# -------------------------
import time

offset = 0
while True:
    try:
        r = requests.get(BASE_URL + "getUpdates", params={"offset": offset, "timeout": 30}).json()
        for update in r.get("result", []):
            offset = max(offset, update["update_id"] + 1)
            message = update.get("message")
            if not message:
                continue
            chat_id = message["chat"]["id"]
            text = message.get("text", "")
            handle_message(chat_id, text)
    except Exception as e:
        print(f"[ERROR polling]: {e}")
    time.sleep(1)
