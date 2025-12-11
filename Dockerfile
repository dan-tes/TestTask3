FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

# Копируем проект
COPY . .

# Создаём директорию для SQLite БД
RUN mkdir -p /app/db

# Применяем миграции при старте
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
