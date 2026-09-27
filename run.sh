#!/usr/bin/env bash
#
# Запускает проект Wishlist целиком: backend (FastAPI) + frontend (React/Vite).
#
# Скрипт делает всё, что нужно для старта с нуля:
#   1. проверяет наличие Python и Node.js;
#   2. создаёт виртуальное окружение .venv и ставит зависимости из requirements.txt;
#   3. создаёт .env с автоматически сгенерированным JWT_SECRET_KEY (без него backend не стартует);
#   4. ставит npm-зависимости фронтенда;
#   5. поднимает оба сервера и гасит их вместе по Ctrl+C.
#
# Повторные запуски быстрые: установка пропускается, если зависимости уже актуальны.
#
# Использование:
#   ./run.sh                  полный запуск
#   ./run.sh --backend-only   только API
#   ./run.sh --frontend-only  только фронтенд
#   ./run.sh --skip-install   не проверять зависимости
#
set -euo pipefail

# Порты зашиты в коде проекта, а не только здесь:
#   8000  -> frontend/src/services/api.js  (baseURL)
#   5173  -> app/main.py                   (список разрешённых CORS-origin)
# Менять их нужно одновременно в обоих местах, иначе браузер получит CORS-ошибку.
BACKEND_PORT=8000
FRONTEND_PORT=5173

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT/.venv"
REQUIREMENTS="$ROOT/requirements.txt"
DEPS_STAMP="$VENV_DIR/.requirements.sha256"
ENV_FILE="$ROOT/.env"
FRONTEND_DIR="$ROOT/frontend"
NODE_MODULES="$FRONTEND_DIR/node_modules"

VENV_PYTHON=''
SKIP_INSTALL=0
BACKEND_ONLY=0
FRONTEND_ONLY=0

if [ -t 1 ]; then
    C_CYAN=$'\033[36m'; C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'
    C_RED=$'\033[31m';  C_DIM=$'\033[90m';   C_OFF=$'\033[0m'
else
    C_CYAN=''; C_GREEN=''; C_YELLOW=''; C_RED=''; C_DIM=''; C_OFF=''
fi

step() { printf '%s==> %s%s\n' "$C_CYAN" "$1" "$C_OFF"; }
ok()   { printf '%s    %s%s\n' "$C_DIM" "$1" "$C_OFF"; }
warn() { printf '%s!!  %s%s\n' "$C_YELLOW" "$1" "$C_OFF"; }
fail() { printf '%sОШИБКА: %s%s\n' "$C_RED" "$1" "$C_OFF" >&2; exit 1; }

usage() {
    sed -n '3,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 0
}

while [ $# -gt 0 ]; do
    case "$1" in
        --skip-install)  SKIP_INSTALL=1 ;;
        --backend-only)  BACKEND_ONLY=1 ;;
        --frontend-only) FRONTEND_ONLY=1 ;;
        -h|--help)       usage ;;
        *) fail "неизвестный аргумент: $1 (см. ./run.sh --help)" ;;
    esac
    shift
done

# Ищем системный интерпретатор Python 3.
resolve_system_python() {
    local candidate
    for candidate in python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' 2>/dev/null; then
                command -v "$candidate"
                return 0
            fi
        fi
    done
    return 1
}

# Linux/macOS кладут интерпретатор venv в bin/, Windows (Git Bash, WSL-less MSYS) — в Scripts/.
find_venv_python() {
    local path
    for path in "$VENV_DIR/bin/python" "$VENV_DIR/Scripts/python.exe"; do
        if [ -x "$path" ]; then
            printf '%s' "$path"
            return 0
        fi
    done
    return 1
}

# sha256sum есть в Linux, shasum — в macOS.
file_sha256() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | cut -d' ' -f1
    else
        shasum -a 256 "$1" | cut -d' ' -f1
    fi
}

