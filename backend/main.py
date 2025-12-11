from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from services import (
    save_raw_message,
    process_message_and_create_request,
    find_passengers_recent
)
from sample_data import create_sample
from pydantic import BaseModel
from typing import Optional


app = FastAPI(title="Travel MVP Level3")

# السماح بالاتصالات من أي مصدر
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===============================
# نماذج الإدخال
# ===============================

class Message(BaseModel):
    text: str
    phone: Optional[str] = None


# ===============================
# المسارات الأساسية
# ===============================

@app.post("/message")
async def receive_message(msg: Message, background_tasks: BackgroundTasks):
    """
    يستقبل الرسالة من المستخدم – يضيفها للسجلات – ثم يعالجها بالخلفية.
    """
    background_tasks.add_task(save_raw_message, msg.text, msg.phone)
    response = process_message_and_create_request(msg.text, msg.phone)
    return response


@app.get("/passengers/recent")
async def recent_passengers():
    """إرجاع آخر الركاب (10 ركاب مثلاً)"""
    return find_passengers_recent()


@app.post("/sample")
async def populate_sample():
    """ إنشاء بيانات تجريبية """
    create_sample()
    return {"status": "sample data created"}


# ===============================
# للتشغيل المحلي فقط
# ===============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
