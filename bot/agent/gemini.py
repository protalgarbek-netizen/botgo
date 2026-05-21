from google import genai
from google.genai import types
from bot.config import GEMINI_MODEL, DEFAULT_GEMINI_KEY
from bot.agent.tools import get_tools_declaration, execute_tool
import logging

logger = logging.getLogger(__name__)

# Системный промпт агента
SYSTEM_PROMPT = """Ты — мощный AI агент встроенный в Telegram бот.
У тебя есть серверные инструменты — это твои "руки":

- web_search: найти информацию в интернете
- read_file: прочитать файл пользователя с сервера  
- write_file: записать/создать файл в папке пользователя
- list_files: показать список файлов пользователя
- run_python: выполнить Python код на сервере
- run_bash: выполнить bash команду на сервере
- delete_file: удалить файл пользователя

Правила:
1. Используй инструменты активно — это снижает нагрузку на AI
2. Когда можешь выполнить задачу инструментом — делай это, не просто объясняй
3. Отвечай на языке пользователя
4. Будь краток но информативен
5. При ошибках объясняй что пошло не так и предлагай решение
6. Каждый пользователь имеет свою изолированную папку — не выходи за её пределы
"""


async def ask_gemini(
    user_id: int,
    api_key: str,
    message: str,
    history: list = None
) -> str:
    """
    Отправить запрос к Gemini Flash.
    Смена api_key не требует перезапуска — ключ берётся из БД при каждом запросе.
    """
    try:
        client = genai.Client(api_key=api_key)

        # Собрать историю сообщений
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "parts": [{"text": message}]})

        # Инструменты агента
        tools = get_tools_declaration(user_id)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=tools,
                temperature=0.7,
                max_output_tokens=2048,
            )
        )

        # Обработка tool calls (агент хочет использовать инструмент)
        result_text = ""
        tool_calls_made = []

        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                tool_result = await execute_tool(
                    tool_name=fc.name,
                    tool_args=dict(fc.args),
                    user_id=user_id
                )
                tool_calls_made.append({
                    "tool": fc.name,
                    "result": tool_result
                })

        # Если были tool calls — получить финальный ответ
        if tool_calls_made:
            # Добавить результаты инструментов в контекст
            tool_results_text = "\n".join([
                f"[{t['tool']}]: {t['result']}"
                for t in tool_calls_made
            ])
            messages.append({
                "role": "model",
                "parts": [{"text": f"Результаты инструментов:\n{tool_results_text}"}]
            })

            final_response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                    max_output_tokens=2048,
                )
            )
            result_text = final_response.text
        else:
            result_text = response.text

        return result_text or "Нет ответа от AI"

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            return (
                "⚠️ *Квота API исчерпана*\n\n"
                "Лимиты Gemini Flash на сегодня закончились.\n"
                "Что можно сделать:\n"
                "• `/setkey NEW_KEY` — вставить новый API ключ\n"
                "• Подождать до полуночи по тихоокеанскому времени\n"
                "• Команды бота (`/files`, `/run`, `/status` и др.) работают без AI ✅"
            )
        elif "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
            return (
                "❌ *Неверный API ключ*\n\n"
                "Используй `/setkey ВАШ_КЛЮЧ` чтобы обновить ключ.\n"
                "Получить ключ: aistudio.google.com"
            )
        else:
            logger.error(f"Gemini error for user {user_id}: {error_msg}")
            return f"❌ Ошибка AI: {error_msg[:200]}"
