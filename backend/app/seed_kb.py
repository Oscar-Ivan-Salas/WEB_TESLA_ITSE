# -*- coding: utf-8 -*-
from pathlib import Path
import sqlite3

DB = Path(__file__).resolve().parents[1] / "tesla.db"

rows = [
    ("itse-basico", "Requisitos ITSE básicos",
     "Para riesgo bajo: planos simples, certificación de instalaciones eléctricas y extintor acorde al metraje.",
     "itse, requisitos, riesgo bajo"),
    ("itse-cocinas", "ITSE para restaurantes/cocinas",
     "Cocinas comerciales suelen ser riesgo medio: considerar extintores clase K, detectores y rutas de evacuación.",
     "itse, restaurante, riesgo medio, cocina, clase K"),
    ("pozo-tierra", "Puesta a tierra",
     "La resistencia recomendada depende de la normativa; se mide con telurímetro. Si es alta, se mejora con tratamiento.",
     "pozo, tierra, resistencia, cne"),
    ("incendios-deteccion", "Sistemas de detección",
     "Se diseñan según área y uso: detectores, sirenas, pulsadores, panel de alarma y señalización.",
     "incendio, detección, alarma, panel"),
]

con = sqlite3.connect(str(DB))
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS kb_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE,
    title TEXT,
    body TEXT,
    tags TEXT
)""")
for slug, title, body, tags in rows:
    try:
        cur.execute("INSERT INTO kb_articles(slug,title,body,tags) VALUES(?,?,?,?)",
                    (slug, title, body, tags))
    except sqlite3.IntegrityError:
        pass
con.commit()
con.close()
print("KB cargada ✔")
