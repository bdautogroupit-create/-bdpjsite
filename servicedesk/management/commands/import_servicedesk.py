# ไฟล์นี้ทำอะไร: คำสั่งนำเข้าสาขาและงานจากไฟล์ Excel (ไม่มีข้อมูลเริ่มต้นในโค้ด ต้องระบุไฟล์เอง)
"""นำเข้าข้อมูลจาก Excel (รันซ้ำได้ ไม่สร้างรายการซ้ำ)

  python manage.py import_servicedesk --branches-excel สาขา.xlsx
  python manage.py import_servicedesk --excel Service_Desk.xlsx
  python manage.py import_servicedesk --branches-excel สาขา.xlsx --excel Service_Desk.xlsx

งานที่ซ้ำ = สาขา, วันที่เปิด, เวลาที่เปิด และเรื่อง เหมือนกัน จะถูกข้าม
ต้องติดตั้ง openpyxl ก่อน (pip install openpyxl) ใช้เฉพาะคำสั่งนี้
"""
import re
from datetime import date, datetime, time

from django.core.management.base import BaseCommand, CommandError

from servicedesk.models import Branch, Category, Ticket
from servicedesk.utils import DEFAULT_CATEGORIES, SHORT_NAMES, guess_category


def to_date(v):
    if isinstance(v, datetime):
        v = v.date()
    if isinstance(v, str):
        m = re.match(r"^\s*(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})\s*$", v)
        if not m:
            return date.fromisoformat(v.strip())
        v = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    if v.year > 2400:  # ปี พ.ศ. -> ค.ศ.
        v = v.replace(year=v.year - 543)
    return v


def to_time(v):
    if v in (None, ""):
        return None
    if isinstance(v, datetime):
        return v.time().replace(second=0, microsecond=0)
    if isinstance(v, time):
        return v.replace(second=0, microsecond=0)
    h, m = str(v).strip().split(":")[:2]
    return time(int(h), int(m))


def read_excel(path, first_header):
    """อ่านแถวข้อมูลของ Excel โดยหาแถวหัวตารางที่ช่องแรกตรงกับ first_header"""
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise CommandError("ยังไม่ได้ติดตั้ง openpyxl ให้รัน: pip install openpyxl")
    rows = list(load_workbook(path, data_only=True).active.iter_rows(values_only=True))
    start = next((i for i, r in enumerate(rows) if r and r[0] == first_header), None)
    if start is None:
        raise CommandError(f"ไม่พบแถวหัวตารางที่ขึ้นต้นด้วย '{first_header}' ในไฟล์ {path}")
    header = [str(h).strip() if h is not None else "" for h in rows[start]]
    for r in rows[start + 1:]:
        if r and any(v not in (None, "") for v in r):
            yield dict(zip(header, r))


class Command(BaseCommand):
    help = "นำเข้าสาขาและงาน Service Desk จากไฟล์ Excel (รันซ้ำได้)"

    def add_arguments(self, parser):
        parser.add_argument("--branches-excel", help="สาขา.xlsx (คอลัมน์: id, DealerName)")
        parser.add_argument("--excel", help="Service_Desk.xlsx (แถวหัวตารางขึ้นต้นด้วย 'ลำดับ')")

    def handle(self, *args, **opts):
        if not opts["excel"] and not opts["branches_excel"]:
            raise CommandError("ต้องระบุไฟล์อย่างน้อยหนึ่งไฟล์ เช่น --excel Service_Desk.xlsx หรือ --branches-excel สาขา.xlsx")

        for name in DEFAULT_CATEGORIES:  # หมวดปัญหามาตรฐาน (เพิ่ม/แก้ภายหลังได้ที่ /admin/)
            Category.objects.get_or_create(name=name)

        if opts["branches_excel"]:
            for r in read_excel(opts["branches_excel"], "id"):
                code, company = str(r["id"]).strip(), str(r["DealerName"]).strip()
                Branch.objects.update_or_create(
                    code=code, defaults={"name": SHORT_NAMES.get(code, company), "company_name": company})
            self.stdout.write(f"สาขาในระบบ: {Branch.objects.count()}")

        if opts["excel"]:
            created = skipped = 0
            for r in read_excel(opts["excel"], "ลำดับ"):
                subject = str(r["เรื่อง"]).strip()
                code = str(r["สาขา"]).strip()
                branch, was_new = Branch.objects.get_or_create(code=code, defaults={"name": code})
                if was_new:
                    self.stderr.write(f"คำเตือน: พบสาขา {code} ที่ยังไม่มีในระบบ จึงสร้างให้อัตโนมัติ (แก้ชื่อได้ที่ /admin/)")
                category, _ = Category.objects.get_or_create(name=guess_category(subject))
                _, is_new = Ticket.objects.get_or_create(
                    branch=branch, date=to_date(r["วันที่"]), opened_at=to_time(r["เวลาเปิด"]), subject=subject,
                    defaults={"category": category, "requester": str(r.get("ผู้ขอ") or "").strip(),
                              "closed_at": to_time(r.get("เวลาเสร็จ")),
                              "solution": str(r.get("วิธีแก้ไขปัญหา") or "").strip(),
                              "status": str(r.get("สถานะ") or "เรียบร้อย").strip(),
                              "remark": str(r.get("หมายเหตุ") or "").strip()})
                created += is_new
                skipped += not is_new
            self.stdout.write(self.style.SUCCESS(f"งานที่นำเข้าใหม่: {created} ข้ามรายการซ้ำ: {skipped}"))
