import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# URL к твоему backend для парсинга Kleinanzeigen
BACKEND_URL = os.getenv("BACKEND_URL")

# URL для ChatGPT endpoint (где я выбираю лучший вариант)
CHATGPT_URL = os.getenv("CHATGPT_URL")