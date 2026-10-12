# MVP TODO — Wishlist2

Актуально после коммита `10d8dc7`. Два раздела: **Backend** и **Frontend**.
Каждый разбит на **Баги** и **Нереализованные фичи**, от простого к сложному.

---

## Что уже исправлено ✅

- `get_current_user` — теперь ищет пользователя в SQLite ✅
- `UserRepository` и `EventRepository` — перенесены на SQLite, данные больше не теряются ✅
- `owner_id` при создании события — теперь берётся из токена ✅
- Синглтон-проблема репозиториев — решена переходом на SQLite ✅
- `ReservationRepository` + `ReservationService` + `reservation_router` — реализованы ✅
- `marketplace_router` — реализован ✅
- `app/routers/__init__.py` — создан ✅

---

## BACKEND — Баги

---

### B1. Регистрация падает с ошибкой 72 bytes — несовместимость passlib + bcrypt

**Файл:** `app/utils/security.py`, `requirements.txt`
**Сложность:** минуты

`passlib 1.7.4` (последний релиз 2020 г.) + `bcrypt >= 4.0` — несовместимы.
В bcrypt 4.0 убрали `__version__`, passlib не может определить версию и падает
с `"password cannot be longer than 72 bytes"` на **любом** пароле, даже из 3 символов.

**Вариант 1 — пин версии:**
```
# requirements.txt — добавить:
bcrypt<4.0.0
```

**Вариант 2 — убрать passlib, использовать bcrypt напрямую (рекомендуется):**
```python
# app/utils/security.py — переписать полностью:
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
```

---

### B2. `gift_service.py` — `HTTPException` используется без импорта

**Файл:** `app/services/gift_service.py:1`
**Сложность:** минуты

```python
# Добавить в начало файла:
from fastapi import HTTPException
```

---

### B3. `user_repository.create_user` — пароль хешируется дважды в возвращаемом объекте

**Файл:** `app/repositories/user_repository.py:9-20`
**Сложность:** минуты

В БД записывается правильный хеш. Но в возвращаемый `User` объект кладётся
`hash_password(user.password)` — то есть хеш хеша. Это не ломает регистрацию
(auth_router использует только `user.login` и `user.id`), но создаёт неконсистентный объект.

```python
# СЕЙЧАС:
return User(
    id=cursor.lastrowid,
    name=user.name,
    login=user.login,
    password=hash_password(user.password)  # повторное хеширование!
)

# ИСПРАВЛЕНИЕ — вернуть пустую строку или оригинальный хеш из cursor:
return User(
    id=cursor.lastrowid,
    name=user.name,
    login=user.login,
    password=""   # пароль не нужен в возвращаемом объекте
)
```

---

### B4. `reservation_service` — бронирование не меняет статус подарка

**Файлы:** `app/services/reservation_service.py`, `app/routers/gift_router.py`
**Сложность:** ~15 минут

`POST /reservations/` создаёт запись в таблице `reservations`, но статус подарка в таблице
`gifts` остаётся `available`. Аналогично `DELETE /reservations/{id}` не возвращает статус
обратно в `available`. Таблица резерваций и поле `status` в gifts живут независимо.

```python
# app/services/reservation_service.py — добавить обновление статуса:
from app.repositories.gift_repository import GiftRepository

class ReservationService:
    def __init__(self, reservation_repository, gift_repository: GiftRepository):
        self.reservation_repository = reservation_repository
        self.gift_repository = gift_repository

    def reserve_gift(self, gift_id, reserver_name=None, is_anonymous=False):
        existing = self.reservation_repository.get_reservation_by_gift(gift_id)
        if existing:
            raise HTTPException(status_code=409, detail="Gift is already reserved")

        reservation = Reservation(gift_id=gift_id, is_anonymous=is_anonymous, reserver_name=reserver_name)
        result = self.reservation_repository.reserve_gift(reservation)
        self.gift_repository.update_gift_status(gift_id, "reserved")  # ← добавить
        return result

    def unreserve_gift(self, reservation_id):
        reservation = self.reservation_repository.get_reservation_by_id(reservation_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        self.reservation_repository.unreserve_by_id(reservation_id)
        self.gift_repository.update_gift_status(reservation.gift_id, "available")  # ← добавить
```

