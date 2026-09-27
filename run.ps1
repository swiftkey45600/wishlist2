#Requires -Version 5.1
<#
.SYNOPSIS
    Запускает проект Wishlist целиком: backend (FastAPI) + frontend (React/Vite).

.DESCRIPTION
    Скрипт делает всё, что нужно для старта с нуля:
      1. проверяет наличие Python и Node.js;
      2. создаёт виртуальное окружение .venv и ставит зависимости из requirements.txt;
      3. создаёт .env с автоматически сгенерированным JWT_SECRET_KEY (без него backend не стартует);
      4. ставит npm-зависимости фронтенда;
      5. поднимает оба сервера и гасит их вместе по Ctrl+C.

    Повторные запуски быстрые: установка пропускается, если зависимости уже актуальны.

.PARAMETER SkipInstall
    Не проверять и не устанавливать зависимости, сразу поднимать серверы.

.PARAMETER BackendOnly
    Запустить только backend.

.PARAMETER FrontendOnly
    Запустить только frontend.

.EXAMPLE
    .\run.ps1
    Полный запуск проекта.

.EXAMPLE
    .\run.ps1 -BackendOnly
    Только API на http://127.0.0.1:8000
#>
[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = 'Stop'

# Порты зашиты в коде проекта, а не только здесь:
#   8000  -> frontend/src/services/api.js  (baseURL)
#   5173  -> app/main.py                   (список разрешённых CORS-origin)
# Менять их нужно одновременно в обоих местах, иначе браузер получит CORS-ошибку.
$BackendPort = 8000
$FrontendPort = 5173

$Root = $PSScriptRoot
$VenvDir = Join-Path $Root '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
$Requirements = Join-Path $Root 'requirements.txt'
$DepsStamp = Join-Path $VenvDir '.requirements.sha256'
$EnvFile = Join-Path $Root '.env'
$FrontendDir = Join-Path $Root 'frontend'
$NodeModules = Join-Path $FrontendDir 'node_modules'

function Write-Step { param([string]$Message) Write-Host "==> $Message" -ForegroundColor Cyan }
function Write-Ok   { param([string]$Message) Write-Host "    $Message" -ForegroundColor DarkGray }
function Write-Warn { param([string]$Message) Write-Host "!!  $Message" -ForegroundColor Yellow }

function Fail {
    param([string]$Message)
    Write-Host "ОШИБКА: $Message" -ForegroundColor Red
    exit 1
}

# Ищем интерпретатор Python: сначала `python`, затем launcher `py`.
function Resolve-SystemPython {
    foreach ($candidate in @('python', 'python3')) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            # В Windows есть заглушка python.exe, открывающая Microsoft Store — она не работает.
            $probe = & $cmd.Source '-c' 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0 -and $probe) { return $cmd.Source }
        }
    }
    $py = Get-Command 'py' -ErrorAction SilentlyContinue
    if ($py) { return $py.Source }
    return $null
}

