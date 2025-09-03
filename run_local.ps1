# Arranca backend (uvicorn) y servidor estático del frontend
param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$Base = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Base 'backend'
$Frontend = Join-Path $Base 'frontend'
$Venv = Join-Path $Backend '.venv'

$Activate = Join-Path $Venv 'Scripts\Activate.ps1'
if (!(Test-Path $Activate)) {
  Write-Host 'Creando venv...'
  python -m venv $Venv
  & "$Venv\Scripts\pip.exe" install --upgrade pip
  & "$Venv\Scripts\pip.exe" install -r "$Backend\requirements.txt"
}
. $Activate
Start-Process -WindowStyle Minimized powershell -ArgumentList @('-NoExit','-Command',"cd `"$Backend`"; . .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --host 0.0.0.0 --port 8000")
Start-Process -WindowStyle Minimized powershell -ArgumentList @('-NoExit','-Command',"cd `"$Frontend`"; python -m http.server 8080")
if (-not $NoBrowser) { Start-Sleep -Seconds 2; Start-Process 'http://localhost:8080' }
Write-Host '✅ Backend: http://127.0.0.1:8000 | Frontend: http://localhost:8080'