```python
# reservation_router.py — передать gift_repo в сервис:
from app.repositories.gift_repository import GiftRepository

gift_repo = GiftRepository()
reservation_service = ReservationService(reservation_repo, gift_repo)
```

---

## BACKEND — Нереализованные фичи

---

### B5. Редактирование подарка — эндпоинт отсутствует

**Файлы:** `app/routers/gift_router.py`, `app/repositories/gift_repository.py`, `app/services/gift_service.py`
**Сложность:** ~30 минут

Нет `PATCH /gifts/{gift_id}` для обновления полей (title, price, description, marketplace_url, picture_url).
Есть только `PATCH /gifts/{gift_id}/status` для смены статуса.

```python
# 1. app/repositories/gift_repository.py — добавить метод:
def update_gift(self, gift_id: int, data: dict) -> Gift | None:
    fields = {k: v for k, v in data.items() if v is not None}
    if not fields:
        return self.get_gift_by_id(gift_id)
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    with get_connection() as conn:
        conn.execute(
            f"UPDATE gifts SET {set_clause} WHERE id = ?",
            (*fields.values(), gift_id)
        )
    return self.get_gift_by_id(gift_id)

# 2. app/services/gift_service.py — добавить метод:
def update_gift(self, gift_id: int, data: dict) -> Gift:
    gift = self.gift_repository.update_gift(gift_id, data)
    if gift is None:
        raise HTTPException(status_code=404, detail="Gift not found")
    return gift

# 3. app/routers/gift_router.py — добавить эндпоинт и модель запроса:
from pydantic import BaseModel
from typing import Optional

class GiftUpdateRequest(BaseModel):
    title: Optional[str] = None
    price: Optional[int] = None
    description: Optional[str] = None
    picture_url: Optional[str] = None
    marketplace_url: Optional[str] = None

@router.patch("/gifts/{gift_id}")
def update_gift(gift_id: int, data: GiftUpdateRequest):
    return gift_service.update_gift(gift_id, data.model_dump(exclude_none=True))
```

---

### B6. Публичная ссылка — `public_token` не генерируется и нет эндпоинта

**Файлы:** `app/services/event_service.py`, `app/routers/event_router.py`
**Сложность:** ~30 минут

`EventRepository.get_event_by_public_token()` и `EventService.get_event_by_token()` уже есть.
Но токен никогда не генерируется при создании события, и нет публичного эндпоинта.

```python
# 1. app/services/event_service.py — генерировать токен:
import secrets

def create_event(self, owner_id, title, description=None, event_date=None, place=None):
    new_event = Event(
        owner_id=owner_id,
        title=title,
        description=description,
        event_date=event_date,
        place=place,
        public_token=secrets.token_urlsafe(16)  # ← добавить
    )
    return self.event_repository.create_event(new_event)

# 2. app/routers/event_router.py — добавить публичный эндпоинт (без авторизации):
from app.repositories.gift_repository import GiftRepository
from app.services.gift_service import GiftService
from app.repositories.contribution_repository import ContributionRepository

gift_repository = GiftRepository()
contribution_repository = ContributionRepository()
gift_service_pub = GiftService(gift_repository, contribution_repository)

@router.get("/public/{token}")
async def get_event_by_token(token: str):
    event = event_service.get_event_by_token(token)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    gifts = gift_service_pub.get_gifts_by_event(event.id)
    return {"event": event, "gifts": gifts}
```

---

## FRONTEND — Баги

---

### F1. Выход из аккаунта не очищает токен в localStorage

**Файл:** `frontend/src/components/Profile/LogoutModal/LogoutModal.jsx:10`
**Сложность:** минуты

```javascript
// ИСПРАВЛЕНИЕ:
function handleLogout() {
    localStorage.removeItem("accessToken")
    localStorage.removeItem("user")
    navigate("/auth")
}
```

---

### F2. Sidebar показывает захардкоженное "John Doe"

**Файл:** `frontend/src/components/Sidebar/Sidebar.jsx:40`
**Сложность:** минуты

```jsx
function Sidebar() {
    const user = JSON.parse(localStorage.getItem("user") || "null")
    return (
        // ...
        <div className="sidebar-profile">
            {user ? user.name : "Гость"}
        </div>
    )
}
```

---

