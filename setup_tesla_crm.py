# -*- coding: utf-8 -*-
"""
Crea backend (FastAPI), venv, Docker y runners SIN tocar frontend/index.html.
Ruta objetivo: E:\\WEB_TESLA_ITSE (ajusta BASE_DIR si usas otra).
"""

import subprocess
from pathlib import Path

# ====== CONFIG ======
BASE_DIR = Path(r"E:\WEB_TESLA_ITSE")
FRONTEND_DIR = BASE_DIR / "frontend"
BACKEND_DIR = BASE_DIR / "backend"
BACKEND_APP = BACKEND_DIR / "app"
VENV_DIR = BACKEND_DIR / ".venv"

# ====== ARCHIVOS QUE SE CREAN ======

DOCKER_COMPOSE = (
    'version: "3.9"\n'
    "services:\n"
    "  backend:\n"
    "    build: ./backend\n"
    "    container_name: tesla-backend\n"
    "    env_file:\n"
    "      - ./backend/.env\n"
    '    ports: ["8000:8000"]\n'
    "    networks: [tesla_net]\n"
    "\n"
    "  frontend:\n"
    "    build: ./frontend\n"
    "    container_name: tesla-frontend\n"
    "    depends_on: [backend]\n"
    '    ports: ["80:80"]\n'
    "    networks: [tesla_net]\n"
    "\n"
    "networks:\n"
    "  tesla_net:\n"
    "    driver: bridge\n"
)

FRONTEND_DOCKERFILE = (
    "FROM nginx:alpine\n"
    "COPY index.html /usr/share/nginx/html/index.html\n"
    "COPY nginx.conf /etc/nginx/conf.d/default.conf\n"
    "EXPOSE 80\n"
)

FRONTEND_NGINX = (
    "server {\n"
    "  listen 80;\n"
    "  server_name _;\n"
    "  root /usr/share/nginx/html;\n"
    "  index index.html;\n"
    "  location /api/ {\n"
    "    proxy_pass http://backend:8000/api/;\n"
    "    proxy_set_header Host $host;\n"
    "    proxy_set_header X-Real-IP $remote_addr;\n"
    "    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
    "  }\n"
    "  location /healthz {\n"
    "    proxy_pass http://backend:8000/healthz;\n"
    "  }\n"
    "}\n"
)

BACKEND_DOCKERFILE = (
    "FROM python:3.11-slim\n"
    "ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\n"
    "WORKDIR /app\n"
    "COPY requirements.txt .\n"
    "RUN pip install --no-cache-dir -r requirements.txt\n"
    "COPY app ./app\n"
    "EXPOSE 8000\n"
    'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]\n'
)

REQUIREMENTS = (
    "fastapi==0.115.0\n"
    "uvicorn[standard]==0.30.5\n"
    "pydantic==2.8.2\n"
    "SQLAlchemy==2.0.32\n"
    "httpx==0.27.0\n"
    "python-dotenv==1.0.1\n"
)

ENV_EXAMPLE = (
    "# === Core ===\n"
    "ENV=production\n"
    "\n"
    "# IA opcional: openai | none\n"
    "AI_PROVIDER=none\n"
    "OPENAI_API_KEY=\n"
    "\n"
    "# Telegram (notificación de leads)\n"
    "TELEGRAM_BOT_TOKEN=\n"
    "TELEGRAM_CHAT_ID=\n"
    "\n"
    "# DB SQLite\n"
    "DB_URL=sqlite:///./tesla.db\n"
    "\n"
    "# CORS (en pruebas puede quedar *)\n"
    "ALLOWED_ORIGINS=*\n"
)