setup_backend() {
    step 'Backend: проверяю окружение Python'

    if VENV_PYTHON="$(find_venv_python)"; then
        ok 'виртуальное окружение .venv уже есть'
    else
        local system_python version
        system_python="$(resolve_system_python)" \
            || fail 'Python 3 не найден в PATH. Установите Python 3.10+ (например: sudo apt install python3 python3-venv).'

        version="$("$system_python" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
        ok "использую Python $version ($system_python)"

        "$system_python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
            || fail "Нужен Python 3.10 или новее, найден $version (в коде используется синтаксис 'timedelta | None')."

        step 'Backend: создаю виртуальное окружение в .venv'
        "$system_python" -m venv "$VENV_DIR" \
            || fail 'не удалось создать виртуальное окружение. В Debian/Ubuntu поставьте пакет python3-venv.'

        VENV_PYTHON="$(find_venv_python)" \
            || fail 'виртуальное окружение создано, но интерпретатор в нём не найден.'
    fi

    # Ставим зависимости только если requirements.txt изменился с прошлого запуска.
    local requirements_hash stamp_hash
    requirements_hash="$(file_sha256 "$REQUIREMENTS")"
    stamp_hash=''
    # Вычищаем пробелы и CR: run.ps1 пишет этот же файл через Set-Content,
    # который дописывает CRLF в конец.
    [ -f "$DEPS_STAMP" ] && stamp_hash="$(tr -d '[:space:]' < "$DEPS_STAMP")"

    if [ "$stamp_hash" = "$requirements_hash" ]; then
        ok 'зависимости Python актуальны, установка пропущена'
    else
        step 'Backend: устанавливаю зависимости из requirements.txt'
        "$VENV_PYTHON" -m pip install --upgrade --quiet pip
        "$VENV_PYTHON" -m pip install --requirement "$REQUIREMENTS" \
            || fail 'pip install завершился с ошибкой (проверьте подключение к сети).'
        printf '%s' "$requirements_hash" > "$DEPS_STAMP"
    fi
}

setup_env_file() {
    if [ -f "$ENV_FILE" ]; then
        # Файл есть, но ключ мог остаться пустым после копирования .env.example.
        if grep -Eq '^[[:space:]]*JWT_SECRET_KEY[[:space:]]*=[[:space:]]*[^[:space:]]' "$ENV_FILE"; then
            ok '.env на месте, JWT_SECRET_KEY заполнен'
            return
        fi
        warn '.env существует, но JWT_SECRET_KEY пустой — backend без него не запустится.'
        warn "Заполните ключ вручную в $ENV_FILE или удалите файл и запустите скрипт снова."
        fail 'пустой JWT_SECRET_KEY в .env'
    fi

    step 'Создаю .env со свежим JWT_SECRET_KEY'
    local secret
    secret="$("$VENV_PYTHON" -c 'import secrets; print(secrets.token_urlsafe(48))')" \
        || fail 'не удалось сгенерировать JWT_SECRET_KEY.'

    cat > "$ENV_FILE" <<EOF
# Создано автоматически скриптом run.sh. Не коммитить — файл в .gitignore.
JWT_SECRET_KEY=$secret
EOF
    chmod 600 "$ENV_FILE"
    ok 'ключ сгенерирован'
}

setup_frontend() {
    step 'Frontend: проверяю окружение Node.js'

    # Проверяем оба: в некоторых окружениях (например, WSL с npm из Windows-PATH)
    # npm находится, а самого node нет, и падение случалось бы уже внутри vite.
    local tool
    for tool in node npm; do
        command -v "$tool" >/dev/null 2>&1 \
            || fail "$tool не найден в PATH. Установите Node.js 20+ с https://nodejs.org/"
    done

    local node_version node_major
    node_version="$(node --version)"
    node_major="${node_version#v}"
    node_major="${node_major%%.*}"
    if [ "$node_major" -lt 20 ]; then
        fail "Нужен Node.js 20 или новее (Vite 8 требует именно так), найден ${node_version#v}."
    fi
    ok "использую Node.js ${node_version#v}"

    # Переустанавливаем, если node_modules нет или package-lock.json свежее.
    if [ -d "$NODE_MODULES" ] && [ ! "$FRONTEND_DIR/package-lock.json" -nt "$NODE_MODULES" ]; then
        ok 'node_modules актуальны, установка пропущена'
    else
        step 'Frontend: устанавливаю npm-зависимости (может занять пару минут)'
        ( cd "$FRONTEND_DIR" && npm install ) || fail 'npm install завершился с ошибкой.'
    fi
}

BACKEND_PID=''
FRONTEND_PID=''