### F3. Нет защиты маршрутов — `/profile`, `/`, `/events/:id` открыты без авторизации

**Файл:** `frontend/src/App.jsx`
**Сложность:** ~15 минут

Все маршруты открыты без токена. При 401 от бэкенда страница показывает ошибку вместо
редиректа на `/auth`.

```jsx
// frontend/src/App.jsx
function ProtectedRoute({ children }) {
    const token = localStorage.getItem("accessToken")
    return token ? children : <Navigate to="/auth" replace />
}

// В Routes:
<Route path="/auth" element={<AuthPage />} />
<Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
<Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
<Route path="/events/:id" element={<ProtectedRoute><EventPage /></ProtectedRoute>} />
```

---

## FRONTEND — Нереализованные фичи

---

### F4. Удаление подарка — обработчик не подключён в `GiftList`

**Файл:** `frontend/src/components/Gifts/GiftList/GiftList.jsx`
**Сложность:** минуты

`GiftCard` принимает `onDelete` пропом и кнопка в UI есть. Но `GiftList` не импортирует
`deleteGift` и не передаёт обработчик в `GiftCard`.

```jsx
// 1. Добавить импорт в GiftList.jsx:
import { getGiftsByEvent, createGift, updateGiftStatus, deleteGift } from "../../../application/giftApplication"

// 2. Добавить функцию:
async function handleDeleteGift(giftId) {
    await deleteGift(giftId)
    setGifts(prev => prev.filter(g => g.id !== giftId))
}

// 3. Передать в GiftCard:
<GiftCard
    key={gift.id}
    gift={gift}
    onToggleStatus={handleToggleStatus}
    onDelete={handleDeleteGift}   // ← добавить
/>
```

---

### F5. Поле `marketplace_url` отсутствует в форме создания подарка

**Файл:** `frontend/src/components/Gifts/GiftList/GiftList.jsx`
**Сложность:** минуты

Бэкенд принимает и хранит поле, но формы нет — данные уходят как `undefined`.

```jsx
// 1. Добавить state:
const [marketplaceUrl, setMarketplaceUrl] = useState("")

// 2. Добавить поле в форму после "Ссылка на изображение":
<label>
    Ссылка на маркетплейс
    <input
        value={marketplaceUrl}
        onChange={e => setMarketplaceUrl(e.target.value)}
        placeholder="https://..."
    />
</label>

// 3. Включить в вызов createGift:
const createdGift = await createGift({
    event_id: Number(eventId),
    title: title.trim(),
    price: parsedPrice,
    description: description.trim() || undefined,
    picture_url: imageUrl.trim() || undefined,
    marketplace_url: marketplaceUrl.trim() || undefined,  // ← добавить
    status: "available"
})

// 4. Сбросить после отправки:
setMarketplaceUrl("")
```

---

### F6. Ссылка на маркетплейс не отображается в карточке подарка

**Файл:** `frontend/src/components/Gifts/GiftCard/GiftCard.jsx`
**Сложность:** минуты

Данные приходят с бэкенда в объекте `gift`, но компонент их не рендерит.

```jsx
// Добавить в GiftCard под h3:
{gift.marketplace_url && (
    <a
        href={gift.marketplace_url}
        target="_blank"
        rel="noopener noreferrer"
        className="marketplace-link"
    >
        Посмотреть на маркетплейсе →
    </a>
)}
```

---

### F7. Бронирование подарков — фронт не использует `/reservations/` API

**Файл:** `frontend/src/components/Gifts/GiftList/GiftList.jsx`
**Сложность:** ~30 минут (после B4)

Сейчас `handleToggleStatus` вызывает `PATCH /gifts/{id}/status` — меняет статус напрямую,
не создаёт запись в `reservations`. Бэкенд теперь имеет полноценный `/reservations/` API.

```javascript
// 1. Добавить в giftRepository.js:
export async function reserveGift(giftId, reserverName, isAnonymous = false) {
    const response = await api.post("/reservations/", {
        gift_id: giftId,
        reserver_name: reserverName,
        is_anonymous: isAnonymous
    })
    return response.data
}

export async function unreserveGift(reservationId) {
    await api.delete(`/reservations/${reservationId}`)
}
```

