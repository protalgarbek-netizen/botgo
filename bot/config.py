import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Дефолтный Gemini ключ (для теста, пользователи ставят свои)
DEFAULT_GEMINI_KEY = os.getenv("DEFAULT_GEMINI_KEY", "")

# Пути
DATA_DIR = "/data/users"
DB_PATH = "/data/users.db"

# Модель — ТОЛЬКО Flash
GEMINI_MODEL = "gemini-2.5-flash"

# Лимиты безопасности
MAX_FILE_SIZE_MB = 50
MAX_CODE_TIMEOUT_SEC = 30
MAX_OUTPUT_LENGTH = 4000