# Возвращает PID'ы прямых детей процесса.
# pgrep есть в Linux и macOS, но не в Git Bash под Windows — там выручает `ps -ef`:
# у него PID во втором столбце, а PPID в третьем на всех трёх платформах.
list_children() {
    local parent="$1"
    if command -v pgrep >/dev/null 2>&1; then
        pgrep -P "$parent" 2>/dev/null || true
    else
        ps -ef 2>/dev/null | awk -v ppid="$parent" 'NR > 1 && $3 == ppid { print $2 }' || true
    fi
}

# Гасим процесс вместе с детьми: `uvicorn --reload` держит воркер отдельным
# процессом, а vite — свои подпроцессы. Убьём только родителя — воркер останется
# сиротой и продолжит держать порт, и следующий запуск упадёт с "address in use".
# Рекурсия по детям, а не `kill -PGID`: setsid нет в macOS, а группа процессов
# здесь общая с самим скриптом, так что по PGID мы застрелили бы и сам скрипт.
kill_tree() {
    local pid="$1"
    [ -n "$pid" ] || return 0

    # Сначала дети, потом родитель — иначе дети успевают осиротеть и потеряться.
    local child
    for child in $(list_children "$pid"); do
        kill_tree "$child"
    done
    kill "$pid" 2>/dev/null || true
}

cleanup() {
    trap - EXIT INT TERM
    printf '\n'
    step 'Останавливаю серверы'
    kill_tree "$BACKEND_PID"
    kill_tree "$FRONTEND_PID"
    wait 2>/dev/null || true
    ok 'готово'
}
trap cleanup EXIT INT TERM

printf '\n%sWishlist — запуск проекта%s\n\n' "$C_GREEN" "$C_OFF"

if [ "$SKIP_INSTALL" -eq 0 ]; then
    if [ "$FRONTEND_ONLY" -eq 0 ]; then
        setup_backend
        setup_env_file
    fi
    if [ "$BACKEND_ONLY" -eq 0 ]; then
        setup_frontend
    fi
else
    ok 'установка зависимостей пропущена (--skip-install)'
    if [ "$FRONTEND_ONLY" -eq 0 ]; then
        VENV_PYTHON="$(find_venv_python)" \
            || fail 'нет .venv — запустите скрипт без --skip-install хотя бы один раз.'
    fi
fi

printf '\n'

if [ "$FRONTEND_ONLY" -eq 0 ]; then
    step "Стартую backend на http://127.0.0.1:$BACKEND_PORT"
    # exec в подоболочке: тогда $! — это PID самого uvicorn, а не обёртки.
    ( cd "$ROOT" && exec "$VENV_PYTHON" -m uvicorn app.main:app --reload --port "$BACKEND_PORT" ) &
    BACKEND_PID=$!
fi

if [ "$BACKEND_ONLY" -eq 0 ]; then
    step "Стартую frontend на http://localhost:$FRONTEND_PORT"
    ( cd "$FRONTEND_DIR" && exec npm run dev ) &
    FRONTEND_PID=$!
fi

printf '\n%s--------------------------------------------------%s\n' "$C_GREEN" "$C_OFF"
[ "$BACKEND_ONLY"  -eq 0 ] && printf '%s  Приложение   http://localhost:%s%s\n'      "$C_GREEN" "$FRONTEND_PORT" "$C_OFF"
[ "$FRONTEND_ONLY" -eq 0 ] && printf '%s  API          http://127.0.0.1:%s%s\n'      "$C_GREEN" "$BACKEND_PORT"  "$C_OFF"
[ "$FRONTEND_ONLY" -eq 0 ] && printf '%s  Swagger UI   http://127.0.0.1:%s/docs%s\n' "$C_GREEN" "$BACKEND_PORT"  "$C_OFF"
printf '%s  Остановить   Ctrl+C%s\n' "$C_GREEN" "$C_OFF"
printf '%s--------------------------------------------------%s\n\n' "$C_GREEN" "$C_OFF"

# Ждём, пока живы все запущенные серверы. Если один упал — выходим, а trap погасит
# остальные, чтобы не остаться с половиной приложения.
# Опрос через `kill -0`, а не `wait -n`: в macOS штатный bash 3.2 без -n.
while true; do
    if [ -n "$BACKEND_PID" ] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then break; fi
    if [ -n "$FRONTEND_PID" ] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then break; fi
    sleep 0.5
done

warn 'один из серверов остановился, завершаю остальные'
