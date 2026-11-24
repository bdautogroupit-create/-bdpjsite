# อัปเดตโปรเจกต์ bdpjsite: เพิ่มแอป IT Service Desk

## โครงสร้างไฟล์ (เหมือนในโฟลเดอร์ D:\Python\bdpjsite ของคุณ)

```
D:\Python\bdpjsite\
├── .idea\                     (ของเดิม ไม่ต้องแตะ)
├── .venv\                     (ของเดิม)
├── .gitignore                 (ของเดิม)
├── db.sqlite3                 (ของเดิม ใช้ตอนทดสอบในเครื่อง)
├── manage.py                  (ของเดิม)
├── requirements.txt           (ของเดิม ไม่ต้องแก้)
│
├── config\
│   ├── settings.py            ← แทนที่ไฟล์เดิม (ตั้งค่าไทย, ล็อกอิน, เพิ่มแอป)
│   └── urls.py                ← แก้เอง เพิ่ม 2 บรรทัด (ดูขั้นที่ 2)
│
└── servicedesk\               ← โฟลเดอร์ใหม่ทั้งหมด
    ├── models.py              ตารางข้อมูล: สาขา, หมวดปัญหา, งาน
    ├── views.py               ตรรกะแต่ละหน้า: dashboard และเพิ่ม/แก้ไข/ดู/ลบงาน
    ├── urls.py                กำหนด URL ของแอป
    ├── forms.py               ฟอร์มเพิ่ม/แก้ไขงาน
    ├── admin.py               หน้า /admin
    ├── utils.py               ฟังก์ชันคำนวณ KPI และจัดหมวดปัญหา
    ├── apps.py                ตั้งชื่อแอป
    ├── tests.py               ชุดทดสอบอัตโนมัติ
    ├── templatetags\thai.py   แสดงวันที่ พ.ศ. และเวลาที่ใช้
    ├── management\commands\import_servicedesk.py   คำสั่งนำเข้าข้อมูล
    ├── seed\                  ข้อมูลเริ่มต้น (สาขา 12 แห่ง + งาน 21 รายการ)
    ├── templates\             หน้าเว็บ (HTML)
    └── static\servicedesk\app.css   หน้าตา (สี, ตัวอักษร)
```

## วิธีติดตั้ง

**1. แตกไฟล์ zip ลงใน D:\Python\bdpjsite โดยตรง** (ไม่ใช่โฟลเดอร์ย่อย) เมื่อ Windows ถามว่าจะแทนที่ `settings.py` ให้เลือกแทนที่

**2. แก้ `config\urls.py`** เพิ่ม `include` ในบรรทัด import และ 2 บรรทัดใน `urlpatterns`
```python
from django.urls import include, path

urlpatterns = [
    # ... ของเดิมคงไว้ ...
    path("accounts/", include("django.contrib.auth.urls")),
    path("servicedesk/", include("servicedesk.urls")),
]
```

**3. สร้างตารางใน Neon** (PowerShell ใน PyCharm Terminal)
```
$env:DATABASE_URL = "postgresql://...neon.tech/...?sslmode=require"
python manage.py makemigrations servicedesk
python manage.py migrate
python manage.py import_servicedesk
python manage.py createsuperuser
```
- ต้อง commit โฟลเดอร์ `servicedesk\migrations\` ขึ้น GitHub ด้วย
- ข้อมูลเดือนใหม่: `pip install openpyxl` (ติดตั้งครั้งเดียว ใช้เฉพาะในเครื่องคุณ) แล้วรัน `python manage.py import_servicedesk --excel Service_Desk.xlsx` รันซ้ำได้ ไม่สร้างรายการซ้ำ

**4. ทดสอบในเครื่องก่อน**
```
python manage.py test servicedesk
python manage.py runserver
```
เปิด http://127.0.0.1:8000/servicedesk/

**5. Deploy บน Render**
- Build Command: `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate`
- Environment: `DEBUG` = `False`, `SECRET_KEY` = ค่าสุ่มใหม่, `DATABASE_URL` = ของ Neon (ตั้งไว้แล้ว)
- `git add . && git commit && git push` Render จะ deploy เอง (แพลนฟรี ครั้งแรกหลังไม่มีคนใช้จะโหลดช้า 30-60 วินาที)

**6. สิทธิ์ผู้ใช้** เข้า `/admin/` สร้างกลุ่ม เช่น `IT Support` (add/change/delete/view งาน) และ `Executive` (view อย่างเดียว) ผู้ที่ไม่มีสิทธิ์จะไม่เห็นปุ่มเพิ่ม/แก้ไข/ลบ ทุกหน้าต้องล็อกอินก่อน

## ความปลอดภัยของข้อมูล
`servicedesk\seed\tickets.json` มีชื่อผู้ขอและรายละเอียดงานภายใน ถ้า GitHub repo เป็น **public** อย่า push ไฟล์นี้ ให้ตั้ง repo เป็น private หรือลบไฟล์นี้หลังนำเข้าเสร็จ