MAIN_PY = (
    "import os\n"
    "from typing import Optional\n"
    "from fastapi import FastAPI, HTTPException\n"
    "from fastapi.middleware.cors import CORSMiddleware\n"
    "from pydantic import BaseModel, EmailStr, Field\n"
    "from sqlalchemy import create_engine, text\n"
    "from sqlalchemy.orm import sessionmaker\n"
    "import httpx\n"
    "from dotenv import load_dotenv\n"
    "\n"
    "load_dotenv()\n"
    "AI_PROVIDER = os.getenv('AI_PROVIDER', 'none').lower()\n"
    "OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')\n"
    "DB_URL = os.getenv('DB_URL', 'sqlite:///./tesla.db')\n"
    "ALLOWED_ORIGINS = [o.strip() for o in os.getenv('ALLOWED_ORIGINS', '*').split(',')]\n"
    "\n"
    "engine = create_engine(DB_URL, connect_args={'check_same_thread': False} if DB_URL.startswith('sqlite') else {})\n"
    "SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)\n"
    "\n"
    "with engine.begin() as conn:\n"
    "    conn.exec_driver_sql(\n"
    "        '''\n"
    "        CREATE TABLE IF NOT EXISTS leads (\n"
    "            id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
    "            name TEXT NOT NULL,\n"
    "            email TEXT,\n"
    "            phone TEXT,\n"
    "            service TEXT,\n"
    "            message TEXT,\n"
    "            created_at DATETIME DEFAULT CURRENT_TIMESTAMP\n"
    "        )\n"
    "        '''\n"
    "    )\n"
    "\n"
    "app = FastAPI(title='Tesla CRM API')\n"
    "app.add_middleware(\n"
    "    CORSMiddleware,\n"
    "    allow_origins=['*'] if '*' in ALLOWED_ORIGINS else ALLOWED_ORIGINS,\n"
    "    allow_credentials=True,\n"
    "    allow_methods=['*'],\n"
    "    allow_headers=['*'],\n"
    ")\n"
    "\n"
    "class LeadIn(BaseModel):\n"
    "    name: str = Field(..., min_length=2)\n"
    "    email: Optional[EmailStr] = None\n"
    "    phone: str = Field(..., min_length=6)\n"
    "    service: Optional[str] = None\n"
    "    message: Optional[str] = None\n"
    "\n"
    "class ChatIn(BaseModel):\n"
    "    message: str\n"
    "    use_ai: bool = True\n"
    "\n"
    "class ChatOut(BaseModel):\n"
    "    reply: str\n"
    "\n"
    "@app.get('/healthz')\n"
    "async def healthz():\n"
    "    return {'ok': True}\n"
    "\n"
    "@app.post('/api/leads')\n"
    "async def create_lead(payload: LeadIn):\n"
    "    if payload.name.lower().startswith('http'):\n"
    "        raise HTTPException(status_code=400, detail='Invalid name')\n"
    "    with engine.begin() as conn:\n"
    "        conn.execute(text(\n"
    "            'INSERT INTO leads(name,email,phone,service,message) '\n"
    "            'VALUES(:name,:email,:phone,:service,:message)'\n"
    "        ), payload.model_dump())\n"
    "    await notify_telegram(payload)\n"
    "    return {'ok': True}\n"
    "\n"
    "async def notify_telegram(lead: LeadIn):\n"
    "    token = os.getenv('TELEGRAM_BOT_TOKEN')\n"
    "    chat_id = os.getenv('TELEGRAM_CHAT_ID')\n"
    "    if not token or not chat_id:\n"
    "        return\n"
    "    text_msg = (\n"
    "        f'Nuevo lead:\\nNombre: {lead.name}\\nEmail: {lead.email}\\nTel: {lead.phone}\\n'\n"
    "        f'Servicio: {lead.service}\\nMensaje: {lead.message}'\n"
    "    )\n"
    "    url = f'https://api.telegram.org/bot{token}/sendMessage'\n"
    "    async with httpx.AsyncClient(timeout=10) as client:\n"
    "        try:\n"
    "            await client.post(url, json={'chat_id': chat_id, 'text': text_msg})\n"
    "        except Exception:\n"
    "            pass\n"
    "\n"
    "KEYS = {\n"
    "    'itse': ['itse','licencia','inspección','inspeccion'],\n"
    "    'pozo': ['pozo','tierra','puesta a tierra'],\n"
    "    'mant': ['mantenimiento','preventivo','correctivo'],\n"
    "    'inc':  ['incendio','incendios','alarma','detección','detector']\n"
    "}\n"
    "\n"
    "def rule_based_reply(text: str) -> str:\n"
    "    t = text.lower()\n"
    "    if any(k in t for k in KEYS['itse']):\n"
    "        return ('ITSE: pago municipal aprox. S/ 218 y gestión desde S/ 300 (referencial). '\n"
    "                'Para precisión: rubro y área en m². ¿Agendamos visita técnica sin costo?')\n"
    "    if any(k in t for k in KEYS['pozo']):\n"
    "        return ('Pozo de tierra: S/ 1,500 – 2,500 (referencial, depende del terreno). '\n"
    "                'Podemos medir resistencia y proponer solución. ¿Dirección para visita?')\n"
    "    if any(k in t for k in KEYS['mant']):\n"
    "        return ('Mantenimiento: plan a medida (preventivo/correctivo). '\n"
    "                'Cuéntame tamaño del local y equipos críticos para estimar.')\n"
    "    if any(k in t for k in KEYS['inc']):\n"
    "        return ('Contra incendios: diseño, detección y alarma según normativa. '\n"
    "                'Costo depende del área y riesgo. ¿Qué tipo de propiedad es?')\n"
    "    return 'Gracias. Déjanos nombre y número para coordinar una visita técnica.'\n"
    "\n"
    "@app.post('/api/chat', response_model=ChatOut)\n"
    "async def chat_route(payload: ChatIn):\n"
    "    user = payload.message.strip()\n"
    "    if not user:\n"
    "        raise HTTPException(status_code=400, detail='Empty message')\n"
    "    rb = rule_based_reply(user)\n"
    "    return ChatOut(reply=rb)\n"
)

