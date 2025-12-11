import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";

/*
  ملاحظة مهمة:
  إذا نُشِر الـ backend على Render سيكون الرابط مختلف.
  لتسهيل الإعداد نستخدم متغيّر البيئة REACT_APP_API_BASE
  إذا لم يكن موجودًا سيستخدم localhost (لتجربة محلية).
*/
const API_BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000";

function RequestsView(){
  const [log, setLog] = useState([]);
  useEffect(()=>{
    // أمثلة عرضية — لا تعتمد على الAPI هنا حتى يعمل backend
    setLog([
      {id:1, from:"+967771234567", name:"Ammar Yasser", message:"السلام عليكم اريد تذكرة عدن الى القاهرة 25/12"},
      {id:2, from:"+967771000111", name:"Sara", message:"Hi I need flight Aden to Cairo 2025-12-25"}
    ]);
  },[]);
  return (
    <div>
      <p>لاختبار النظام: أرسل POST إلى <code>{API_BASE}/webhook/whatsapp</code>. أمثلة اختبارية:</p>
      <ul>
        <li>السلام عليكم اريد تذكرة عدن الى القاهرة 25/12</li>
        <li>Hi I need flight Aden to Cairo 2025-12-25</li>
      </ul>

      <div style={{marginTop:10}}>
        {log.map(r => (
          <div key={r.id} style={{border:'1px solid #ddd', padding:8, marginBottom:8}}>
            <b>{r.name}</b> — {r.from}
            <div style={{marginTop:6}}>{r.message}</div>
            <div style={{marginTop:6}}>
              <button disabled style={{marginRight:6}}>اجمع نفس الطلب (محاكاة)</button>
              <button disabled>ارسل رد موحّد (محاكاة)</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MediaLibrary(){
  return (
    <div>
      <p>مولّد ميديا تجريبي (قوالب):</p>
      <div style={{border:'1px dashed #aaa', padding:10}}>
        <p>اختر وجهة، ضع نص، واضغط "Generate" (محاكاة)</p>
        <button disabled>Generate 3 Images</button>
        <button disabled style={{marginLeft:8}}>Generate 1 Video</button>
      </div>
      <p style={{marginTop:12}}>عرض الصور / الفيديوهات سيظهر هنا بعد التوليد.</p>
    </div>
  );
}

function Dashboard(){
  const [passengers, setPassengers] = useState([]);

  useEffect(()=>{
    axios.get(`${API_BASE}/api/passengers/recent?months=3`)
      .then(res => setPassengers(res.data))
      .catch(err => {
        console.error(err);
        setPassengers([]);
      });
  },[]);

  return (
    <div style={{padding:16}}>
      <section style={{marginBottom: 20}}>
        <h3>المسافرون خلال آخر 3 أشهر</h3>
        <table style={{width:'100%', borderCollapse:'collapse'}}>
          <thead>
            <tr style={{background:'#eee'}}>
              <th style={{padding:6}}>الاسم</th><th style={{padding:6}}>الهاتف</th><th style={{padding:6}}>البريد</th>
            </tr>
          </thead>
          <tbody>
            {passengers.map(p => (
              <tr key={p.id}>
                <td style={{padding:6}}>{p.full_name}</td>
                <td style={{padding:6}}>{p.phone}</td>
                <td style={{padding:6}}>{p.email}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section style={{display:'flex', gap:20, flexWrap:'wrap'}}>
        <div style={{flex:1, minWidth:300}}>
          <h3>الطلبات الواردة (محاكاة واتساب)</h3>
          <RequestsView />
        </div>
        <div style={{width:360}}>
          <h3>مكتبة الميديا (مولّد بسيط)</h3>
          <MediaLibrary />
        </div>
      </section>
    </div>
  );
}

/* App component + render */
function App(){
  return (
    <div style={{fontFamily: 'Arial, sans-serif', direction: 'rtl'}}>
      <header style={{padding: '10px', backgroundColor:'#0b5ed7', color:'#fff'}}>
        <h2>نظام سفريات - النسخة التجريبية</h2>
      </header>
      <main>
        <Dashboard />
      </main>
    </div>
  );
}

const container = document.getElementById("root");
const root = createRoot(container);
root.render(<App />);
