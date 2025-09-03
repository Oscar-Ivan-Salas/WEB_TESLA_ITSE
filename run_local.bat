@echo off
setlocal
SET BASE=%~dp0
SET BACKEND=%BASE%backend
SET FRONTEND=%BASE%frontend
SET VENV=%BACKEND%\.venv
IF NOT EXIST "%VENV%\Scripts\activate.bat" (
  echo Creando venv...
  python -m venv "%VENV%"
  "%VENV%\Scripts\pip.exe" install --upgrade pip
  "%VENV%\Scripts\pip.exe" install -r "%BACKEND%\requirements.txt"
)
start "tesla-backend" cmd /k "cd /d %BACKEND% && call %VENV%\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000"
start "tesla-frontend" cmd /k "cd /d %FRONTEND% && python -m http.server 8080"
timeout /t 2 >NUL
start http://localhost:8080
echo ✅ Backend: http://127.0.0.1:8000  ^|  Frontend: http://localhost:8080
endlocal
