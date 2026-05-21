from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction
from bot.database import get_user, register_user, increment_request_count
from bot.agent.gemini import ask_gemini

# Простая история диалога в памяти (сбрасывается при перезапуске)
# Для персистентности можно хранить в SQLite
conversation_history: dict[int, list] = {}
MAX_HISTORY = 10  # последних сообщений


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений → AI агент"""
    user = update.effective_user
    await register_user(user.id, user.username or "", user.first_name or "")

    user_data = await get_user(user.id)

    # Проверка наличия API ключа
    if not user_data or not user_data.get("api_key"):
        await update.message.reply_text(
            "🔑 *Нет API ключа*\n\n"
            "Чтобы использовать AI, установи ключ Gemini:\n"
            "`/setkey ВАШ_КЛЮЧ`\n\n"
            "Получить бесплатно: aistudio.google.com\n\n"
            "Команды бота работают без ключа ✅",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Показать "печатает..."
    await update.effective_chat.send_action(ChatAction.TYPING)

    # История диалога
    user_id = user.id
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    history = conversation_history[user_id]

    # Запрос к Gemini Flash
    response = await ask_gemini(
        user_id=user_id,
        api_key=user_data["api_key"],
        message=update.message.text,
        history=history[-MAX_HISTORY:]
    )

    # Обновить историю
    conversation_history[user_id].append(
        {"role": "user", "parts": [{"text": update.message.text}]}
    )
    conversation_history[user_id].append(
        {"role": "model", "parts": [{"text": response}]}
    )
    # Обрезать историю
    if len(conversation_history[user_id]) > MAX_HISTORY * 2:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY * 2:]

    await increment_request_count(user_id)

    # Отправить ответ (с обработкой длинных сообщений)
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            await update.message.reply_text(response[i:i+4000])
    else:
        try:
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text(response)
