# Wishlist Frontend

Frontend часть проекта Wishlist.

Стек:
- React
- Vite
- Axios

---

# Запуск проекта

## 1. Перейти в frontend
## 2. Установить зависимости

```bash
npm install
```

`npm install` обязателен после первого clone репозитория, так как папка `node_modules` не хранится в git.

---

## 3. Запустить frontend

```bash
npm run dev
```

Frontend будет доступен по адресу:

```text
http://localhost:5173
```

---

# Backend

Для полноценной работы frontend необходимо запустить backend.

Backend будет доступен по адресу:

```text
http://127.0.0.1:8000/docs
```

---

# Структура frontend

```text
src/

application/     -> frontend business logic
repositories/    -> работа с backend API
services/        -> axios/api layer
mocks/           -> fallback mock data

components/      -> UI компоненты
pages/           -> страницы приложения
```

---

# Слои приложения

## Components

Отвечают только за UI.

Компоненты:
- не делают HTTP requests
- получают данные через props

---

## Application

Слой frontend логики.

Отвечает за:
- вызовы repository
- обработку ошибок
- fallback mocks
- frontend business logic

Пример:

---

## Repository

Слой работы с backend API.

Repository:
- делает HTTP requests
- знает про endpoints
- использует axios

---

## Services

Общие сервисы приложения.

Сейчас:
- axios instance
- baseURL

---

## Mocks

Fallback данные.

Используются если backend недоступен

---
