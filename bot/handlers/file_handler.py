import os
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from bot.database import get_user_dir, register_user
from bot.config import MAX_FILE_SIZE_MB


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Принять файл от пользователя и сохранить в его папку.
    Работает БЕЗ AI — чистый файловый менеджер.
    """
    user = update.effective_user
    await register_user(user.id, user.username or "", user.first_name or "")

    doc = update.message.document
    if not doc:
        return

    # Проверка размера
    if doc.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        await update.message.reply_text(
            f"❌ Файл слишком большой. Максимум: {MAX_FILE_SIZE_MB} MB"
        )
        return

    user_dir = await get_user_dir(user.id)
    filename = doc.file_name or f"file_{doc.file_id[:8]}"
    filepath = os.path.join(user_dir, filename)

    # Скачать файл
    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(filepath)

    size_kb = doc.file_size / 1024
    await update.message.reply_text(
        f"✅ Файл сохранён!\n\n"
        f"📄 `{filename}`\n"
        f"💾 {size_kb:.1f} KB\n\n"
        f"Команды: `/files` · `/get {filename}` · `/run {filename}`",
        parse_mode=ParseMode.MARKDOWN
    )
