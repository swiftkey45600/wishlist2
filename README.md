# Wishlist Service

Сервис вишлистов подарков: пользователь создаёт события (день рождения, свадьба), наполняет их
подарками и делится публичной ссылкой с друзьями. Друзья по ссылке видят список и могут забронировать
подарок, чтобы никто не подарил одно и то же дважды.

Стек: **FastAPI + SQLite** (backend), **React + Vite** (frontend), JWT-авторизация.

---

## Быстрый старт

Нужны только установленные Python и Node.js — всё остальное скрипт сделает сам.

**Windows (PowerShell):**

```powershell
git clone <url-репозитория>
cd wishlist2
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

**Linux / macOS:**

```bash
git clone <url-репозитория>
cd wishlist2
chmod +x run.sh
./run.sh
```

Скрипт поднимет сразу и backend, и frontend. Когда в консоли появится рамка с адресами — открывайте
браузер:

```text
--------------------------------------------------
  Приложение   http://localhost:5173
  API          http://127.0.0.1:8000
  Swagger UI   http://127.0.0.1:8000/docs
  Остановить   Ctrl+C
--------------------------------------------------
```

`Ctrl+C` останавливает оба сервера сразу.

### Что делает скрипт

Первый запуск занимает пару минут (скачиваются зависимости), последующие — несколько секунд.

1. Проверяет, что установлены Python 3.10+ и Node.js 20+, и внятно сообщает, чего не хватает.
2. Создаёт виртуальное окружение `.venv` и ставит в него зависимости из `requirements.txt`.
3. Создаёт файл `.env` со случайным `JWT_SECRET_KEY` — **без него backend не стартует вообще**.
4. Ставит npm-зависимости фронтенда, если папки `node_modules` ещё нет.
5. Запускает оба сервера и по `Ctrl+C` гасит их вместе с дочерними процессами, не оставляя
   занятых портов.

Повторная установка зависимостей пропускается, если `requirements.txt` и `package-lock.json`
не менялись.

### Флаги

| Windows | Linux / macOS | Что делает |
|---|---|---|
| `.\run.ps1 -BackendOnly` | `./run.sh --backend-only` | только API, без фронтенда |
| `.\run.ps1 -FrontendOnly` | `./run.sh --frontend-only` | только фронтенд |
| `.\run.ps1 -SkipInstall` | `./run.sh --skip-install` | не проверять зависимости, сразу запускать |
| — | `./run.sh --help` | справка |

---

## Требования

| Что | Версия | Зачем |
|---|---|---|
| Python | 3.10+ | в коде используется синтаксис `timedelta \| None` |
| Node.js | 20+ | требование Vite 8 |

БД отдельно ставить не нужно: используется SQLite, файл `wishlist.db` создаётся и миграции
применяются автоматически при старте backend.

На Debian/Ubuntu может потребоваться пакет для виртуальных окружений:

```bash
sudo apt install python3-venv
```

---

## Ручной запуск

Если скрипт по какой-то причине не подходит, то же самое руками.

**Backend** (из корня проекта):

```bash
python -m venv .venv

source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

pip install -r requirements.txt

# Обязательно: без JWT_SECRET_KEY приложение упадёт при импорте
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(48))" > .env

uvicorn app.main:app --reload
```

**Frontend** (в отдельном терминале):

```bash
cd frontend
npm install
npm run dev
```

---

## Переменные окружения

Файл `.env` в корне проекта, шаблон — в `.env.example`. В git не попадает.

| Переменная | Обязательна | Описание |
|---|---|---|
| `JWT_SECRET_KEY` | да | ключ подписи JWT. Пустое значение = `RuntimeError` при старте |

Сгенерировать ключ вручную:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## Порты

Порты **зашиты в коде**, а не только в скрипте запуска. Чтобы их поменять, правьте оба места
одновременно, иначе браузер получит ошибку CORS:

| Порт | Где задан |
|---|---|
| `8000` (backend) | `frontend/src/services/api.js` — `baseURL` |
| `5173` (frontend) | `app/main.py` — список разрешённых CORS-origin |

---

## API

Полная интерактивная документация — `http://127.0.0.1:8000/docs`.

