# Backend

FastAPI-сервер для Wishlist Service.

## Требования

- Python 3.10+

## Установка и запуск

```bash
# Перейти в корень проекта (не в папку backend)
cd ..

# Создать виртуальное окружение
python -m venv venv

# Активировать виртуальное окружение
source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows

# Установить зависимости
pip install -r requirements.txt

# Запустить сервер
uvicorn app.main:app --reload
```

## Доступные адреса

| Адрес | Описание |
|-------|----------|
| `http://localhost:8000` | REST API |
| `http://localhost:8000/docs` | Swagger UI (интерактивная документация) |
| `http://localhost:8000/redoc` | ReDoc документация |

## Структура

```
app/
├── main.py              # точка входа, FastAPI-приложение
├── models/              # dataclass-модели сущностей
├── repositories/        # слой работы с данными
├── routers/             # маршруты API
└── services/            # бизнес-логика
requirements.txt         # зависимости Python
```
