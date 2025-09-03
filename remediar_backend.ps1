# Script de remediación para el backend

# 0) Configuración inicial
$BASE = "E:\WEB_TESLA_ITSE"
Set-Location $BASE\backend

# 1) Cerrar procesos que puedan estar bloqueando
Write-Host "Deteniendo procesos Python/uvicorn..." -ForegroundColor Yellow
taskkill /IM python.exe /F 2>$null
taskkill /IM uvicorn.exe /F 2>$null

# 2) Recrear entorno virtual limpio
Write-Host "`nCreando entorno virtual limpio..." -ForegroundColor Cyan
if (Test-Path ".\.venv") { 
    Remove-Item -Recurse -Force .\.venv 
    Write-Host "Entorno virtual anterior eliminado." -ForegroundColor Green
}

python -m venv .venv
if (-not $?) {
    Write-Host "Error al crear el entorno virtual" -ForegroundColor Red
    exit 1
}

# 3) Actualizar pip e instalar dependencias
Write-Host "`nActualizando pip..." -ForegroundColor Cyan
.\\.venv\Scripts\python.exe -m pip install --upgrade pip

# 4) Configurar requirements.txt con versiones compatibles
Write-Host "`nConfigurando dependencias..." -ForegroundColor Cyan
@"
fastapi==0.115.2
uvicorn[standard]==0.30.6
pydantic==2.8.2
SQLAlchemy==2.0.32
httpx==0.27.2
python-dotenv==1.0.1
"@ | Out-File -Encoding utf8 "$BASE\backend\requirements.txt"

# 5) Instalar dependencias
Write-Host "Instalando dependencias..." -ForegroundColor Cyan
.\\.venv\Scripts\pip.exe install -r .\requirements.txt
if (-not $?) {
    Write-Host "Error al instalar dependencias" -ForegroundColor Red
    exit 1
}

# 6) Verificar archivo .env
$envFile = "$BASE\secrets\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "`nADVERTENCIA: No se encontró $envFile" -ForegroundColor Yellow
    Write-Host "Creando archivo .env de ejemplo..." -ForegroundColor Yellow
    @"
# Configuración de base de datos
DB_URL=sqlite:///./tesla.db

# Configuración de Telegram (opcional)
# TELEGRAM_BOT_TOKEN=tu_token_aqui
# TELEGRAM_CHAT_ID=tu_chat_id

# Configuración del modelo de IA (opcional)
# AI_PROVIDER=openai
# OPENAI_API_KEY=tu_api_key_aqui
"@ | Out-File -Encoding utf8 $envFile -Force
    Write-Host "Archivo .env de ejemplo creado en $envFile" -ForegroundColor Green
}

# 7) (Opcional) Sembrar KB
$seedFile = "$BASE\backend\app\seed_kb.py"
if (Test-Path $seedFile) {
    Write-Host "`nSembrando base de conocimientos..." -ForegroundColor Cyan
    .\.venv\Scripts\python.exe .\app\seed_kb.py
}

# 8) Iniciar servidor
Write-Host "`nIniciando servidor FastAPI..." -ForegroundColor Green
Write-Host "URLs de acceso:" -ForegroundColor Cyan
Write-Host "- API: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "- Documentación: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "- Health check: http://127.0.0.1:8000/healthz" -ForegroundColor White
Write-Host "`nPresiona Ctrl+C para detener el servidor`n" -ForegroundColor Yellow

# Iniciar el servidor
.\\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