```jsx
// 2. В GiftList — заменить handleToggleStatus:
async function handleToggleStatus(gift) {
    if (gift.status === "available") {
        // Бронируем — передаём имя пользователя из localStorage
        const user = JSON.parse(localStorage.getItem("user") || "null")
        await reserveGift(gift.id, user?.name ?? "Аноним")
    } else {
        // Снимаем бронь — нужен reservation_id (хранить в объекте подарка или запрашивать)
        await unreserveGift(gift.reservation_id)
    }
    // Обновить список подарков
    const updated = await getGiftsByEvent(eventId)
    setGifts(Array.isArray(updated) ? updated : [])
}
```

> Чтобы хранить `reservation_id` на фронте, бэкенд должен возвращать его вместе с подарком
> (например, JOIN reservations в `/events/{id}/gifts`).

---

### F8. Статус "Куплено" — нет кнопки в UI

**Файл:** `frontend/src/components/Gifts/GiftCard/GiftCard.jsx`
**Сложность:** ~15 минут

```jsx
// В GiftCard — добавить кнопку для зарезервированных подарков:
{gift.status === "reserved" && onMarkBought && (
    <button
        className="bought-button"
        onClick={() => onMarkBought(gift.id)}
    >
        Куплено ✓
    </button>
)}
```

```jsx
// В GiftList — добавить обработчик:
async function handleMarkBought(giftId) {
    const updated = await updateGiftStatus(giftId, "bought")
    if (updated) {
        setGifts(prev => prev.map(g => g.id === giftId ? updated : g))
    }
}

// Передать в GiftCard:
<GiftCard
    gift={gift}
    onToggleStatus={handleToggleStatus}
    onDelete={handleDeleteGift}
    onMarkBought={handleMarkBought}
/>
```

---

### F9. Редактирование подарка — UI полностью отсутствует

**Файлы:** `frontend/src/components/Gifts/GiftList/GiftList.jsx`, `GiftCard/GiftCard.jsx`
**Сложность:** ~1 час (требует B5)

```javascript
// 1. Добавить в giftRepository.js:
export async function updateGift(giftId, data) {
    const response = await api.patch(`/gifts/${giftId}`, data)
    return response.data
}
```

```javascript
// 2. Добавить в giftApplication.js:
import { updateGift as updateGiftRepository } from "../repositories/giftRepository"

export async function editGift(giftId, data) {
    try {
        return await updateGiftRepository(giftId, data)
    } catch (error) {
        console.error(error)
        return null
    }
}
```

```jsx
// 3. В GiftCard — добавить кнопку редактирования (рядом с кнопкой удаления):
{onEdit && (
    <button className="edit-gift-button" onClick={() => onEdit(gift)}>
        ✏️
    </button>
)}
```

```jsx
// 4. В GiftList — добавить состояние и форму редактирования:
const [editingGift, setEditingGift] = useState(null)

async function handleEditGift(giftId, data) {
    const updated = await editGift(giftId, data)
    if (updated) {
        setGifts(prev => prev.map(g => g.id === giftId ? updated : g))
        setEditingGift(null)
    }
}
```

---

### F10. Поделиться ссылкой — нет кнопки и нет публичной страницы

**Файлы:** `frontend/src/App.jsx`, новый `PublicEventPage`
**Сложность:** ~2 часа (требует B6)

```jsx
// 1. Добавить в App.jsx роут БЕЗ ProtectedRoute:
<Route path="/share/:token" element={<PublicEventPage />} />

// 2. Создать PublicEventPage — загружает событие по токену, без кнопок редактирования:
import { useParams } from "react-router-dom"

function PublicEventPage() {
    const { token } = useParams()
    const [data, setData] = useState(null)

    useEffect(() => {
        api.get(`/events/public/${token}`).then(r => setData(r.data))
    }, [token])

    return data ? (
        <div>
            <h1>{data.event.title}</h1>
            {/* GiftCard без onDelete / onEdit */}
            {data.gifts.map(gift => <GiftCard key={gift.id} gift={gift} />)}
        </div>
    ) : <p>Загрузка...</p>
}

// 3. В EventPage — добавить кнопку «Поделиться»:
function handleShare() {
    navigator.clipboard.writeText(`${window.location.origin}/share/${event.public_token}`)
    // показать тост "Ссылка скопирована"
}
```

