# Leads router (FastAPI + async SQLAlchemy)

## Что реализовано (кратко)

* Сущности: Operator, Lead, Source, OperatorSource (веса), Contact (обращение).
* Асинхронный FastAPI-приложение.
* Алгоритм назначения: **стохастический** — случайный выбор оператора с вероятностью пропорциональной весу `weight / sum(weights)` среди доступных (active + не превышен capacity). Если нет подходящих — создаётся обращение **без** оператора.
* Понимание что обращения принадлежат одному лидy: поиск лида по `external_id`, затем по `phone`, затем по `email`. Если не найден — создаём новый.

## Активная нагрузка (как считаем)

Под нагрузкой по оператору понимается количество обращений (Contact) с `operator_id=...` и `status` в `("open", "in_progress")`. Оператор доступен только если `current_load < capacity`.

## Как запустить

1. **Установить Python 3.10+**

2. **Установить зависимости:**

```bash
pip install -r requirements.txt
```

3. **Применить миграции Alembic:**

```bash
alembic upgrade head
```

4. **Запуск локально:**

```bash
python -m app.main
```

или

```bash
uvicorn app.main:app --reload
```

5. **Запуск через Docker:**

```bash
docker compose up --build
```

После старта контейнера выполнить миграции:

```bash
docker exec -it leads_api alembic upgrade head
```
