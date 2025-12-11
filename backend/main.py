from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from .services import save_raw_message, process_message_and_create_request, find_passengers_recent
from .sample_data import create_sample
import uvicorn
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Travel MVP Level3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WhatsAppPayload(BaseModel):
    from_number: str
    display_name: Optional[str] = None
    message: str

@app.on_event("startup")
def startup_event():
    try:
        create_sample()
    except:
        pass

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: WhatsAppPayload, background_tasks: BackgroundTasks):
    raw = save_raw_message(payload.from_number, payload.display_name, payload.message)
    background_tasks.add_task(process_message_and_create_request, raw)
    return {"status":"received", "id": raw.id}

@app.get("/api/passengers/recent")
def passengers_recent(months: int = 3):
    rows = find_passengers_recent(months=months)
    return [{"id":p.id, "full_name":p.full_name, "phone":p.phone, "email":p.email} for p in rows]

@app.get("/api/health")
def health():
    return {"status":"ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