---

## Сводная таблица

### Баги

| # | Файл | Что | Сложность | Приоритет |
|---|------|-----|-----------|-----------|
| B1 | `security.py` / `requirements.txt` | passlib + bcrypt → регистрация не работает | минуты | **критично** |
| B2 | `gift_service.py` | `HTTPException` без импорта → NameError | минуты | **критично** |
| B3 | `user_repository.py` | Двойное хеширование пароля в возвращаемом User | минуты | низкий |
| B4 | `reservation_service.py` | Бронирование не меняет статус подарка | ~15 мин | высокий |
| F1 | `LogoutModal.jsx` | Logout не чистит localStorage | минуты | высокий |
| F2 | `Sidebar.jsx` | Захардкоженное "John Doe" | минуты | средний |
| F3 | `App.jsx` | Нет редиректа на `/auth` без токена | ~15 мин | высокий |

### Нереализованные фичи

| # | Файл | Что | Сложность | Приоритет |
|---|------|-----|-----------|-----------|
| F4 | `GiftList.jsx` | Подключить удаление подарка | минуты | высокий |
| F5 | `GiftList.jsx` | Поле `marketplace_url` в форме | минуты | высокий |
| F6 | `GiftCard.jsx` | Показать ссылку на маркетплейс | минуты | высокий |
| F7 | `GiftList.jsx` | Использовать `/reservations/` вместо статус-тогла | ~30 мин | высокий |
| F8 | `GiftCard.jsx` + `GiftList.jsx` | Кнопка «Куплено» | ~15 мин | средний |
| B5 | `gift_router.py` + репо + сервис | `PATCH /gifts/{id}` — редактирование полей | ~30 мин | высокий |
| F9 | `GiftList.jsx` + `GiftCard.jsx` | UI редактирования подарка | ~1 ч | высокий |
| B6 | `event_service.py` + `event_router.py` | Генерация токена + эндпоинт `/events/public/{token}` | ~30 мин | средний |
| F10 | `App.jsx` + новый `PublicEventPage` | Публичная страница + кнопка «Поделиться» | ~2 ч | средний |

---

# Спринт 4

Размер: **S** — пара вечеров, **M** — несколько дней, **L** — большая часть спринта.

### S4.1 + S4.2. Деплой на сервер и домен — **Kirill Shiryev** (L)

