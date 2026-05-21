import os
import asyncio
import subprocess
import aiohttp
from bot.config import DATA_DIR, MAX_CODE_TIMEOUT_SEC, MAX_OUTPUT_LENGTH


def get_tools_declaration(user_id: int) -> list:
    """Объявления инструментов для Gemini"""
    return [
        {
            "function_declarations": [
                {
                    "name": "web_search",
                    "description": "Поиск информации в интернете",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Поисковый запрос"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "read_file",
                    "description": "Прочитать содержимое файла из папки пользователя",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Имя файла"}
                        },
                        "required": ["filename"]
                    }
                },
                {
                    "name": "write_file",
                    "description": "Создать или записать файл в папку пользователя",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Имя файла"},
                            "content": {"type": "string", "description": "Содержимое"}
                        },
                        "required": ["filename", "content"]
                    }
                },
                {
                    "name": "list_files",
                    "description": "Показать список файлов пользователя",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "run_python",
                    "description": "Выполнить Python код на сервере",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Python код"},
                            "filename": {
                                "type": "string",
                                "description": "Имя файла в папке пользователя (опционально)"
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "run_bash",
                    "description": "Выполнить безопасную bash команду (только чтение/утилиты)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "bash команда"}
                        },
                        "required": ["command"]
                    }
                },
                {
                    "name": "delete_file",
                    "description": "Удалить файл из папки пользователя",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Имя файла"}
                        },
                        "required": ["filename"]
                    }
                }
            ]
        }
    ]


async def execute_tool(tool_name: str, tool_args: dict, user_id: int) -> str:
    """Выполнить инструмент и вернуть результат"""
    user_dir = os.path.join(DATA_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    if tool_name == "web_search":
        return await _web_search(tool_args.get("query", ""))

    elif tool_name == "read_file":
        return _read_file(user_dir, tool_args.get("filename", ""))

    elif tool_name == "write_file":
        return _write_file(user_dir, tool_args.get("filename", ""), tool_args.get("content", ""))

    elif tool_name == "list_files":
        return _list_files(user_dir)

    elif tool_name == "run_python":
        return await _run_python(
            user_dir,
            tool_args.get("code", ""),
            tool_args.get("filename")
        )

    elif tool_name == "run_bash":
        return await _run_bash(user_dir, tool_args.get("command", ""))

    elif tool_name == "delete_file":
        return _delete_file(user_dir, tool_args.get("filename", ""))

    return f"Неизвестный инструмент: {tool_name}"


async def _web_search(query: str) -> str:
    """Поиск через DuckDuckGo (бесплатно, без API ключа)"""
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json(content_type=None)
                results = []
                if data.get("AbstractText"):
                    results.append(data["AbstractText"])
                for r in data.get("RelatedTopics", [])[:3]:
                    if isinstance(r, dict) and r.get("Text"):
                        results.append(r["Text"])
                return "\n".join(results) if results else "Результаты не найдены"
    except Exception as e:
        return f"Ошибка поиска: {str(e)}"


def _read_file(user_dir: str, filename: str) -> str:
    """Прочитать файл из папки пользователя"""
    # Безопасность: запрет выхода за пределы папки
    filename = os.path.basename(filename)
    filepath = os.path.join(user_dir, filename)
    if not os.path.exists(filepath):
        return f"Файл '{filename}' не найден"
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(MAX_OUTPUT_LENGTH)
        return content
    except Exception as e:
        return f"Ошибка чтения: {str(e)}"


def _write_file(user_dir: str, filename: str, content: str) -> str:
    """Записать файл в папку пользователя"""
    filename = os.path.basename(filename)
    filepath = os.path.join(user_dir, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Файл '{filename}' сохранён ({len(content)} символов)"
    except Exception as e:
        return f"Ошибка записи: {str(e)}"


def _list_files(user_dir: str) -> str:
    """Список файлов пользователя"""
    try:
        files = os.listdir(user_dir)
        if not files:
            return "Папка пуста"
        result = []
        for f in sorted(files):
            path = os.path.join(user_dir, f)
            size = os.path.getsize(path)
            result.append(f"📄 {f} ({size} bytes)")
        return "\n".join(result)
    except Exception as e:
        return f"Ошибка: {str(e)}"


async def _run_python(user_dir: str, code: str, filename: str = None) -> str:
    """Запустить Python код в изолированной папке пользователя"""
    try:
        # Если передано имя файла — запустить файл
        if filename:
            filename = os.path.basename(filename)
            script_path = os.path.join(user_dir, filename)
            if not os.path.exists(script_path):
                return f"Файл '{filename}' не найден"
            cmd = ["python3", script_path]
        else:
            # Запустить код напрямую
            cmd = ["python3", "-c", code]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=user_dir
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=MAX_CODE_TIMEOUT_SEC
            )
        except asyncio.TimeoutError:
            proc.kill()
            return f"⏱️ Таймаут ({MAX_CODE_TIMEOUT_SEC}с)"

        output = ""
        if stdout:
            output += stdout.decode("utf-8", errors="replace")
        if stderr:
            output += f"\n[stderr]: {stderr.decode('utf-8', errors='replace')}"
        return output[:MAX_OUTPUT_LENGTH] if output else "(нет вывода)"
    except Exception as e:
        return f"Ошибка запуска: {str(e)}"


# Разрешённые команды bash (белый список для безопасности)
SAFE_BASH_PREFIXES = [
    "ls", "cat", "echo", "pwd", "df", "du", "free",
    "uname", "date", "whoami", "ps", "grep", "find",
    "head", "tail", "wc", "sort", "uniq", "curl"
]


async def _run_bash(user_dir: str, command: str) -> str:
    """Выполнить bash команду (только безопасные команды)"""
    cmd_lower = command.strip().lower()
    is_safe = any(cmd_lower.startswith(prefix) for prefix in SAFE_BASH_PREFIXES)

    if not is_safe:
        return (
            "⛔ Команда заблокирована по соображениям безопасности.\n"
            f"Разрешены: {', '.join(SAFE_BASH_PREFIXES)}"
        )
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=user_dir
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=15
        )
        output = stdout.decode("utf-8", errors="replace")
        if stderr:
            output += f"\n[stderr]: {stderr.decode('utf-8', errors='replace')}"
        return output[:MAX_OUTPUT_LENGTH] or "(нет вывода)"
    except asyncio.TimeoutError:
        return "⏱️ Таймаут (15с)"
    except Exception as e:
        return f"Ошибка: {str(e)}"


def _delete_file(user_dir: str, filename: str) -> str:
    """Удалить файл из папки пользователя"""
    filename = os.path.basename(filename)
    filepath = os.path.join(user_dir, filename)
    if not os.path.exists(filepath):
        return f"Файл '{filename}' не найден"
    try:
        os.remove(filepath)
        return f"✅ Файл '{filename}' удалён"
    except Exception as e:
        return f"Ошибка удаления: {str(e)}"
