# backend/server.py
# Single-file simulated WhatsApp bot + staff dashboard backend
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import sqlite3, os, re, time, json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "travel_bot.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        display_name TEXT,
        raw_message TEXT,
        intent TEXT,
        service TEXT,
        destination TEXT,
        travel_date TEXT,
        adults INTEGER DEFAULT 0,
        children INTEGER DEFAULT 0,
        infants INTEGER DEFAULT 0,
        status TEXT DEFAULT 'new', -- new, handled
        staff_reply TEXT,
        created_at TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS canned_replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intent TEXT,
        reply_text TEXT,
        created_at TEXT
    );
    """)
    conn.commit()
    conn.close()

init_db()

app = FastAPI(title="Simulated WhatsApp Bot (Demo)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ----- simple parser to extract counts, date, destination, name intent
def parse_message(text: str) -> Dict:
    t = text or ""
    res = {"intent": None, "service": None, "destination": None, "travel_date": None, "adults": 0, "children": 0, "infants": 0}
    # simple intent detection
    if re.search(r"\b(حجز|حجز طيران|تذكرة|flight|ticket)\b", t, re.I):
        res["intent"] = "booking"
        res["service"] = "flight"
    elif re.search(r"\b(flight|air|طيران)\b", t, re.I):
        res["intent"] = "booking"
        res["service"] = "flight"
    elif re.search(r"\b(فندق|hotel)\b", t, re.I):
        res["intent"] = "hotel"
        res["service"] = "hotel"
    elif re.search(r"\b(فيزا|visa)\b", t, re.I):
        res["intent"] = "visa"
        res["service"] = "visa"
    else:
        # default to inquiry
        res["intent"] = "inquiry"
    # destination keywords
    places = ["عدن","القاهرة","مصر","جدة","الرياض","دبي","عمان","amman","cairo","aden","riyadh","jeddah","dubai"]
    for p in places:
        if p.lower() in t.lower():
            res["destination"] = p
            break
    # date detection dd/mm or yyyy-mm-dd
    m = re.search(r"(\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b)", t)
    if m:
        res["travel_date"] = m.group(1)
    # counts
    ad = re.search(r"(\d+)\s*(?:بالغ|ب؟ل?غ|adult|adults)", t, re.I)
    ch = re.search(r"(\d+)\s*(?:طفل|children|child|kids)", t, re.I)
    inft = re.search(r"(\d+)\s*(?:رضيع|infant|infants|baby)", t, re.I)
    if ad: res["adults"] = max(0,int(ad.group(1)))
    if ch: res["children"] = max(0,int(ch.group(1)))
    if inft: res["infants"] = max(0,int(inft.group(1)))
    # fallback: if user wrote "2" alone maybe it's passengers count (not robust but helpful)
    if res["adults"]==0 and res["children"]==0 and res["infants"]==0:
        m2 = re.findall(r"\b(\d{1,2})\b", t)
        if m2:
            # assign first number to adults if small
            res["adults"] = int(m2[0])
    return res

# ----- DB helpers
def save_message(phone, display_name, raw_text, parsed):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("""
        INSERT INTO messages (phone, display_name, raw_message, intent, service, destination, travel_date, adults, children, infants, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (phone, display_name, raw_text, parsed.get("intent"), parsed.get("service"), parsed.get("destination"), parsed.get("travel_date"), parsed.get("adults") or 0, parsed.get("children") or 0, parsed.get("infants") or 0, now))
    conn.commit()
    mid = cur.lastrowid
    conn.close()
    return mid

def get_recent_canned(intent, within_minutes=10):
    conn = get_conn()
    cur = conn.cursor()
    cutoff = (datetime.utcnow() - timedelta(minutes=within_minutes)).isoformat()
    cur.execute("SELECT id, reply_text, created_at FROM canned_replies WHERE intent=? AND created_at>=? ORDER BY created_at DESC", (intent, cutoff))
    row = cur.fetchone()
    conn.close()
    return row

def store_canned(intent, reply_text):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("INSERT INTO canned_replies (intent, reply_text, created_at) VALUES (?, ?, ?)", (intent, reply_text, now))
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid

def apply_reply_to_messages(message_ids: List[int], reply_text: str):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    # update selected messages
    cur.executemany("UPDATE messages SET status='handled', staff_reply=?, created_at=created_at WHERE id=?", [(reply_text, mid) for mid in message_ids])
    conn.commit()
    # return count updated
    cur.execute("SELECT COUNT(*) as c FROM messages WHERE id IN ({seq})".format(seq=",".join(["?"]*len(message_ids))), message_ids)
    count = cur.fetchone()["c"]
    conn.close()
    return count

