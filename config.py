import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BACKEND_URL = os.getenv("https://hexkleinan.onrender.com")
CHATGPT_URL = os.getenv("CHATGPT_URL")