- Вынести в `.env` путь к БД, папку `uploads/`, список CORS-origin (сейчас зашит в `main.py`) и адрес API для фронта (`VITE_API_URL` вместо хардкода в `api.js`).
- Поднять uvicorn за nginx, фронт собрать через `npm run build` и отдавать статикой. БД и картинки хранить вне папки с кодом.
- Взять домен (платный или бесплатный), направить на сервер, выпустить HTTPS (Let's Encrypt).

### S4.3. Минимальная длина логина и пароля

- **Бэк — Mikhail (S):** валидация в `/auth/register` и `PATCH /users/me` (минимальная длина, запрет пароля из одинаковых символов), понятный текст ошибки.
- **Фронт — Сенчик (S):** те же проверки в форме регистрации на `AuthPage` с подсказками под полями.

### S4.4. Загрузка своих картинок на подарок

- **Бэк — Mikhail (S):** ручка `POST /images` уже есть. При повторной загрузке той же картинки возвращать существующую, а не 409. Закрыть загрузку и удаление авторизацией, ограничить размер файла. Отдавать `image_url` полным адресом.
- **Фронт — Сенчик (M):** в формах создания и редактирования подарка выбор файла с превью. Файл уходит в `POST /images`, полученный `image_id` — в подарок.

### S4.5. Теги / группы для подарков

- **Бэк — EnotikPoker (M):** таблицы тегов и связи подарок↔тег, CRUD-ручки тегов события, теги в ответе подарка, привязка тегов при создании и редактировании.
- **Фронт — alfur (M):** выбор или создание тегов в форме подарка, чипы тегов на `GiftCard`, группировка списка по тегам.

---

# Спринт 5

### S5.1. Фильтры подарков (цена, теги, название, статус)

- **Бэк — EnotikPoker (M):** query-параметры на `GET /events/{id}/gifts` и публичной ручке (`min_price`, `max_price`, `tags`, `q`, `status`, сортировка).
- **Фронт — Сенчик (M):** панель фильтров над списком подарков на `EventPage` и `PublicEventPage`, состояние фильтров в URL.

### S5.2. Emoji-заглушки вместо битой картинки

- **Фронт — Сенчик (S):** если картинки нет или она не загрузилась (`onError`), в `GiftCard` показывать случайный emoji. Выбирать стабильно по id подарка, чтобы не прыгал при перерисовке.
- **Бэк:** не нужен.

### S5.3. Бронь без регистрации через секретное слово

- **Бэк — EnotikPoker (M):** публичная ручка брони без JWT (имя + секретное слово, хеш слова хранить в `reservations`) и ручка снятия брони по слову. Защита от перебора.
- **Фронт — alfur (M):** на `PublicEventPage` у незалогиненного вместо редиректа на `/auth` модалка «имя + секретное слово». Для отмены брони — ввод того же слова.

### S5.4. Виджет распределения подарков по цене

- **Бэк — Mikhail (S):** ручка статистики события для владельца: число подарков по ценовым диапазонам и рекомендации вида «мало подарков до 1000 ₽».
- **Фронт — Сенчик (M):** виджет на `EventPage` (гистограмма по диапазонам + рекомендации), виден только владельцу.

### S5.5. Автоподтягивание картинки, названия и цены с маркетплейса

- **Бэк — Mikhail (L):** ручка «дай ссылку — верни данные товара». Парсинг Open Graph и мета-тегов, парсеры под популярные маркетплейсы, картинку скачивать к себе через `images`. Таймаут и кеш.
- **Фронт — alfur (S):** кнопка «Заполнить по ссылке» рядом с полем маркетплейса в форме подарка. Заполняет название, цену и картинку, всё остаётся редактируемым.

### S5.6. Рекомендации подарков из общей базы

- **Бэк — Kirill Shiryev (L):** ручка рекомендаций для события: похожие подарки из других событий по тегам, цене, названию и популярности, без дублей с уже добавленными. Приватные данные чужих событий не отдавать.
- **Фронт — alfur (M):** блок «Может понравиться» на `EventPage` с добавлением подарка в своё событие в один клик.

---

## Кто что делает

Фронт и бэк одной задачи делают разные люди. Большие задачи — тем, кто давно не коммитил; маленькие — тем, кто много сделал в последних коммитах (Сенчик, alfur, EnotikPoker).

| Кто | Роль | Спринт 4 | Спринт 5 |
|---|---|---|---|
| **Kirill Shiryev** | бэк / деплой | S4.1 + S4.2 деплой и домен (L) | S5.6 рекомендации (L) |
| **Mikhail** | бэк | S4.3 валидация (S), S4.4 картинки (S) | S5.4 статистика (S), S5.5 парсинг маркетплейса (L) |
| **EnotikPoker** | бэк | S4.5 теги (M) | S5.1 фильтры (M), S5.3 бронь по слову (M) |
| **Сенчик** | фронт | S4.3 валидация (S), S4.4 загрузка картинки (M) | S5.1 фильтры (M), S5.2 emoji (S), S5.4 виджет (M) |
| **alfur** | фронт | S4.5 теги (M) | S5.3 бронь по слову (M), S5.5 кнопка автозаполнения (S), S5.6 блок рекомендаций (M) |

Зависимые бэк-задачи у одного человека: теги → фильтры (EnotikPoker), картинки → парсинг маркетплейса (Mikhail).

Перед началом задачи бэк и фронт договариваются о формате ручки (путь + пример JSON). Фронт до готовности бэка работает на моках из `src/mocks/`.

---

# TODO v3 — бизнес-фичи (спринты 6–8)

Собрано по итогам тестирования 11.10.2026: прогон API, сборка фронта, проверка прода `https://swishlist.duckdns.org`. Подробности — в `PRODUCT_GAPS.md`.

Правила те же:
- фронт и бэк одной задачи делают разные люди;
- зависимые бэк-задачи — у одного человека;
- кто больше сделал в спринтах 4–5, получает задачи поменьше.

## Итоги спринтов 4–5

| Кто | Сделано | Не сделано |
|---|---|---|
| **Mikhail** | S4.3, S4.4, S5.4, S5.5 — бэк | — |
| **Kirill Shiryev** | S4.1 + S4.2 деплой и домен | S5.6 рекомендации |
| **Сенчик** | S4.3, S4.4 — фронт | S5.1 фильтры, S5.2 emoji, S5.4 виджет |
| **alfur** | S4.5 теги — фронт (на моках) | S5.3, S5.5, S5.6 — фронт |
| **EnotikPoker** | — | S4.5 теги, S5.1 фильтры, S5.3 бронь — бэк |

Несделанное перенесено в задачи ниже.

---

# Спринт 6 — чтобы вишлистом можно было пользоваться

### V1. Картинки на проде и заглушки

На проде у любого подарка с картинкой падает страница: `resolveImageUrl` делает `new URL(path, "/api")`. Заглушка берётся с мёртвого `via.placeholder.com`.

- **Фронт — Сенчик (S):** правильно собирать адрес картинки при относительном `VITE_API_URL`. Без картинки показывать emoji (бывшая S5.2). Статусы выводить по-русски вместо `available` / `reserved`.
- **Бэк — Mikhail (S):** удалять картинку может только тот, кто её загрузил. Не отдавать абсолютный путь на сервере. Проверять, что файл действительно картинка.

### V2. Сюрприз остаётся сюрпризом

Сейчас владелец видит брони, а кто бронировал — может узнать любой без логина.

- **Бэк — Kirill Shiryev (M):** владельцу брони в своём событии не отдавать, закрыть `GET /reservations/{id}`. Флаг «показывать брони» для тех, кто хочет знать.
- **Фронт — Сенчик (S):** на странице своего события скрыть статусы брони, добавить переключатель «Показать брони (спойлер)».

### V3. Бронь без регистрации по секретному слову (бывшая S5.3)

- **Бэк — Kirill Shiryev (M):** публичная бронь без JWT (имя + секретное слово, хранить хеш), снятие брони по слову, защита от перебора.
- **Фронт — alfur (M):** на публичной странице у гостя вместо редиректа на `/auth` модалка «имя + секретное слово», отмена брони по слову.

### V4. Приватность и валидация

- **Бэк — EnotikPoker (M):**
  - подарки и событие по id — только владельцу, гостям — только через публичный токен;
  - `GET /users/` закрыть;
  - запретить цену ≤ 0 и пустые названия у подарка и события.
- **Фронт — alfur (S):** те же проверки в формах подарка и события, с подсказками под полями.

### V5. Настоящие теги (бывшая S4.5)

Сейчас на фронте `USE_TAG_MOCKS = true`, бэка нет, после перезагрузки тег пропадает.

- **Бэк — EnotikPoker (M):** таблицы тегов и связи подарок↔тег, ручки `/events/{id}/tags` и `/tags/{id}` — как в `tagRepository.js`. Теги в ответе подарка, приём `tag_ids`.
- **Фронт — alfur (S):** выключить моки, проверить сохранение тегов и группировку на живых данных.

### V6. Работающее автозаполнение с маркетплейса

Ozon отдаёт «HTTP 307», справочник маркетплейсов на проде пустой.

- **Бэк — Mikhail (M):** проходить редиректы и антибот-заголовки. Если страницу не отдают — брать хотя бы данные из ссылки. Заполнить справочник (Ozon, WB, Я.Маркет, AliExpress).
- **Фронт — alfur (S):** кнопка «Заполнить по ссылке» в форме подарка (бывшая S5.5).

### V7. Виджет цен (бывшая S5.4)

- **Фронт — Сенчик (M):** гистограмма по ценовым диапазонам и рекомендации на странице своего события. Бэк уже есть: `GET /events/{id}/statistics`.

---

# Спринт 7 — удобство для владельца и гостей

### V8. Фильтры подарков (бывшая S5.1, после V5)

- **Бэк — EnotikPoker (M):** `min_price`, `max_price`, `tags`, `q`, `status` и сортировка на списке подарков — и для владельца, и на публичной странице.
- **Фронт — Сенчик (M):** панель фильтров на странице события и на публичной странице, фильтры в URL.

### V9. Рекомендации (бывшая S5.6)

- **Бэк — EnotikPoker (L):** похожие подарки по тегам, цене и популярности, без дублей и без приватных данных чужих событий.
- **Фронт — Сенчик (M):** блок «Может понравиться», добавление в своё событие в один клик.

### V10. Почта, восстановление пароля, долгая сессия

Сейчас почты нет, пароль не восстановить, через 90 минут выкидывает на логин.

- **Бэк — Kirill Shiryev (M):** email у пользователя, сброс пароля по ссылке из письма, refresh-токен.
- **Фронт — alfur (S):** email в регистрации и профиле, страницы «Забыли пароль?» и «Новый пароль», тихое обновление токена.

### V11. Уведомления (после V10)

- **Бэк — Kirill Shiryev (L):** письма:
  - владельцу «ваш подарок забронировали» — без деталей, если включён сюрприз;
  - гостям — напоминание за 3 дня до события;
  - бронировавшим — «список обновился».
- **Фронт — alfur (S):** настройки уведомлений в профиле.

### V12. Удобно делиться ссылкой

У ссылки нет превью в мессенджерах, `lang="en"`.

- **Бэк — Mikhail (M):** для `/share/:token` отдавать HTML с Open Graph (название, картинка, число подарков) для ботов Telegram/VK. Правило в nginx в `deploy.yml`.
- **Фронт — alfur (S):** QR-код ссылки, кнопки «Отправить в Telegram / WhatsApp», `lang="ru"`, нормальный `<title>`.

---

# Спринт 8 — то, ради чего возвращаются

### V13. Совместный сбор на дорогой подарок

Сейчас — заготовка с `NotImplementedError`.

- **Бэк — EnotikPoker (L):** ручки взносов (сумма, имя, для гостя — по секретному слову), цель сбора, `contribution_total` в ответе подарка. Собрали полную сумму — подарок забронирован.
- **Фронт — Сенчик (M):** прогресс-бар и кнопка «Скинуться» на карточке, модалка взноса, список участников.

### V14. Жизненный цикл события

- **Бэк — Kirill Shiryev (M):** архив прошедших событий, статус «получен» и благодарность дарителю, копирование вишлиста в новое событие.
- **Фронт — alfur (M):** вкладка «Архив», кнопки «Получил» / «Сказать спасибо», «Создать на основе этого».

### V15. Вопросы к подарку и приоритет

- **Бэк — Mikhail (M):** вопросы и ответы к подарку (гость спрашивает, владелец отвечает), приоритет («очень хочу» / «было бы неплохо»), сортировка по приоритету.
- **Фронт — Сенчик (M):** блок вопросов под подарком, выбор приоритета в форме, бейдж на карточке.

---

## Кто что делает в спринтах 6–8

| Кто | Роль | Спринт 6 | Спринт 7 | Спринт 8 |
|---|---|---|---|---|
| **EnotikPoker** | бэк | V4 приватность (M), V5 теги (M) | V8 фильтры (M), V9 рекомендации (L) | V13 совместный сбор (L) |
| **Kirill Shiryev** | бэк | V2 сюрприз (M), V3 бронь по слову (M) | V10 почта и пароль (M), V11 уведомления (L) | V14 жизненный цикл (M) |
| **Mikhail** | бэк | V1 безопасность картинок (S), V6 парсинг (M) | V12 превью ссылок (M) | V15 вопросы и приоритет (M) |
| **Сенчик** | фронт | V1 картинки и emoji (S), V2 скрытие броней (S), V7 виджет цен (M) | V8 фильтры (M), V9 рекомендации (M) | V13 сбор (M), V15 вопросы (M) |
| **alfur** | фронт | V3 бронь по слову (M), V4 валидация (S), V5 теги без моков (S), V6 автозаполнение (S) | V10 почта и пароль (S), V11 настройки уведомлений (S), V12 шаринг (S) | V14 архив и «спасибо» (M) |

- Mikhail закрыл всё своё в спринтах 4–5, поэтому у него задачи поменьше.
- EnotikPoker не сдал ничего — у него крупные задачи, и первая из них — теги (V5): от них зависят фильтры и рекомендации.
- Цепочки зависимых бэк-задач у одного человека: теги → фильтры → рекомендации (EnotikPoker), почта → уведомления (Kirill).

Моки на фронте выключаются в том же спринте, когда готов бэк, — а не остаются навсегда, как с тегами.
