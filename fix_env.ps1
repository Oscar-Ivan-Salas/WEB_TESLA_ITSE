# Script para solucionar problemas de entorno

# 1. Detener cualquier proceso de Python que pueda estar usando el entorno
Write-Host "Deteniendo procesos de Python..." -ForegroundColor Yellow
Get-Process python* | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. Cambiar al directorio del proyecto
$projectDir = "E:\WEB_TESLA_ITSE"
Set-Location $projectDir

# 3. Eliminar el entorno virtual existente si existe
$venvPath = "$projectDir\.venv"
if (Test-Path $venvPath) {
    Write-Host "Eliminando entorno virtual existente..." -ForegroundColor Yellow
    try {
        Remove-Item -Path $venvPath -Recurse -Force -ErrorAction Stop
        Write-Host "Entorno virtual eliminado correctamente." -ForegroundColor Green
    } catch {
        Write-Host "Error al eliminar el entorno virtual: $_" -ForegroundColor Red
        exit 1
    }
}

# 4. Crear un nuevo entorno virtual
Write-Host "Creando nuevo entorno virtual..." -ForegroundColor Cyan
try {
    python -m venv $venvPath
    if (-not $?) { throw "Error al crear el entorno virtual" }
    Write-Host "Entorno virtual creado correctamente." -ForegroundColor Green
} catch {
    Write-Host "Error al crear el entorno virtual: $_" -ForegroundColor Red
    exit 1
}

# 5. Activar el entorno virtual e instalar dependencias
$activatePath = "$venvPath\Scripts\Activate.ps1"
if (-not (Test-Path $activatePath)) {
    Write-Host "No se pudo encontrar el script de activación." -ForegroundColor Red
    exit 1
}

Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
. $activatePath

# 6. Actualizar pip e instalar dependencias
Write-Host "Actualizando pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# 7. Instalar dependencias del proyecto
$requirementsPath = "$projectDir\backend\requirements.txt"
if (Test-Path $requirementsPath) {
    Write-Host "Instalando dependencias..." -ForegroundColor Cyan
    pip install -r $requirementsPath
} else {
    Write-Host "No se encontró requirements.txt" -ForegroundColor Yellow
}

Write-Host "`nConfiguración completada.`n" -ForegroundColor Green
Write-Host "Para activar el entorno virtual manualmente, ejecuta:" -ForegroundColor White
Write-Host ".\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "`nPara iniciar el servidor de desarrollo:" -ForegroundColor White
Write-Host "cd backend" -ForegroundColor Cyan
Write-Host "uvicorn app.main:app --reload" -ForegroundColor Cyan
