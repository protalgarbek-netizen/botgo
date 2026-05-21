import asyncio
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ConversationHandler
)
from bot.config import TELEGRAM_BOT_TOKEN
from bot.database import init_db
from bot.handlers.commands import (
    start, help_cmd, setkey, mykey, files_cmd,
    delete_cmd, get_cmd, run_cmd, status_cmd, quota_cmd
)
from bot.handlers.file_handler import handle_document
from bot.handlers.ai_handler import handle_message

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class PingHandler(BaseHTTPRequestHandler):
    """HTTP keep-alive endpoint для HuggingFace Spaces."""

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        # Отключить логи пингов
        pass


def run_ping_server():
    server = HTTPServer(("0.0.0.0", 7860), PingHandler)
    server.serve_forever()


async def main():
    # Инициализация БД
    await init_db()
    logger.info("Database initialized")

    # Создание приложения
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # === Команды (работают БЕЗ AI, всегда) ===
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("setkey", setkey))
    app.add_handler(CommandHandler("mykey", mykey))
    app.add_handler(CommandHandler("files", files_cmd))
    app.add_handler(CommandHandler("delete", delete_cmd))
    app.add_handler(CommandHandler("get", get_cmd))
    app.add_handler(CommandHandler("run", run_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("quota", quota_cmd))

    # === Загрузка файлов (без AI) ===
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # === AI диалог (только текст, нужен ключ) ===
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запустить HTTP сервер keep-alive в отдельном потоке
    ping_thread = threading.Thread(target=run_ping_server, daemon=True)
    ping_thread.start()

    logger.info("Bot started!")
    await app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
