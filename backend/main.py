from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from services import save_raw_message, process_message_and_create_request, find_passengers_recent
from sample_data import create_sample
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

class MessageIn(BaseModel):
    text: str
    phone: Optional[str] = None

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/webhook/whatsapp")
async def webhook_whatsapp(payload: MessageIn, background_tasks: BackgroundTasks):
    background_tasks.add_task(save_raw_message, payload.text, payload.phone)
    result = process_message_and_create_request(payload.text, payload.phone)
    return {"status": "received", "result": result}

@app.get("/api/passengers/recent")
async def passengers_recent():
    return find_passengers_recent()

@app.post("/api/sample")
async def make_sample():
    create_sample()
    return {"status": "sample created"}
