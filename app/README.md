# Backend

FastAPI-сервер для Wishlist Service.

> Чтобы поднять весь проект одной командой (backend + frontend), используйте скрипт из корня:
> `.\run.ps1` на Windows или `./run.sh` на Linux/macOS — см. [корневой README](../README.md).
> Ниже — запуск только backend.

## Требования

- Python 3.10+ (в коде используется синтаксис `timedelta | None`)

## Установка и запуск

Все команды выполняются **из корня проекта**, а не из папки `app`.

```bash
# Создать виртуальное окружение
python -m venv .venv

# Активировать виртуальное окружение
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows

# Установить зависимости
pip install -r requirements.txt

# Создать .env с ключом подписи JWT — без него сервер не стартует
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(48))" > .env

# Запустить сервер
uvicorn app.main:app --reload
```

Либо то же самое одной командой: `./run.sh --backend-only` (`.\run.ps1 -BackendOnly` на Windows).

## Переменные окружения

| Переменная | Обязательна | Описание |
|---|---|---|
| `JWT_SECRET_KEY` | да | ключ подписи JWT. Пустое значение — `RuntimeError` при импорте приложения |

Файл `.env` лежит в корне проекта, шаблон — `.env.example`.

## База данных

SQLite, файл `wishlist.db` в корне проекта. Отдельная установка не нужна: при старте
`init_db()` применяет `app/schema.sql` и досоздаёт недостающие колонки. Чтобы начать с чистой
БД, достаточно удалить `wishlist.db` и перезапустить сервер.

## Доступные адреса

| Адрес | Описание |
|-------|----------|
| `http://127.0.0.1:8000` | REST API |
| `http://127.0.0.1:8000/docs` | Swagger UI (интерактивная документация) |
| `http://127.0.0.1:8000/redoc` | ReDoc документация |

Список эндпоинтов — в [корневом README](../README.md#api).

Порт `8000` продублирован в `frontend/src/services/api.js`, а разрешённый origin фронтенда
`5173` — в `app/main.py`. При смене портов правьте оба файла, иначе браузер получит ошибку CORS.

## Структура

```text
app/
├── main.py              точка входа, CORS, подключение роутеров
├── config.py            чтение .env
├── database.py          подключение к SQLite, init_db и миграции
├── schema.sql           схема БД
├── models/              dataclass-модели и pydantic-схемы запросов
├── repositories/        SQL-запросы
├── routers/             HTTP-эндпоинты
├── services/            бизнес-логика
└── utils/               хеширование паролей (bcrypt), выпуск и проверка JWT
```

## Зависимости

| Пакет | Зачем |
|---|---|
| `fastapi` | веб-фреймворк |
| `uvicorn[standard]` | ASGI-сервер |
| `python-jose[cryptography]` | выпуск и проверка JWT |
| `python-multipart` | разбор multipart-запросов для `POST /images` |
| `bcrypt` | хеширование паролей |
| `python-dotenv` | чтение `.env` |

## Не реализовано

`ContributionRepository` и `ContributionService.add_contribution` — заготовки, бросающие
`NotImplementedError`; HTTP-роутера для взносов нет, поле `Gift.contribution_total` всегда `0`.
Совместный сбор на подарок пока не работает.
