# ระบบ Computer Support (bdpjsite): โครงสร้างและวิธีอัปเดต

## โครงสร้างไฟล์

```
D:\Python\bdpjsite\
├── .idea  .venv  .gitignore  db.sqlite3  manage.py  requirements.txt     (ของเดิม)
│
├── config\                         ตั้งค่าทั้งเว็บ
│   ├── settings.py                 ตั้งค่า (รายชื่อแอป, ฐานข้อมูล, ภาษาไทย, ล็อกอิน)
│   └── urls.py                     ศูนย์รวม URL: ต่อ core, servicedesk, admin, accounts
│
├── core\                           ระบบกลาง: หน้าแรก + เมนู + หน้าตาที่ทุกโมดูลใช้ร่วมกัน
│   ├── navigation.py               ★ เมนูทั้งระบบอยู่ที่ไฟล์นี้ไฟล์เดียว
│   ├── context_processors.py       ส่งเมนูไปทุกหน้า และบอกว่าเมนูไหนกำลังเปิดอยู่
│   ├── views.py / urls.py          หน้าแรก "/" (ยินดีต้อนรับ)
│   ├── templates\core\base.html    โครงหน้าเว็บ (เมนูซ้าย + เนื้อหา) ทุกหน้าใช้ร่วมกัน
│   ├── templates\core\home.html    หน้าแรก
│   ├── templates\registration\login.html   หน้าเข้าสู่ระบบ
│   └── static\core\base.css        สี ตัวอักษร เมนู ปุ่ม ตาราง ฟอร์ม
│
└── servicedesk\                    โมดูล "แจ้งปัญหาในการใช้งาน"
    ├── models.py                   ตารางข้อมูล: สาขา, หมวดปัญหา, งาน
    ├── forms.py                    ฟอร์มเพิ่ม/แก้ไขงาน
    ├── urls.py                     /servicedesk/dashboard/  และ  /servicedesk/tickets/ ...
    ├── views\
    │   ├── dashboard_views.py      หน้า "แดชบอร์ด"
    │   └── ticket_views.py         หน้า "รายการงาน" และ เพิ่ม/แก้ไข/ดู/ลบ
    ├── querystring.py              ตัวช่วยทำลิงก์ตัวกรองและเลขหน้า
    ├── utils.py                    คำนวณ KPI, จัดหมวดปัญหาอัตโนมัติ
    ├── admin.py  tests.py  apps.py
    ├── templatetags\thai.py        แสดงวันที่ พ.ศ. และเวลาที่ใช้
    ├── management\commands\import_servicedesk.py   นำเข้าข้อมูลจาก seed/Excel
    ├── seed\                       ข้อมูลเริ่มต้น
    ├── templates\servicedesk\      dashboard.html, ticket_list.html, ticket_form.html ...
    └── static\servicedesk\app.css  หน้าตาเฉพาะแดชบอร์ดและรายการงาน
```

## เมนูและ URL ในระบบ

| เมนู | หน้าที่แสดง | URL |
|---|---|---|
| หน้าแรก | ยินดีต้อนรับเข้าสู่ระบบ Computer Support | `/` |
| แจ้งปัญหาในการใช้งาน > แดชบอร์ด | แดชบอร์ด | `/servicedesk/dashboard/` |
| แจ้งปัญหาในการใช้งาน > แจ้งปัญหาการใช้งาน | รายการงาน (ค้นหา กรอง เพิ่ม แก้ไข ลบ) | `/servicedesk/tickets/` |

## วิธีอัปเดตจากเวอร์ชันก่อนหน้า

**1. ลบไฟล์เก่า 3 ไฟล์** (ถูกย้ายหรือแทนที่แล้ว) PowerShell ที่โฟลเดอร์โปรเจกต์
```
Remove-Item servicedesk\views.py, servicedesk\templates\servicedesk\base.html, servicedesk\templates\registration\login.html
```
**2. แตกไฟล์ zip ลงใน D:\Python\bdpjsite** เลือกแทนที่ไฟล์เดิม
**3. ตรวจและทดสอบ** (ไม่ต้อง makemigrations เพราะไม่ได้แก้ตารางข้อมูล)
```
python manage.py check
python manage.py test core servicedesk
python manage.py runserver
```
**4. ส่งขึ้นออนไลน์**
```
git add config core servicedesk README_SETUP.md
git status
git commit -m "Add menu layout, home page, split dashboard and ticket list"
git push
```
ใน `git status` ต้องไม่เห็น `tickets.json` และ `db.sqlite3`

## วิธีเพิ่มระบบ (โมดูล) ใหม่ในอนาคต
ตัวอย่าง: ทะเบียนอุปกรณ์ IT
1. `python manage.py startapp assets` สร้างแอปใหม่ แล้วเขียน models/views/urls ภายในแอปนั้น (ตั้ง `app_name = "assets"` ใน urls.py)
2. `config/settings.py` เพิ่ม `'assets'` ใน `INSTALLED_APPS`
3. `config/urls.py` เพิ่ม `path("assets/", include("assets.urls"))`
4. `core/navigation.py` เพิ่มเมนู เช่น `{"label": "ทะเบียนอุปกรณ์ IT", "children": [{"label": "รายการอุปกรณ์", "url_name": "assets:list"}]}`
5. ในหน้าเว็บของแอปใหม่ เขียน `{% extends "core/base.html" %}` จะได้เมนูซ้ายและหน้าตาเหมือนกันทั้งระบบ
หน้าแรกจะแสดงทางลัดของเมนูใหม่ให้อัตโนมัติ

## ความปลอดภัยของข้อมูล
`servicedesk\seed\tickets.json` มีชื่อผู้ขอและรายละเอียดงานภายใน GitHub repo เป็น Public จึงต้องไม่ push ไฟล์นี้ (ตั้งใน `.gitignore` แล้ว)
