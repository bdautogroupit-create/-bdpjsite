# ระบบ Computer Support (bdpjsite): โครงสร้างและวิธีอัปเดต

## โครงสร้างไฟล์ (มีแอปเดียวคือ servicedesk)

```
D:\Python\bdpjsite\
├── .idea  .venv  .gitignore  db.sqlite3  manage.py  requirements.txt     (ของเดิม)
│
├── config\
│   ├── settings.py                 ตั้งค่า (รายชื่อแอป, ฐานข้อมูล, ภาษาไทย, ล็อกอิน)
│   └── urls.py                     ศูนย์รวม URL (admin, ล็อกอิน, servicedesk)
│
└── servicedesk\
    ├── models.py                   ตารางข้อมูล: สาขา, หมวดปัญหา, งาน
    ├── views.py                    ★ ตรรกะของทุกหน้า (หน้าแรก, แดชบอร์ด, รายการงาน, เพิ่ม/แก้ไข/ดู/ลบ)
    ├── urls.py                     กำหนด URL ของแต่ละหน้า
    ├── forms.py                    ฟอร์มเพิ่ม/แก้ไขงาน
    ├── admin.py                    หน้า /admin
    ├── utils.py                    คำนวณ KPI และจัดหมวดปัญหาอัตโนมัติ
    ├── exports.py                  สร้างไฟล์ Excel สำหรับปุ่ม "ส่งออก Excel"
    ├── tests.py                    ชุดทดสอบอัตโนมัติ
    ├── templatetags\thai.py        แสดงวันที่ พ.ศ. และเวลาที่ใช้
    ├── management\commands\import_servicedesk.py   นำเข้าสาขา/งานจาก Excel
    ├── templates\
    │   ├── servicedesk\
    │   │   ├── base.html           ★ โครงหน้าเว็บ + เมนูซ้าย (แก้เมนูที่นี่)
    │   │   ├── home.html           หน้าแรก
    │   │   ├── dashboard.html      หน้าแดชบอร์ด
    │   │   ├── ticket_list.html    หน้ารายการงาน
    │   │   └── ticket_form.html / ticket_detail.html / ticket_confirm_delete.html / _field.html
    │   └── registration\login.html หน้าเข้าสู่ระบบ
    └── static\servicedesk\app.css  หน้าตาทั้งระบบ (ไฟล์เดียว)
```

## เมนูและ URL

| เมนู | หน้าที่แสดง | URL |
|---|---|---|
| หน้าแรก | ยินดีต้อนรับเข้าสู่ระบบ Computer Support | `/` |
| แจ้งปัญหาในการใช้งาน > แดชบอร์ด | แดชบอร์ด | `/dashboard/` |
| แจ้งปัญหาในการใช้งาน > แจ้งปัญหาการใช้งาน | รายการงาน | `/tickets/` |
| (ปุ่ม ส่งออก Excel ในหน้ารายการงาน) | ดาวน์โหลดไฟล์ Excel ของรายการที่กรองอยู่ | `/tickets/export/` |

อยากเพิ่ม/แก้ไข/ลบเมนู: เปิด `servicedesk\templates\servicedesk\base.html` แล้วแก้ในส่วน `<nav>` (มีคอมเมนต์กำกับ)

## วิธีอัปเดต (เอาแอป core ออก กลับมาใช้แอปเดียว)

**1. ลบของเก่าก่อน** (ต้องทำก่อนแตกไฟล์) PowerShell ที่โฟลเดอร์โปรเจกต์
```
Remove-Item -Recurse -Force core, servicedesk\views, servicedesk\querystring.py
```
**2. แตกไฟล์ zip ลงใน D:\Python\bdpjsite** เลือกแทนที่ไฟล์เดิม
**3. ตรวจและทดสอบ** (ไม่ต้อง makemigrations เพราะไม่ได้แก้ตารางข้อมูล)
```
python manage.py check
python manage.py test servicedesk
python manage.py runserver
```
**4. ส่งขึ้นออนไลน์**
```
git add -A config servicedesk README_SETUP.md
git status
git commit -m "Remove core app; keep single servicedesk app with menu"
git push
```
ใน `git status` ควรเห็นไฟล์ในโฟลเดอร์ `core` ถูกลบ (deleted) และต้องไม่เห็น `db.sqlite3`

## ปุ่มส่งออก Excel
ในหน้ารายการงาน กรองหรือค้นหาตามต้องการ แล้วกดปุ่ม **ส่งออก Excel** จะได้ไฟล์ `.xlsx` ของ **ทุกรายการที่กรองอยู่** (ไม่ใช่แค่หน้าที่เห็น) มี 2 ชีต
- **รายการงาน**: ทุกคอลัมน์ รวมวันที่/เวลาเปิด-ปิด วันที่เป็น พ.ศ. และเวลาที่ใช้ทั้งแบบอ่านง่าย (เช่น 1 ชม. 6 นาที) และเป็นตัวเลขนาทีสำหรับคำนวณ
- **สรุป**: เงื่อนไขที่กรอง เวลาที่ส่งออก ผู้ส่งออก และตัวเลขสรุป (จำนวนงาน ค่ากลาง ค่าเฉลี่ย ปิดภายใน 30 นาที)

ผู้ใช้ทุกคนที่ล็อกอินส่งออกได้ (รวมผู้ที่ดูอย่างเดียว) ต้องมี `openpyxl` ใน `requirements.txt` เพื่อให้ Render ติดตั้งให้ (เปิดไฟล์ใน PyCharm แล้วเพิ่มบรรทัด `openpyxl` ต่อท้าย)

## ข้อมูลในระบบมาจากไหน
ไม่มีข้อมูลเริ่มต้นในโค้ด ข้อมูลทั้งหมดอยู่ในฐานข้อมูล (Neon บนเว็บจริง, `db.sqlite3` ในเครื่อง)
- **งาน**: ปุ่ม "เพิ่มงานใหม่" ในหน้ารายการงาน
- **สาขาและหมวดปัญหา**: เข้า `/admin/` เพิ่ม/แก้ไขในเมนู "สาขา" และ "หมวดปัญหา"
- **จาก Excel** (ติดตั้ง `pip install openpyxl` ครั้งเดียว):
  ```
  python manage.py import_servicedesk --branches-excel สาขา.xlsx
  python manage.py import_servicedesk --excel Service_Desk.xlsx
  ```

## ความปลอดภัยของข้อมูล
GitHub repo เป็น Public ข้อมูลงานจริงอยู่ในฐานข้อมูล ไม่อยู่ใน repo อย่านำไฟล์ Excel ที่มีข้อมูลจริง (ชื่อผู้ขอ รายละเอียดงาน) ขึ้น GitHub และอย่า commit ไฟล์ `.env`