| Метод | Путь | Авторизация | Описание |
|---|---|---|---|
| `POST` | `/auth/register` | — | регистрация (`login`, `name`, `password`) |
| `POST` | `/auth/login` | — | вход, возвращает `access_token` |
| `GET` | `/users/me` | JWT | текущий пользователь |
| `PATCH` | `/users/me` | JWT | обновить профиль |
| `GET` | `/users/` · `/users/{id}` | JWT | список / карточка пользователя |
| `DELETE` | `/users/{id}` | JWT | удалить пользователя |
| `GET` `POST` | `/events/` | JWT | список своих событий / создать событие |
| `GET` | `/events/{id}` | JWT | событие по id |
| `PATCH` `DELETE` | `/events/{id}` | JWT | изменить / удалить событие |
| `GET` | `/events/user/{owner_id}` | JWT | события конкретного пользователя |
| `GET` | `/events/public/{public_token}` | — | **публичная страница события для друзей** |
| `GET` | `/events/{event_id}/gifts` | JWT | подарки события |
| `POST` | `/gifts/` | JWT | добавить подарок |
| `GET` `PATCH` `DELETE` | `/gifts/{id}` | JWT | получить / изменить / удалить подарок |
| `PATCH` | `/gifts/{id}/status` | JWT | сменить статус подарка |
| `POST` | `/reservations/` | JWT | забронировать подарок |
| `GET` `DELETE` | `/reservations/{id}` | JWT | получить / снять бронь |
| `POST` | `/images` | — | загрузить картинку (multipart) |
| `GET` `DELETE` | `/images/{id}` | — | получить / удалить картинку |
| `GET` | `/marketplaces` · `/marketplace/{slug}` | — | справочник маркетплейсов |

Токен передаётся заголовком `Authorization: Bearer <access_token>`, время жизни — 90 минут.

---

## Структура проекта

```text
wishlist2/
├── run.ps1                  запуск всего проекта (Windows)
├── run.sh                   запуск всего проекта (Linux / macOS)
├── requirements.txt         зависимости Python
├── .env.example             шаблон переменных окружения
├── wishlist.db              БД SQLite (создаётся автоматически)
│
├── app/                     backend, FastAPI
│   ├── main.py              точка входа, CORS, подключение роутеров
│   ├── config.py            чтение .env
│   ├── database.py          подключение к SQLite, init_db и миграции
│   ├── schema.sql           схема БД
│   ├── models/              dataclass-модели и pydantic-схемы запросов
│   ├── repositories/        SQL-запросы
│   ├── routers/             HTTP-эндпоинты
│   ├── services/            бизнес-логика
│   └── utils/               хеширование паролей (bcrypt), JWT
│
└── frontend/                frontend, React + Vite
    └── src/
        ├── pages/           страницы
        ├── components/      UI-компоненты
        ├── application/     frontend-логика, обработка ошибок, fallback на моки
        ├── repositories/    обращения к API
        └── services/        экземпляр axios и baseURL
```

Подробнее по частям — в [`app/README.md`](app/README.md) и [`frontend/README.md`](frontend/README.md).

---

## Состояние функциональности

Работает:

- регистрация, вход, JWT-авторизация;
- события: создание, редактирование, удаление, публичная ссылка для друзей;
- подарки: создание, редактирование, удаление, смена статуса;
- бронирование подарков;
- загрузка картинок с дедупликацией по SHA-256;
- справочник ссылок на маркетплейсы.

Не доделано:

- **совместный сбор на подарок** (несколько друзей скидываются на дорогой подарок) — задумывался
  как killer feature, но пока это заготовка: `ContributionRepository` и
  `ContributionService.add_contribution` бросают `NotImplementedError`, HTTP-роутера для взносов
  нет. У модели `Gift` есть поле `contribution_total`, которое всегда остаётся `0`;
- тесты отсутствуют.

Планы по задачам — в [`MVP_TODO.md`](MVP_TODO.md).

---

## Возможные проблемы

**`run.ps1 не может быть загружен, так как выполнение сценариев отключено`**

Политика запуска скриптов в Windows. Либо запускайте с обходом:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

либо разрешите локальные скрипты один раз:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**`RuntimeError: JWT_SECRET_KEY must be set in the environment or .env`**

Нет `.env` или в нём пустой ключ. Удалите `.env` и запустите скрипт заново — он сгенерирует ключ.

**`Form data requires "python-multipart" to be installed`**

Зависимости поставлены из устаревшего `requirements.txt`. Обновите репозиторий и переустановите:

```bash
pip install -r requirements.txt
```

**`[Errno 98] Address already in use` / `порт уже занят`**

С прошлого раза остался процесс на 8000 или 5173. Найти и снять:

```powershell
# Windows
Get-NetTCPConnection -LocalPort 8000 -State Listen | ForEach-Object { taskkill /T /F /PID $_.OwningProcess }
```

```bash
# Linux / macOS
lsof -ti:8000 | xargs kill
```

**Фронтенд показывает данные, которых нет в БД**

Слой `application/` при недоступном backend подставляет моки из `src/mocks/`. Проверьте, что
backend поднят и отвечает на `http://127.0.0.1:8000/docs`.

**`error: externally-managed-environment` при ручной установке**

Пакеты ставятся в системный Python вместо виртуального окружения. Убедитесь, что `.venv`
активировано, или просто используйте скрипт запуска.
