# Script para configurar el entorno de desarrollo

# 1. Ir al directorio del proyecto
$projectDir = "E:\WEB_TESLA_ITSE"
Set-Location $projectDir

# 2. Verificar Python
Write-Host "`n=== Verificando Python ===" -ForegroundColor Cyan
python --version
if (-not $?) {
    Write-Host "Error: Python no está instalado o no está en el PATH" -ForegroundColor Red
    exit 1
}

# 3. Crear/limpiar entorno virtual
$venvPath = "$projectDir\.venv"
if (Test-Path $venvPath) {
    Write-Host "`nEliminando entorno virtual existente..." -ForegroundColor Yellow
    Remove-Item -Path $venvPath -Recurse -Force
}

Write-Host "`n=== Creando entorno virtual ===" -ForegroundColor Cyan
python -m venv $venvPath

# 4. Activar entorno virtual e instalar dependencias
Write-Host "`n=== Instalando dependencias ===" -ForegroundColor Cyan
& "$venvPath\Scripts\activate.ps1"
python -m pip install --upgrade pip
Set-Location "$projectDir\backend"
pip install -r requirements.txt

# 5. Verificar instalación
Write-Host "`n=== Verificando instalación ===" -ForegroundColor Cyan
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"
python -c "import uvicorn; print(f'Uvicorn version: {uvicorn.__version__}')"

# 6. Iniciar el servidor (opcional)
Write-Host "`nPara iniciar el servidor, ejecuta:" -ForegroundColor Green
Write-Host "cd $projectDir\backend" -ForegroundColor White
Write-Host ".\.venv\Scripts\activate" -ForegroundColor White
Write-Host "uvicorn app.main:app --reload" -ForegroundColor White
