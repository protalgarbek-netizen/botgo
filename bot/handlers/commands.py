import os
import psutil
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from bot.database import register_user, get_user, set_api_key, get_user_dir
from bot.utils.server import get_server_status
from bot.config import DATA_DIR


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Регистрация + создание папки пользователя"""
    user = update.effective_user
    await register_user(user.id, user.username or "", user.first_name or "")

    user_dir = os.path.join(DATA_DIR, str(user.id))
    os.makedirs(user_dir, exist_ok=True)

    await update.message.reply_text(
        f"👋 Привет, *{user.first_name}*!\n\n"
        f"Я AI агент с серверными возможностями.\n"
        f"📁 Твоя папка на сервере создана.\n\n"
        f"*Для начала работы с AI:*\n"
        f"`/setkey ВАШ_GEMINI_API_KEY`\n\n"
        f"Получить ключ: aistudio.google.com\n\n"
        f"*Команды без AI (работают всегда):*\n"
        f"/help — список всех команд",
        parse_mode=ParseMode.MARKDOWN
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Все команды бота*\n\n"
        "*🔑 Управление ключом (без AI):*\n"
        "`/setkey КЛЮЧ` — установить API ключ Gemini\n"
        "`/mykey` — статус твоего ключа\n\n"
        "*📁 Файлы (без AI, всегда работает):*\n"
        "`/files` — список твоих файлов\n"
        "`/get имя_файла` — скачать файл\n"
        "`/delete имя_файла` — удалить файл\n"
        "`/run имя_файла.py` — запустить Python скрипт\n\n"
        "*⚙️ Сервер (без AI):*\n"
        "`/status` — статус сервера\n"
        "`/quota` — счётчик AI запросов\n\n"
        "*🤖 AI агент:*\n"
        "Просто напиши любой текст — агент ответит и выполнит задачу.\n"
        "Нужен API ключ Gemini Flash.",
        parse_mode=ParseMode.MARKDOWN
    )


async def setkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установить API ключ. Работает мгновенно, без перезапуска бота."""
    user = update.effective_user
    args = context.args

    if not args:
        await update.message.reply_text(
            "❌ Укажи ключ: `/setkey ВАШ_КЛЮЧ`\n"
            "Получить ключ: aistudio.google.com",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    api_key = args[0].strip()

    # Простая валидация формата ключа Gemini
    if not api_key.startswith("AIza") or len(api_key) < 30:
        await update.message.reply_text(
            "❌ Ключ выглядит неверным.\n"
            "Ключи Gemini начинаются с `AIza...`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    await register_user(user.id, user.username or "", user.first_name or "")
    await set_api_key(user.id, api_key)

    # Удалить сообщение с ключом для безопасности
    try:
        await update.message.delete()
    except Exception:
        pass

    await update.effective_chat.send_message(
        "✅ *API ключ сохранён!*\n\n"
        "Теперь можешь писать мне и я буду использовать твой ключ.\n"
        "_(Сообщение с ключом удалено для безопасности)_",
        parse_mode=ParseMode.MARKDOWN
    )


async def mykey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статус ключа (сам ключ не показываем)"""
    user_data = await get_user(update.effective_user.id)
    if not user_data or not user_data.get("api_key"):
        await update.message.reply_text(
            "🔑 API ключ *не установлен*.\n"
            "Используй `/setkey ВАШ_КЛЮЧ`",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        key = user_data["api_key"]
        masked = key[:6] + "..." + key[-4:]
        await update.message.reply_text(
            f"✅ API ключ установлен: `{masked}`\n"
            f"Запросов сделано: {user_data['request_count']}\n\n"
            f"Чтобы сменить: `/setkey НОВЫЙ_КЛЮЧ`",
            parse_mode=ParseMode.MARKDOWN
        )


async def files_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список файлов пользователя (без AI)"""
    user_dir = await get_user_dir(update.effective_user.id)
    try:
        files = os.listdir(user_dir)
        if not files:
            await update.message.reply_text(
                "📂 Твоя папка пуста.\n"
                "Отправь мне любой файл и я его сохраню."
            )
            return
        lines = []
        total_size = 0
        for f in sorted(files):
            path = os.path.join(user_dir, f)
            size = os.path.getsize(path)
            total_size += size
            lines.append(f"📄 `{f}` — {size:,} bytes")
        text = (
            f"📁 *Твои файлы* ({len(files)} шт):\n\n"
            + "\n".join(lines)
            + f"\n\n💾 Всего: {total_size:,} bytes"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")


async def delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить файл (без AI)"""
    if not context.args:
        await update.message.reply_text("Укажи файл: `/delete имя_файла`", parse_mode=ParseMode.MARKDOWN)
        return
    filename = os.path.basename(context.args[0])
    user_dir = await get_user_dir(update.effective_user.id)
    filepath = os.path.join(user_dir, filename)
    if not os.path.exists(filepath):
        await update.message.reply_text(f"❌ Файл `{filename}` не найден.", parse_mode=ParseMode.MARKDOWN)
        return
    os.remove(filepath)
    await update.message.reply_text(f"✅ Файл `{filename}` удалён.", parse_mode=ParseMode.MARKDOWN)


async def get_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Скачать файл из папки пользователя (без AI)"""
    if not context.args:
        await update.message.reply_text("Укажи файл: `/get имя_файла`", parse_mode=ParseMode.MARKDOWN)
        return
    filename = os.path.basename(context.args[0])
    user_dir = await get_user_dir(update.effective_user.id)
    filepath = os.path.join(user_dir, filename)
    if not os.path.exists(filepath):
        await update.message.reply_text(f"❌ Файл `{filename}` не найден.", parse_mode=ParseMode.MARKDOWN)
        return
    with open(filepath, "rb") as f:
        await update.message.reply_document(document=f, filename=filename)


async def run_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запустить Python скрипт из папки пользователя (без AI)"""
    if not context.args:
        await update.message.reply_text("Укажи файл: `/run script.py`", parse_mode=ParseMode.MARKDOWN)
        return
    filename = os.path.basename(context.args[0])
    if not filename.endswith(".py"):
        await update.message.reply_text("❌ Только `.py` файлы", parse_mode=ParseMode.MARKDOWN)
        return
    user_dir = await get_user_dir(update.effective_user.id)
    filepath = os.path.join(user_dir, filename)
    if not os.path.exists(filepath):
        await update.message.reply_text(f"❌ Файл `{filename}` не найден.", parse_mode=ParseMode.MARKDOWN)
        return

    await update.message.reply_text(f"▶️ Запускаю `{filename}`...", parse_mode=ParseMode.MARKDOWN)

    import asyncio
    proc = await asyncio.create_subprocess_exec(
        "python3", filepath,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=user_dir
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode("utf-8", errors="replace")
        if stderr:
            output += f"\n[stderr]:\n{stderr.decode('utf-8', errors='replace')}"
        output = output[:3500] or "(нет вывода)"
        await update.message.reply_text(
            f"✅ *Результат `{filename}`*:\n```\n{output}\n```",
            parse_mode=ParseMode.MARKDOWN
        )
    except asyncio.TimeoutError:
        proc.kill()
        await update.message.reply_text("⏱️ Таймаут 30 секунд")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статус сервера (без AI)"""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    await update.message.reply_text(
        f"🖥️ *Статус сервера*\n\n"
        f"CPU: {cpu}%\n"
        f"RAM: {ram.used // 1024 // 1024} MB / {ram.total // 1024 // 1024} MB ({ram.percent}%)\n"
        f"Диск: {disk.used // 1024 // 1024 // 1024} GB / {disk.total // 1024 // 1024 // 1024} GB ({disk.percent}%)",
        parse_mode=ParseMode.MARKDOWN
    )


async def quota_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Счётчик запросов к AI"""
    user_data = await get_user(update.effective_user.id)
    count = user_data["request_count"] if user_data else 0
    # Gemini 2.5 Flash free tier: 250 RPD
    remaining_est = max(0, 250 - (count % 250))
    await update.message.reply_text(
        f"📊 *Использование AI*\n\n"
        f"Всего запросов: {count}\n"
        f"Примерный остаток сегодня: ~{remaining_est}/250\n\n"
        f"_Лимит: 10 RPM, 250 RPD (Gemini 2.5 Flash Free)_\n"
        f"_Сброс: каждый день в полночь по PST_",
        parse_mode=ParseMode.MARKDOWN
    )
