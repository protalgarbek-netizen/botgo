import aiosqlite
import os
from bot.config import DB_PATH, DATA_DIR


async def init_db():
    """Создать таблицы если не существуют"""
    os.makedirs(DATA_DIR, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                api_key     TEXT DEFAULT NULL,
                api_key_set_at TIMESTAMP DEFAULT NULL,
                registered_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                request_count  INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def register_user(user_id: int, username: str, first_name: str):
    """Зарегистрировать нового пользователя и создать его папку"""
    # Создать папку пользователя на сервере
    user_dir = os.path.join(DATA_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        """, (user_id, username, first_name))
        await db.commit()


async def get_user(user_id: int) -> dict | None:
    """Получить данные пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, username, first_name, api_key, registered_at, request_count FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "username": row[1],
                    "first_name": row[2],
                    "api_key": row[3],
                    "registered_at": row[4],
                    "request_count": row[5]
                }
    return None


async def set_api_key(user_id: int, api_key: str):
    """Установить/сменить API ключ пользователя (без перезапуска бота!)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users 
            SET api_key = ?, api_key_set_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (api_key, user_id))
        await db.commit()


async def increment_request_count(user_id: int):
    """Увеличить счётчик запросов к AI"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET request_count = request_count + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()


async def get_user_dir(user_id: int) -> str:
    """Получить путь к папке пользователя"""
    user_dir = os.path.join(DATA_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir
