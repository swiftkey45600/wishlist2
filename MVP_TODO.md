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