RUN_LOCAL_PS1 = (
    "# Arranca backend (uvicorn) y servidor estático del frontend\n"
    "param([switch]$NoBrowser)\n"
    "$ErrorActionPreference = 'Stop'\n"
    "$Base = Split-Path -Parent $MyInvocation.MyCommand.Path\n"
    "$Backend = Join-Path $Base 'backend'\n"
    "$Frontend = Join-Path $Base 'frontend'\n"
    "$Venv = Join-Path $Backend '.venv'\n"
    "\n"
    "$Activate = Join-Path $Venv 'Scripts\\Activate.ps1'\n"
    "if (!(Test-Path $Activate)) {\n"
    "  Write-Host 'Creando venv...'\n"
    "  python -m venv $Venv\n"
    "  & \"$Venv\\Scripts\\pip.exe\" install --upgrade pip\n"
    "  & \"$Venv\\Scripts\\pip.exe\" install -r \"$Backend\\requirements.txt\"\n"
    "}\n"
    ". $Activate\n"
    "Start-Process -WindowStyle Minimized powershell -ArgumentList @('-NoExit','-Command',\"cd `\"$Backend`\"; . .\\.venv\\Scripts\\Activate.ps1; uvicorn app.main:app --host 0.0.0.0 --port 8000\")\n"
    "Start-Process -WindowStyle Minimized powershell -ArgumentList @('-NoExit','-Command',\"cd `\"$Frontend`\"; python -m http.server 8080\")\n"
    "if (-not $NoBrowser) { Start-Sleep -Seconds 2; Start-Process 'http://localhost:8080' }\n"
    "Write-Host '✅ Backend: http://127.0.0.1:8000 | Frontend: http://localhost:8080'\n"
)

RUN_LOCAL_BAT = (
    "@echo off\n"
    "setlocal\n"
    "SET BASE=%~dp0\n"
    "SET BACKEND=%BASE%backend\n"
    "SET FRONTEND=%BASE%frontend\n"
    "SET VENV=%BACKEND%\\.venv\n"
    "IF NOT EXIST \"%VENV%\\Scripts\\activate.bat\" (\n"
    "  echo Creando venv...\n"
    "  python -m venv \"%VENV%\"\n"
    "  \"%VENV%\\Scripts\\pip.exe\" install --upgrade pip\n"
    "  \"%VENV%\\Scripts\\pip.exe\" install -r \"%BACKEND%\\requirements.txt\"\n"
    ")\n"
    "start \"tesla-backend\" cmd /k \"cd /d %BACKEND% && call %VENV%\\Scripts\\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000\"\n"
    "start \"tesla-frontend\" cmd /k \"cd /d %FRONTEND% && python -m http.server 8080\"\n"
    "timeout /t 2 >NUL\n"
    "start http://localhost:8080\n"
    "echo ✅ Backend: http://127.0.0.1:8000  ^|  Frontend: http://localhost:8080\n"
    "endlocal\n"
)

