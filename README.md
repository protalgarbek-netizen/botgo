# 🤖 Telegram AI Agent Bot

Полноценный AI агент в Telegram с серверными "руками", файловой системой на пользователя и командами без AI.

**Стек:** Python · `python-telegram-bot` 21.x · Google Gemini 2.5 Flash · Docker · HuggingFace Spaces · SQLite

---

## ✨ Что умеет бот

### Без AI (всегда работает, даже без квоты)
| Команда | Действие |
|---|---|
| `/start` | Регистрация, создание папки пользователя |
| `/setkey <ключ>` | Установить/сменить API ключ Gemini (без перезапуска!) |
| `/mykey` | Показать статус ключа (маскированный) |
| `/files` | Список файлов в твоей папке |
| `/get <имя>` | Скачать файл из твоей папки |
| `/delete <имя>` | Удалить файл из твоей папки |
| `/run <имя.py>` | Запустить Python скрипт из твоей папки |
| `/status` | Статус сервера (RAM, CPU, диск) |
| `/quota` | Счётчик AI запросов |
| `/help` | Список всех команд |
| _отправить файл_ | Автосохранение в твою папку |

### С AI (Gemini 2.5 Flash, нужен ключ)
- 💬 Свободный диалог
- 🔍 `web_search` — поиск в интернете (DuckDuckGo)
- 📄 `read_file` / `write_file` / `list_files` / `delete_file` — управление файлами
- 🐍 `run_python` — выполнение Python кода
- 🖥️ `run_bash` — безопасные bash команды (whitelist)

---

## 📁 Структура

```
telegram-ai-agent/
├── bot/
│   ├── __init__.py
│   ├── main.py              # точка входа + keep-alive HTTP сервер
│   ├── config.py            # настройки и лимиты
│   ├── database.py          # SQLite (aiosqlite)
│   ├── handlers/
│   │   ├── commands.py      # все /команды (без AI)
│   │   ├── ai_handler.py    # обработчик AI диалога
│   │   └── file_handler.py  # загрузка файлов
│   ├── agent/
│   │   ├── gemini.py        # клиент Gemini Flash + tool-calling
│   │   └── tools.py         # серверные инструменты агента
│   └── utils/
│       └── server.py        # статус сервера
├── data/
│   └── users/               # папки пользователей (volume)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Быстрый старт

### 1. Подготовка

1. Получи токен Telegram бота у [@BotFather](https://t.me/BotFather) → `/newbot`
2. Получи API ключ Gemini на [aistudio.google.com](https://aistudio.google.com) → Get API key

### 2. Локальный запуск через Docker

```bash
git clone https://github.com/antifragile022-sys/telegram-ai-agent.git
cd telegram-ai-agent
cp .env.example .env
# Отредактируй .env — вставь свой TELEGRAM_BOT_TOKEN
docker compose up --build
```

### 3. Запуск без Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # вставь TELEGRAM_BOT_TOKEN
python -m bot.main
```

> Важно: в коде пути `/data/users` и `/data/users.db` захардкожены. При локальном запуске без Docker создай симлинк `sudo mkdir -p /data && sudo chown $USER /data` или поправь `bot/config.py`.

---

## 🤗 Деплой на HuggingFace Spaces

1. Создай Space: [huggingface.co/new-space](https://huggingface.co/new-space)
   - **SDK:** Docker
   - **Visibility:** Private (рекомендуется)
2. В Settings → **Repository secrets** добавь:
   - `TELEGRAM_BOT_TOKEN` = токен от BotFather
   - `DEFAULT_GEMINI_KEY` = твой Gemini API ключ
3. Включи Settings → **Persistent storage** (чтобы данные пользователей сохранялись).
4. Залей код:
   ```bash
   git clone https://huggingface.co/spaces/<твой_ник>/<имя_space>
   cd <имя_space>
   cp -r /путь/к/telegram-ai-agent/* .
   git add . && git commit -m "Initial deploy" && git push
   ```
5. Логи → должна появиться строка `Bot started!`. Напиши боту `/start` в Telegram.

### Keep-Alive

HuggingFace засыпает через 48ч без активности. В `bot/main.py` уже встроен HTTP keep-alive сервер на порту `7860`. Настрой ping каждые 25 минут на любом внешнем сервисе (например [cron-job.org](https://cron-job.org)):

```
https://<твой_ник>-<имя_space>.hf.space/
```

---

## ⚠️ Лимиты Gemini 2.5 Flash (Free Tier)

| Параметр | Лимит |
|---|---|
| RPM | 10 |
| RPD | 250 |
| TPM | 250,000 |
| Сброс квоты | Полночь PST |

Когда квоты нет — команды бота продолжают работать. Сменить ключ можно через `/setkey` **без перезапуска**.

---

## 🔐 Безопасность

- API ключи хранятся в SQLite, никогда не показываются целиком (`/mykey` показывает маску).
- Сообщения с `/setkey` автоматически удаляются из чата.
- Каждый пользователь видит только свою папку (`os.path.basename` фильтрует выход за пределы).
- Bash команды агента фильтруются по whitelist:
  `ls, cat, echo, pwd, df, du, free, uname, date, whoami, ps, grep, find, head, tail, wc, sort, uniq, curl`.
- Лимит размера файла: 50 MB. Таймаут запуска Python: 30 сек. Длина вывода: 4000 символов.

---

## 📖 Документация по проекту

См. оригинальный план в `TELEGRAM_AI_AGENT_PROJECT.md` (передан как ТЗ).
