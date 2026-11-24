# ไฟล์นี้ทำอะไร: คำสั่งนำเข้าข้อมูลสาขาและงาน (จากข้อมูลเริ่มต้น หรือจากไฟล์ Excel)
"""Load Service Desk data.

  python manage.py import_servicedesk                       # bundled seed (branches + the first 21 tickets)
  python manage.py import_servicedesk --excel Service_Desk.xlsx [--branches-excel สาขา.xlsx]

Safe to run repeatedly: a ticket with the same branch, date, open time and subject is not duplicated.
"""
import json
import re
from datetime import date, datetime, time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from servicedesk.models import Branch, Category, Ticket
from servicedesk.utils import DEFAULT_CATEGORIES, SHORT_NAMES, guess_category

SEED_DIR = Path(__file__).resolve().parents[2] / "seed"


def to_date(v):
    if isinstance(v, datetime):
        v = v.date()
    if isinstance(v, str):
        m = re.match(r"^\s*(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})\s*$", v)
        if not m:
            return date.fromisoformat(v.strip())
        v = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    if v.year > 2400:  # Buddhist Era (พ.ศ.) -> ค.ศ.
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
    from openpyxl import load_workbook

    rows = list(load_workbook(path, data_only=True).active.iter_rows(values_only=True))
    start = next((i for i, r in enumerate(rows) if r and r[0] == first_header), None)
    if start is None:
        raise CommandError(f"ไม่พบแถวหัวตารางที่ขึ้นต้นด้วย '{first_header}' ในไฟล์ {path}")
    header = [str(h).strip() if h is not None else "" for h in rows[start]]
    for r in rows[start + 1:]:
        if r and any(v not in (None, "") for v in r):
            yield dict(zip(header, r))


class Command(BaseCommand):
    help = "Import branches, categories and Service Desk tickets (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--excel", help="Service_Desk.xlsx (header row starts with 'ลำดับ')")
        parser.add_argument("--branches-excel", help="สาขา.xlsx (columns: id, DealerName)")

    def handle(self, *args, **opts):
        for name in DEFAULT_CATEGORIES:
            Category.objects.get_or_create(name=name)

        # branches
        if opts["branches_excel"]:
            branches = [{"code": str(r["id"]).strip(), "company_name": str(r["DealerName"]).strip()}
                        for r in read_excel(opts["branches_excel"], "id")]
        else:
            branches = json.loads((SEED_DIR / "branches.json").read_text(encoding="utf-8"))
        for b in branches:
            Branch.objects.update_or_create(
                code=b["code"],
                defaults={"name": SHORT_NAMES.get(b["code"], b["company_name"]), "company_name": b["company_name"]})
        self.stdout.write(f"สาขา: {Branch.objects.count()}")

        # tickets
        if opts["excel"]:
            records = [{
                "branch": str(r["สาขา"]).strip(), "subject": str(r["เรื่อง"]).strip(),
                "requester": str(r.get("ผู้ขอ") or "").strip(), "date": to_date(r["วันที่"]),
                "opened_at": to_time(r["เวลาเปิด"]), "closed_at": to_time(r.get("เวลาเสร็จ")),
                "solution": str(r.get("วิธีแก้ไขปัญหา") or "").strip(),
                "status": str(r.get("สถานะ") or "เรียบร้อย").strip(),
                "remark": str(r.get("หมายเหตุ") or "").strip(), "category": None,
            } for r in read_excel(opts["excel"], "ลำดับ")]
        else:
            records = json.loads((SEED_DIR / "tickets.json").read_text(encoding="utf-8"))
            for r in records:
                r["date"] = date.fromisoformat(r["date"])
                r["opened_at"] = to_time(r["opened_at"])
                r["closed_at"] = to_time(r.get("closed_at"))

        created = skipped = 0
        for r in records:
            branch, was_new = Branch.objects.get_or_create(code=r["branch"], defaults={"name": r["branch"]})
            if was_new:
                self.stderr.write(f"คำเตือน: พบสาขา {r['branch']} ที่ไม่มีในรายการสาขา จึงสร้างให้อัตโนมัติ")
            category, _ = Category.objects.get_or_create(name=r.get("category") or guess_category(r["subject"]))
            _, is_new = Ticket.objects.get_or_create(
                branch=branch, date=r["date"], opened_at=r["opened_at"], subject=r["subject"],
                defaults={"category": category, "requester": r["requester"], "closed_at": r["closed_at"],
                          "solution": r["solution"], "status": r["status"], "remark": r["remark"]})
            created += is_new
            skipped += not is_new
        self.stdout.write(self.style.SUCCESS(f"งานที่นำเข้าใหม่: {created} ข้ามรายการซ้ำ: {skipped}"))
