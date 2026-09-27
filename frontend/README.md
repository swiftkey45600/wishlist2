# Wishlist Frontend

Frontend часть проекта Wishlist.

Стек:
- React
- Vite
- Axios

> Чтобы поднять весь проект одной командой (frontend + backend), используйте скрипт из корня:
> `.\run.ps1` на Windows или `./run.sh` на Linux/macOS — см. [корневой README](../README.md).
> Ниже — запуск только frontend.

Требуется Node.js 20 или новее (требование Vite 8).

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

Для полноценной работы frontend необходимо запустить backend — иначе слой `application/`
подставит моки из `src/mocks/`, и на страницах будут данные, которых нет в БД.

Backend будет доступен по адресу:

```text
http://127.0.0.1:8000/docs
```

Адрес API задан в `src/services/api.js` (`baseURL`). Если менять его, нужно синхронно поправить
список разрешённых CORS-origin в `app/main.py`, иначе браузер заблокирует запросы.

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
