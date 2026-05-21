FROM python:3.11-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код бота
COPY bot/ ./bot/

# Папка данных
RUN mkdir -p /data/users

# HuggingFace Spaces: порт 7860 обязателен
EXPOSE 7860

# Запуск
CMD ["python", "-m", "bot.main"]
