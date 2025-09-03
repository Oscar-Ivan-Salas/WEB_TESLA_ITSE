import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import httpx
from dotenv import load_dotenv

load_dotenv()
AI_PROVIDER = os.getenv('AI_PROVIDER', 'none').lower()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DB_URL = os.getenv('DB_URL', 'sqlite:///./tesla.db')
ALLOWED_ORIGINS = [o.strip() for o in os.getenv('ALLOWED_ORIGINS', '*').split(',')]

engine = create_engine(DB_URL, connect_args={'check_same_thread': False} if DB_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

with engine.begin() as conn:
    conn.exec_driver_sql(
        '''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            service TEXT,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

app = FastAPI(title='Tesla CRM API')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'] if '*' in ALLOWED_ORIGINS else ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class LeadIn(BaseModel):
    name: str = Field(..., min_length=2)
    email: Optional[EmailStr] = None
    phone: str = Field(..., min_length=6)
    service: Optional[str] = None
    message: Optional[str] = None

class ChatIn(BaseModel):
    message: str
    use_ai: bool = True

class ChatOut(BaseModel):
    reply: str

@app.get('/healthz')
async def healthz():
    return {'ok': True}

@app.post('/api/leads')
async def create_lead(payload: LeadIn):
    if payload.name.lower().startswith('http'):
        raise HTTPException(status_code=400, detail='Invalid name')
    with engine.begin() as conn:
        conn.execute(text(
            'INSERT INTO leads(name,email,phone,service,message) '
            'VALUES(:name,:email,:phone,:service,:message)'
        ), payload.model_dump())
    await notify_telegram(payload)
    return {'ok': True}

async def notify_telegram(lead: LeadIn):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        return
    text_msg = (
        f'Nuevo lead:\nNombre: {lead.name}\nEmail: {lead.email}\nTel: {lead.phone}\n'
        f'Servicio: {lead.service}\nMensaje: {lead.message}'
    )
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(url, json={'chat_id': chat_id, 'text': text_msg})
        except Exception:
            pass

KEYS = {
    'itse': ['itse','licencia','inspección','inspeccion'],
    'pozo': ['pozo','tierra','puesta a tierra'],
    'mant': ['mantenimiento','preventivo','correctivo'],
    'inc':  ['incendio','incendios','alarma','detección','detector']
}

def rule_based_reply(text: str) -> str:
    t = text.lower()
    if any(k in t for k in KEYS['itse']):
        return ('ITSE: pago municipal aprox. S/ 218 y gestión desde S/ 300 (referencial). '
                'Para precisión: rubro y área en m². ¿Agendamos visita técnica sin costo?')
    if any(k in t for k in KEYS['pozo']):
        return ('Pozo de tierra: S/ 1,500 – 2,500 (referencial, depende del terreno). '
                'Podemos medir resistencia y proponer solución. ¿Dirección para visita?')
    if any(k in t for k in KEYS['mant']):
        return ('Mantenimiento: plan a medida (preventivo/correctivo). '
                'Cuéntame tamaño del local y equipos críticos para estimar.')
    if any(k in t for k in KEYS['inc']):
        return ('Contra incendios: diseño, detección y alarma según normativa. '
                'Costo depende del área y riesgo. ¿Qué tipo de propiedad es?')
    return 'Gracias. Déjanos nombre y número para coordinar una visita técnica.'

@app.post('/api/chat', response_model=ChatOut)
async def chat_route(payload: ChatIn):
    user = payload.message.strip()
    if not user:
        raise HTTPException(status_code=400, detail='Empty message')
    rb = rule_based_reply(user)
    return ChatOut(reply=rb)
