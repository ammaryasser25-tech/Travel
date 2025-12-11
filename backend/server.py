# backend/server.py
# Single-file backend for Travel MVP (FastAPI + SQLite)
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import re
import logging
import sqlite3
import os

# --- logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("travel_singlefile")

# --- DB (lightweight sqlite using sqlite3 for single-file simplicity)
DB_PATH = os.path.join(os.path.dirname(__file__), "travel_singlefile.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS passengers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_message TEXT,
        phone TEXT,
        name TEXT,
        destination TEXT,
        date TEXT,
        created_at TEXT
    );
    """)
    conn.commit()
    conn.close()

init_db()

# --- simple parser
def parse_message(text: str) -> Dict:
    res = {"name": None, "destination": None, "date": None}
    # date pattern dd/mm or dd-mm or yyyy-mm-dd
    m = re.search(r"(\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b)", text)
    if m:
        res["date"] = m.group(1)
    places = ["عدن", "القاهرة", "مصر", "جدة", "الرياض", "دبي", "الدوحة", "cairo", "aden", "riyadh"]
    for p in places:
        if p.lower() in text.lower():
            res["destination"] = p
            break
    name_m = re.search(r"(?:اسمي|أنا|my name is|mr\.|ms\.)\s*([A-Za-z\u0600-\u06FF ]{2,40})", text, re.IGNORECASE)
    if name_m:
        res["name"] = name_m.group(1).strip()
    if not res["name"]:
        words = re.split(r"\s+", text.strip())
        if len(words) <= 4 and len(words) > 0:
            res["name"] = " ".join(words[:2])
    return res

# --- services
def save_message_raw(raw: str, phone: Optional[str]=None):
    conn = get_conn()
    cur = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    cur.execute("INSERT INTO passengers (raw_message, phone, created_at) VALUES (?, ?, ?);", (raw, phone, created_at))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid

def create_passenger_from_message(raw: str, phone: Optional[str]=None):
    parsed = parse_message(raw)
    conn = get_conn()
    cur = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    cur.execute("""
        INSERT INTO passengers (raw_message, phone, name, destination, date, created_at)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (raw, phone, parsed.get("name"), parsed.get("destination"), parsed.get("date"), created_at))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid, parsed

def get_recent_passengers(months: int = 3):
    cutoff = datetime.utcnow() - timedelta(days=30*months)
    cutoff_iso = cutoff.isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, raw_message, phone, name, destination, date, created_at FROM passengers WHERE created_at >= ? ORDER BY id DESC LIMIT 100;", (cutoff_iso,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def insert_sample_data():
    conn = get_conn()
    cur = conn.cursor()
    samples = [
        ("اسمي احمد واريد حجز من عدن الى القاهرة 20/12", "+967771234567", "احمد", "القاهرة", "20/12"),
        ("Ammar flight to Cairo 2025-12-30", "+967771000111", "Ammar", "Cairo", "2025-12-30"),
        ("My name is Sara. Trip to Riyadh 05/01", "+967770000222", "Sara", "الرياض", "05/01"),
    ]
    now = datetime.utcnow().isoformat()
    for raw, phone, name, dest, date in samples:
        cur.execute("INSERT INTO passengers (raw_message, phone, name, destination, date, created_at) VALUES (?, ?, ?, ?, ?, ?);", (raw, phone, name, dest, date, now))
    conn.commit()
    conn.close()

# --- FastAPI app
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
app = FastAPI(title="Travel Single-File Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageIn(BaseModel):
    text: str
    phone: Optional[str] = None

@app.on_event("startup")
def on_startup():
    logger.info("Starting server (single-file).")
    init_db()
    # insert_sample_data()  # uncomment if you want initial data automatically

@app.get("/")
def root():
    return {"status":"alive", "note":"use /api/health and /api/passengers/recent"}

@app.get("/api/health")
def health():
    return {"status":"ok"}

@app.post("/webhook/whatsapp")
def webhook_whatsapp(payload: MessageIn, background_tasks: BackgroundTasks):
    # save raw quickly, then process
    rowid = save_message_raw(payload.text, payload.phone)
    background_tasks.add_task(create_passenger_from_message, payload.text, payload.phone)
    return {"status":"received", "raw_id": rowid}

@app.get("/api/passengers/recent")
def passengers_recent(months: int = 3):
    return get_recent_passengers(months=months)

@app.post("/api/sample")
def sample():
    insert_sample_data()
    return {"status":"sample inserted"}