function Get-FileHashHex {
    param([string]$Path)
    # Приводим к нижнему регистру: Get-FileHash отдаёт HEX в верхнем, а sha256sum
    # в run.sh — в нижнем. Без нормализации переключение между скриптами каждый раз
    # выглядело бы как смена requirements.txt и тянуло лишнюю переустановку.
    return (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Initialize-Backend {
    Write-Step 'Backend: проверяю окружение Python'

    if (-not (Test-Path $VenvPython)) {
        $systemPython = Resolve-SystemPython
        if (-not $systemPython) {
            Fail 'Python не найден в PATH. Установите Python 3.10+ с https://www.python.org/downloads/ и включите опцию "Add python.exe to PATH".'
        }

        # Кавычки внутри кода — одинарные: PowerShell 5.1 при вызове нативного exe
        # съедает вложенные двойные кавычки, и Python получал бы битый синтаксис.
        $version = & $systemPython '-c' "import sys; print('.'.join(map(str, sys.version_info[:2])))"
        Write-Ok "использую Python $version ($systemPython)"

        $tooOld = & $systemPython '-c' 'import sys; print(1 if sys.version_info < (3, 10) else 0)'
        if ($tooOld -eq '1') {
            Fail "Нужен Python 3.10 или новее, найден $version (в коде используется синтаксис 'timedelta | None')."
        }

        Write-Step "Backend: создаю виртуальное окружение в .venv"
        & $systemPython '-m' 'venv' $VenvDir
        if ($LASTEXITCODE -ne 0) { Fail 'не удалось создать виртуальное окружение.' }
    }
    else {
        Write-Ok 'виртуальное окружение .venv уже есть'
    }

    # Ставим зависимости только если requirements.txt изменился с прошлого запуска.
    $requirementsHash = Get-FileHashHex $Requirements
    $stampHash = ''
    if (Test-Path $DepsStamp) { $stampHash = (Get-Content $DepsStamp -Raw).Trim() }

    if ($stampHash -eq $requirementsHash) {
        Write-Ok 'зависимости Python актуальны, установка пропущена'
    }
    else {
        Write-Step 'Backend: устанавливаю зависимости из requirements.txt'
        & $VenvPython '-m' 'pip' 'install' '--upgrade' '--quiet' 'pip'
        & $VenvPython '-m' 'pip' 'install' '--requirement' $Requirements
        if ($LASTEXITCODE -ne 0) { Fail 'pip install завершился с ошибкой (проверьте подключение к сети).' }
        Set-Content -Path $DepsStamp -Value $requirementsHash -Encoding ascii
    }
}

function Initialize-EnvFile {
    if (Test-Path $EnvFile) {
        # Файл есть, но ключ мог остаться пустым после копирования .env.example.
        $hasKey = Select-String -Path $EnvFile -Pattern '^\s*JWT_SECRET_KEY\s*=\s*\S' -Quiet
        if ($hasKey) {
            Write-Ok '.env на месте, JWT_SECRET_KEY заполнен'
            return
        }
        Write-Warn '.env существует, но JWT_SECRET_KEY пустой — backend без него не запустится.'
        Write-Warn "Заполните ключ вручную в $EnvFile или удалите файл и запустите скрипт снова."
        Fail 'пустой JWT_SECRET_KEY в .env'
    }

    Write-Step 'Создаю .env со свежим JWT_SECRET_KEY'
    $secret = & $VenvPython '-c' 'import secrets; print(secrets.token_urlsafe(48))'
    if ($LASTEXITCODE -ne 0 -or -not $secret) { Fail 'не удалось сгенерировать JWT_SECRET_KEY.' }

    $content = @"
# Создано автоматически скриптом run.ps1. Не коммитить — файл в .gitignore.
JWT_SECRET_KEY=$($secret.Trim())
"@
    # Пишем UTF-8 без BOM вручную: `Set-Content -Encoding utf8` в PowerShell 5.1
    # добавляет BOM, и эти три байта прилипли бы к имени первой переменной в .env.
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($EnvFile, $content + "`r`n", $utf8NoBom)
    Write-Ok 'ключ сгенерирован'
}

function Initialize-Frontend {
    Write-Step 'Frontend: проверяю окружение Node.js'

    if (-not (Get-Command 'npm' -ErrorAction SilentlyContinue)) {
        Fail 'npm не найден в PATH. Установите Node.js 20+ с https://nodejs.org/'
    }

    $nodeVersion = (& node '--version').TrimStart('v')
    $nodeMajor = [int]($nodeVersion -split '\.')[0]
    if ($nodeMajor -lt 20) {
        Fail "Нужен Node.js 20 или новее (Vite 8 требует именно так), найден $nodeVersion."
    }
    Write-Ok "использую Node.js $nodeVersion"

    # Переустанавливаем, если node_modules нет или package-lock.json свежее.
    $needInstall = $true
    if (Test-Path $NodeModules) {
        $lock = Join-Path $FrontendDir 'package-lock.json'
        $lockTime = (Get-Item $lock).LastWriteTimeUtc
        $modulesTime = (Get-Item $NodeModules).LastWriteTimeUtc
        if ($modulesTime -ge $lockTime) {
            $needInstall = $false
            Write-Ok 'node_modules актуальны, установка пропущена'
        }
    }

    if ($needInstall) {
        Write-Step 'Frontend: устанавливаю npm-зависимости (может занять пару минут)'
        Push-Location $FrontendDir
        try {
            & npm install
            if ($LASTEXITCODE -ne 0) { Fail 'npm install завершился с ошибкой.' }
        }
        finally { Pop-Location }
    }
}

# Гасим процесс вместе со всем деревом детей: uvicorn и vite порождают подпроцессы,
# которые останутся висеть на портах, если убить только родителя.
function Stop-ProcessTree {
    param($Process)
    if ($null -eq $Process) { return }
    if ($Process.HasExited) { return }
    & taskkill '/T' '/F' '/PID' $Process.Id *> $null
}

$processes = @()

try {
    Write-Host ''
    Write-Host 'Wishlist — запуск проекта' -ForegroundColor Green
    Write-Host ''

    if (-not $SkipInstall) {
        if (-not $FrontendOnly) {
            Initialize-Backend
            Initialize-EnvFile
        }
        if (-not $BackendOnly) {
            Initialize-Frontend
        }
    }
    else {
        Write-Ok 'установка зависимостей пропущена (-SkipInstall)'
        if (-not $FrontendOnly -and -not (Test-Path $VenvPython)) {
            Fail 'нет .venv — запустите скрипт без -SkipInstall хотя бы один раз.'
        }
    }

    Write-Host ''

    if (-not $FrontendOnly) {
        Write-Step "Стартую backend на http://127.0.0.1:$BackendPort"
        $backend = Start-Process -FilePath $VenvPython `
            -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--reload', '--port', "$BackendPort") `
            -WorkingDirectory $Root -NoNewWindow -PassThru
        $processes += $backend
    }

    if (-not $BackendOnly) {
        Write-Step "Стартую frontend на http://localhost:$FrontendPort"
        # npm.cmd, а не npm: Start-Process не умеет запускать shell-обёртки без расширения.
        $frontend = Start-Process -FilePath 'npm.cmd' `
            -ArgumentList @('run', 'dev') `
            -WorkingDirectory $FrontendDir -NoNewWindow -PassThru
        $processes += $frontend
    }

    Write-Host ''
    Write-Host '--------------------------------------------------' -ForegroundColor Green
    if (-not $BackendOnly)  { Write-Host "  Приложение   http://localhost:$FrontendPort" -ForegroundColor Green }
    if (-not $FrontendOnly) { Write-Host "  API          http://127.0.0.1:$BackendPort" -ForegroundColor Green }
    if (-not $FrontendOnly) { Write-Host "  Swagger UI   http://127.0.0.1:$BackendPort/docs" -ForegroundColor Green }
    Write-Host '  Остановить   Ctrl+C' -ForegroundColor Green
    Write-Host '--------------------------------------------------' -ForegroundColor Green
    Write-Host ''

    # Держим скрипт живым, пока работают оба сервера. Если один упал — гасим второй,
    # чтобы не остаться с половиной приложения.
    while ($true) {
        $alive = @($processes | Where-Object { -not $_.HasExited })
        if ($alive.Count -lt $processes.Count) {
            Write-Warn 'один из серверов остановился, завершаю остальные'
            break
        }
        Start-Sleep -Milliseconds 400
    }
}
finally {
    Write-Host ''
    Write-Step 'Останавливаю серверы'
    foreach ($proc in $processes) { Stop-ProcessTree $proc }
    Write-Ok 'готово'
}
