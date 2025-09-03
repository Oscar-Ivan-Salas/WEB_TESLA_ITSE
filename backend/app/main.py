# -*- coding: utf-8 -*-
import os, re
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import httpx
from dotenv import load_dotenv

# ==== Cargar secretos desde E:\WEB_TESLA_ITSE\secrets\.env ====
BASE_DIR = Path(__file__).resolve().parents[2]  # ...\WEB_TESLA_ITSE
load_dotenv(BASE_DIR / "secrets" / ".env")

AI_PROVIDER = os.getenv("AI_PROVIDER", "none").lower()  # openai|gemini|anthropic|none (hoy: none)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_URL = os.getenv("DB_URL", "sqlite:///./tesla.db")
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]

engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==== Esquema mínimo: leads + kb (conocimiento) ====
with engine.begin() as conn:
    conn.exec_driver_sql("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        service TEXT,
        message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.exec_driver_sql("""
    CREATE TABLE IF NOT EXISTS kb_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE,
        title TEXT,
        body TEXT,
        tags TEXT
    )
    """)

# ==== FastAPI + CORS ====
app = FastAPI(title="Tesla CRM API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in ALLOWED_ORIGINS else ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== Modelos ====
class LeadIn(BaseModel):
    name: str = Field(..., min_length=2)
    email: Optional[EmailStr] = None
    phone: str = Field(..., min_length=6)
    service: Optional[str] = None
    message: Optional[str] = None

class ChatIn(BaseModel):
    message: str
    use_ai: bool = True  # hoy usa “IA ligera” (reglas + BD). Futuro: AI_PROVIDER != none.

class ChatOut(BaseModel):
    reply: str
    lead_created: bool = False

# ==== Utilidades ====
WHATSAPP_HINT = "Si prefieres, podemos continuar por WhatsApp: +51 906 315 961."
APPOINTMENT_QUESTION = "¿Agendamos una visita técnica gratuita para evaluar en sitio?"

RUBROS = {
    "restaurante": ["restaurante", "pollería", "cevichería", "comida", "cocina"],
    "tienda": ["tienda", "boutique", "bodega", "comercial"],
    "oficina": ["oficina", "estudio", "consultorio"],
    "taller": ["taller", "mecánico", "metal", "soldadura"],
    "hotel": ["hotel", "hostal", "hospedaje"],
}
SERVICES = {
    "itse": ["itse", "licencia", "inspección", "inspeccion", "edificaciones"],
    "pozo": ["pozo", "tierra", "puesta a tierra"],
    "mant": ["mantenimiento", "preventivo", "correctivo", "tableros"],
    "inc":  ["incendio", "incendios", "alarma", "detección", "detector", "rociadores"],
}

def detect_service(text: str) -> Optional[str]:
    t = text.lower()
    for key, words in SERVICES.items():
        if any(w in t for w in words):
            return key
    return None

def detect_rubro(text: str) -> Optional[str]:
    t = text.lower()
    for rubro, words in RUBROS.items():
        if any(w in t for w in words):
            return rubro
    return None

def extract_area_m2(text: str) -> Optional[int]:
    # Busca números + m2/m²
    m = re.search(r"(\d{2,5})\s*(m2|m²)", text.lower())
    if m:
        try:
            return int(m.group(1))
        except:
            return None
    return None

def classify_risk(rubro: Optional[str], area_m2: Optional[int]) -> str:
    # Regla simple: área + rubro “cocina” elevan riesgo
    if area_m2 is None and rubro is None:
        return "indeterminado"
    if area_m2 and area_m2 >= 300:
        return "ALTO"
    if rubro in ["restaurante", "taller", "hotel"]:
        return "MEDIO" if (area_m2 is None or area_m2 < 300) else "ALTO"
    if area_m2 and area_m2 >= 120:
        return "MEDIO"
    return "BAJO"

async def notify_telegram(lead: LeadIn):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    text_msg = (
        f"Nuevo lead:\nNombre: {lead.name}\nEmail: {lead.email}\nTel: {lead.phone}\n"
        f"Servicio: {lead.service}\nMensaje: {lead.message}"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(url, json={"chat_id": chat_id, "text": text_msg})
        except Exception:
            pass

def kb_search(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    # LIKE simple sobre title/body/tags
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT id, slug, title, body, tags
                FROM kb_articles
                WHERE title LIKE :q OR body LIKE :q OR tags LIKE :q
                ORDER BY id DESC
                LIMIT :lim
            """),
            {"q": f"%{query}%", "lim": limit}
        ).mappings().all()
    return [dict(r) for r in rows]

def format_kb_snippet(items: List[Dict[str, Any]]) -> str:
    if not items:
        return ""
    out = []
    for it in items:
        out.append(f"• {it['title']}: {it['body'][:140]}{'…' if len(it['body'])>140 else ''}")
    return "\n".join(out)

def referential_price(service: str, risk: str) -> str:
    if service == "itse":
        base = "Pago municipal aprox. S/ 218 y gestión desde S/ 300"
        if risk == "ALTO": return base + " (para alto riesgo usualmente desde S/ 600)."
        if risk == "MEDIO": return base + " (riesgo medio usualmente desde S/ 450)."
        return base + " (riesgo bajo)."
    if service == "pozo":
        return "Pozo de tierra: S/ 1,500 – 2,500 (depende del terreno y medición de resistencia)."
    if service == "mant":
        return "Mantenimiento: plan a medida (preventivo/correctivo). Requiere conocer equipos y periodicidad."
    if service == "inc":
        return "Contra incendios: diseño/detección/alarma según normativa. Costo depende del área y riesgo."
    return "Puedo ayudarte con ITSE, Pozo de Tierra, Mantenimiento y Sistemas Contra Incendios."

def build_reply(user_text: str) -> Dict[str, Any]:
    svc = detect_service(user_text)
    rubro = detect_rubro(user_text)
    area = extract_area_m2(user_text)
    risk = classify_risk(rubro, area)

    kb_ctx = kb_search(user_text, limit=2)
    kb_txt = format_kb_snippet(kb_ctx)

    if svc == "itse":
        msg = (
            f"{referential_price('itse', risk)} "
            f"{'(rubro: ' + rubro + ') ' if rubro else ''}"
            f"{'(área: ' + str(area) + ' m²) ' if area else ''}"
            f"Riesgo estimado: {risk}. {APPOINTMENT_QUESTION} {WHATSAPP_HINT}"
        )
    elif svc == "pozo":
        msg = f"{referential_price('pozo', risk)} {APPOINTMENT_QUESTION} {WHATSAPP_HINT}"
    elif svc == "mant":
        msg = f"{referential_price('mant', risk)} ¿Qué equipos críticos tienes y qué horario operativo manejas? {APPOINTMENT_QUESTION}"
    elif svc == "inc":
        msg = f"{referential_price('inc', risk)} ¿Es comercio, industria u oficina? ¿Aprox. cuántos m²? {APPOINTMENT_QUESTION}"
    else:
        msg = ("Puedo ayudarte con ITSE, Pozo de Tierra, Mantenimiento y Sistemas Contra Incendios. "
               "Cuéntame el rubro de tu negocio y área aproximada en m² para darte un estimado. "
               f"{APPOINTMENT_QUESTION}")

    if kb_txt:
        msg += "\n\nInformación útil:\n" + kb_txt
    return {"reply": msg, "lead_created": False}

def try_extract_phone(text_: str) -> Optional[str]:
    digits = re.sub(r"\D", "", text_)
    # Números peruanos típicos: 9 dígitos móviles; permitir +51 prefijo
    if len(digits) >= 9:
        # devolver últimos 9-11
        return digits[-11:]
    return None

# ==== ENDPOINTS ====
@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.post("/api/leads")
async def create_lead(payload: LeadIn):
    if payload.name.lower().startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid name")
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO leads(name,email,phone,service,message)
            VALUES(:name,:email,:phone,:service,:message)
            """),
            payload.model_dump()
        )
    await notify_telegram(payload)
    return {"ok": True}

@app.post("/api/chat", response_model=ChatOut)
async def chat_route(payload: ChatIn):
    user = payload.message.strip()
    if not user:
        raise HTTPException(status_code=400, detail="Empty message")

    # 1) IA ligera (reglas + BD + clasificador simple ya embebido)
    out = build_reply(user)

    # 2) Si el usuario deja teléfono o dice "agendar", guardamos lead básico
    lead_created = False
    wants_appointment = any(w in user.lower() for w in ["agendar", "visita", "llámame", "llamame", "cítame", "cita"])
    candidate_phone = try_extract_phone(user)
    if wants_appointment or candidate_phone:
        lead = LeadIn(
            name="Chat Website",
            email=None,
            phone=candidate_phone or "000000000",
            service=detect_service(user) or "consulta",
            message=user[:500]
        )
        with engine.begin() as conn:
            conn.execute(
                text("""
                INSERT INTO leads(name,email,phone,service,message)
                VALUES(:name,:email,:phone,:service,:message)
                """),
                lead.model_dump()
            )
        await notify_telegram(lead)
        lead_created = True

    return ChatOut(reply=out["reply"], lead_created=lead_created)

# Métricas simples para “dashboard” (puedes reemplazar por datos reales)
@app.get("/api/metrics")
async def metrics():
    # Ejemplo: proporciones simuladas o basadas en conteos de KB/leads
    with engine.begin() as conn:
        leads_total = conn.execute(text("SELECT COUNT(*) c FROM leads")).scalar() or 0
    # Mantén escalas 0–100
    base = 50 + min(leads_total, 50)
    return {"itse": min(base, 90), "pozo": min(40 + leads_total, 80), "mant": 90, "inc": 50}