STOP_LOCAL_PS1 = (
    "# Detiene procesos en puertos 8000 y 8080\n"
    "$ErrorActionPreference = 'SilentlyContinue'\n"
    "function KillByPort($port) {\n"
    "  $lines = netstat -ano | findstr LISTENING | findstr \":$port\"\n"
    "  foreach ($line in $lines) { $parts = $line -split \"\\s+\"; $pid = $parts[-1]; if ($pid -match \"^\\d+$\") { taskkill /PID $pid /F | Out-Null } }\n"
    "}\n"
    "KillByPort 8000\n"
    "KillByPort 8080\n"
    "Write-Host '🛑 Procesos locales detenidos.'\n"
)

# ====== HELPERS ======

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    # NUNCA tocamos frontend/index.html si ya existe
    if path.name == "index.html" and path.exists():
        print(f"• Manteniendo tu archivo existente: {path}")
        return
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"• Archivo creado: {path}")

def create_layout() -> None:
    ensure_dir(BASE_DIR)
    ensure_dir(FRONTEND_DIR)
    ensure_dir(BACKEND_APP)

def create_files() -> None:
    # raíz
    write_text(BASE_DIR / "docker-compose.yml", DOCKER_COMPOSE)
    # frontend (NO tocamos index.html)
    write_text(FRONTEND_DIR / "Dockerfile", FRONTEND_DOCKERFILE)
    write_text(FRONTEND_DIR / "nginx.conf", FRONTEND_NGINX)
    # backend
    write_text(BACKEND_DIR / "Dockerfile", BACKEND_DOCKERFILE)
    write_text(BACKEND_DIR / "requirements.txt", REQUIREMENTS)
    write_text(BACKEND_DIR / ".env.example", ENV_EXAMPLE)
    write_text(BACKEND_APP / "main.py", MAIN_PY)

def create_venv_and_install() -> None:
    if not VENV_DIR.exists():
        print("• Creando venv backend\\.venv ...")
        subprocess.check_call(["python", "-m", "venv", str(VENV_DIR)])
    pip = VENV_DIR / "Scripts" / "pip.exe"
    if not pip.exists():
        pip = VENV_DIR / "bin" / "pip"  # por si luego lo usas en Linux/Mac
    print("• Instalando dependencias en venv ...")
    subprocess.check_call([str(pip), "install", "--upgrade", "pip"])
    subprocess.check_call([str(pip), "install", "-r", str(BACKEND_DIR / "requirements.txt")])
    print("• venv listo.")

def write_runners() -> None:
    write_text(BASE_DIR / "run_local.ps1", RUN_LOCAL_PS1)
    write_text(BASE_DIR / "run_local.bat", RUN_LOCAL_BAT)
    write_text(BASE_DIR / "stop_local.ps1", STOP_LOCAL_PS1)

def main() -> None:
    print("== SETUP BACKEND TESLA ==")
    create_layout()
    create_files()
    write_runners()
    try:
        create_venv_and_install()
    except Exception as e:
        print(f"⚠️ No se pudo crear/instalar venv automáticamente: {e}")
        print("   Puedes hacerlo manual:")
        print(f"   python -m venv {VENV_DIR}")
        print(f"   {VENV_DIR}\\Scripts\\pip.exe install -r {BACKEND_DIR}\\requirements.txt")
    print("\n✅ Listo en:", BASE_DIR)
    print("Siguientes pasos:")
    print("  1) Si no lo hiciste, pega tu frontend/index.html (ya tienes el tuyo).")
    print("  2) cd backend && copy .env.example .env  (edita TELEGRAM y/o IA si usarás)")
    print("  3) Local sin Docker:  PowerShell -> E:\\WEB_TESLA_ITSE\\run_local.ps1")
    print("  4) Docker:            cd E:\\WEB_TESLA_ITSE && docker compose up --build")
    print("  5) Frontend local:    http://localhost:8080  | Backend: http://127.0.0.1:8000/healthz")

if __name__ == "__main__":
    main()