def broadcast_reply_by_intent(intent, reply_text, within_minutes=10):
    conn = get_conn()
    cur = conn.cursor()
    cutoff = (datetime.utcnow() - timedelta(minutes=within_minutes)).isoformat()
    # select messages that are new and match intent and created_at >= cutoff
    cur.execute("SELECT id FROM messages WHERE intent=? AND status='new' AND created_at>=?", (intent, cutoff))
    rows = cur.fetchall()
    ids = [r["id"] for r in rows]
    if ids:
        cur.executemany("UPDATE messages SET status='handled', staff_reply=? WHERE id=?", [(reply_text, mid) for mid in ids])
        conn.commit()
    conn.close()
    return ids

# ----- API models
class WAInput(BaseModel):
    from_number: str
    display_name: Optional[str] = None
    message: str

# ----- endpoints
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: WAInput, background_tasks: BackgroundTasks):
    parsed = parse_message(payload.message)
    mid = save_message(payload.from_number, payload.display_name or "", payload.message, parsed)

    # If there is a recent canned reply for this intent (last 10 minutes) — auto-respond
    canned = get_recent_canned(parsed.get("intent"))
    if canned:
        reply = canned["reply_text"]
        # mark this message handled and attach staff_reply
        conn = get_conn(); cur = conn.cursor()
        cur.execute("UPDATE messages SET status='handled', staff_reply=? WHERE id=?", (reply, mid))
        conn.commit(); conn.close()
        return {"status":"auto-replied", "reply": reply}

    # otherwise, return prompt for simulated chat flow (simulate step-by-step prompts)
    # We'll provide a next-question suggestion based on missing fields
    next_q = None
    # if no service chosen and intent==inquiry -> ask choose service
    if parsed.get("intent") == "inquiry":
        next_q = "أهلاً، ما نوع الخدمة التي تريد؟ اكتب رقم:\n1) حجوزات طيران\n2) حجوزات فنادق\n3) فيزا\n4) خدمات أخرى"
    elif parsed.get("service") == "flight":
        if not parsed.get("destination"):
            next_q = "أي وجهة تريد؟ (مثال: القاهرة، جدة، الرياض)"
        elif not parsed.get("travel_date"):
            next_q = "متى تاريخ السفر؟ (مثال: 20/12 أو 2025-12-30)"
        elif parsed.get("adults",0)==0:
            next_q = "كم عدد البالغين؟ (اكتب رقم)"
        else:
            next_q = "شكراً — تم تسجيل طلبك. سيقوم الموظف بالرد عليك قريباً."
    else:
        # default fallback
        next_q = "شكراً، سيتم تحويل طلبك لموظف. اذكر أي بيانات إضافية إن وجدت."

    return {"status":"received", "message_id": mid, "next": next_q, "parsed": parsed}

@app.get("/api/messages")
async def api_messages(intent: Optional[str]=None, status: Optional[str]=None, minutes:int=0):
    conn = get_conn(); cur = conn.cursor()
    q = "SELECT * FROM messages WHERE 1=1"
    params = []
    if intent:
        q += " AND intent=?"; params.append(intent)
    if status:
        q += " AND status=?"; params.append(status)
    if minutes>0:
        cutoff = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
        q += " AND created_at>=?"; params.append(cutoff)
    q += " ORDER BY created_at DESC LIMIT 200"
    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

class StaffReplyIn(BaseModel):
    message_ids: Optional[List[int]] = None
    intent: Optional[str] = None
    reply_text: str

@app.post("/api/staff/reply")
async def staff_reply(in_data: StaffReplyIn):
    # If message_ids provided: reply to them
    ids = []
    if in_data.message_ids:
        ids = in_data.message_ids
        count = apply_reply_to_messages(ids, in_data.reply_text)
    elif in_data.intent:
        # store canned and broadcast to recent messages in last 10 minutes
        store_canned(in_data.intent, in_data.reply_text)
        ids = broadcast_reply_by_intent(in_data.intent, in_data.reply_text, within_minutes=10)
        count = len(ids)
    else:
        return {"error": "provide message_ids or intent"}
    return {"status":"ok", "updated": count, "ids": ids}

@app.get("/api/canned")
async def api_canned(intent: Optional[str]=None, minutes:int=60):
    conn = get_conn(); cur = conn.cursor()
    cutoff = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
    if intent:
        cur.execute("SELECT * FROM canned_replies WHERE intent=? AND created_at>=? ORDER BY created_at DESC", (intent,cutoff))
    else:
        cur.execute("SELECT * FROM canned_replies WHERE created_at>=? ORDER BY created_at DESC", (cutoff,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/api/message/{mid}")
async def api_message(mid: int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM messages WHERE id=?", (mid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"error":"not found"}
    return dict(row)
