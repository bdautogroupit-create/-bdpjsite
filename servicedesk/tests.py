# ไฟล์นี้ทำอะไร: ชุดทดสอบอัตโนมัติของ servicedesk (สร้างข้อมูลทดสอบเองในโค้ด ไม่ต้องมีไฟล์ข้อมูลใดๆ) รันด้วย: python manage.py test servicedesk
import os
import tempfile
from datetime import date, datetime, time

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Branch, Category, Ticket
from .utils import compute_kpis


def make_ticket(branch, category, subject, day, opened, closed=None, **extra):
    return Ticket.objects.create(branch=branch, category=category, subject=subject, date=day,
                                 opened_at=opened, closed_at=closed, **extra)


class ServiceDeskTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        User.objects.create_superuser("admin", "a@example.com", "pw")
        User.objects.create_user("viewer", password="pw")

        sk = Branch.objects.create(code="BDSK", name="สงขลา")
        nr = Branch.objects.create(code="BDNR", name="นราธิวาส")
        Branch.objects.create(code="BDPL", name="พัทลุง")  # สาขาที่ไม่มีงาน
        dealer = Category.objects.create(name="Dealer Pro")
        net = Category.objects.create(name="อินเทอร์เน็ต")
        printer = Category.objects.create(name="เครื่องพิมพ์ / ถ่ายเอกสาร")

        # ใช้เวลา 10, 30, 60, 20 นาที และงานสุดท้ายยังไม่มีเวลาปิด
        make_ticket(sk, dealer, "ระบบ Dealer Pro Error", date(2026, 5, 4), time(10, 0), time(10, 10))
        make_ticket(sk, dealer, "Dealer Pro ใช้งานไม่ได้", date(2026, 5, 5), time(10, 0), time(10, 30))
        make_ticket(sk, net, "internet ช้ามาก", date(2026, 5, 6), time(9, 0), time(10, 0))
        make_ticket(nr, net, "internet ใช้งานไม่ได้", date(2026, 5, 7), time(9, 0), time(9, 20))
        make_ticket(nr, printer, "พิมพ์ไม่ออก", date(2026, 5, 8), time(9, 0))

    def test_kpis(self):
        k = compute_kpis(list(Ticket.objects.select_related("branch")))
        self.assertEqual(k["total"], 5)
        self.assertEqual(k["branches"], 2)
        self.assertEqual(k["median"], 25)      # (20 + 30) / 2
        self.assertEqual(k["mean"], 30)        # (10 + 30 + 60 + 20) / 4
        self.assertEqual(k["within30"], 75)    # 3 จาก 4 งานที่มีเวลาปิด
        self.assertEqual(k["longest"], 60)
        self.assertEqual(k["no_time"], 1)

    def test_pages_need_login(self):
        for name in ("home", "dashboard", "ticket_list"):
            r = self.client.get(reverse(f"servicedesk:{name}"))
            self.assertEqual(r.status_code, 302)
            self.assertIn("/accounts/login/", r["Location"])

    def test_home_shows_welcome_and_menu(self):
        self.client.login(username="viewer", password="pw")
        r = self.client.get(reverse("servicedesk:home"))
        self.assertContains(r, "ยินดีต้อนรับเข้าสู่ระบบ Computer Support")
        for label in ("แจ้งปัญหาในการใช้งาน", "แดชบอร์ด", "แจ้งปัญหาการใช้งาน"):
            self.assertContains(r, label)

    def test_menu_highlights_current_page(self):
        self.client.login(username="viewer", password="pw")
        for name in ("dashboard", "ticket_list"):
            r = self.client.get(reverse(f"servicedesk:{name}"))
            self.assertContains(r, 'nav-sub on', count=1)  # เมนูย่อยที่กำลังเปิดอยู่ มีเมนูเดียว

    def test_dashboard_filter_by_branch(self):
        self.client.login(username="admin", password="pw")
        r = self.client.get(reverse("servicedesk:dashboard"), {"branch": "BDSK"})
        self.assertEqual(r.context["kpi"]["total"], 3)

    def test_dashboard_works_with_empty_database(self):
        Ticket.objects.all().delete()
        self.client.login(username="admin", password="pw")
        self.assertEqual(self.client.get(reverse("servicedesk:dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("servicedesk:ticket_list")).status_code, 200)

    def test_ticket_list_filter_search_and_pagination(self):
        self.client.login(username="admin", password="pw")
        url = reverse("servicedesk:ticket_list")
        self.assertEqual(self.client.get(url).context["paginator"].count, 5)
        self.assertEqual(self.client.get(url, {"branch": "BDSK"}).context["paginator"].count, 3)
        self.assertEqual(self.client.get(url, {"q": "Dealer"}).context["paginator"].count, 2)
        branch, cat = Branch.objects.get(code="BDSK"), Category.objects.first()
        for i in range(60):
            make_ticket(branch, cat, f"x{i}", date(2026, 5, 1), time(9, 0))
        r = self.client.get(url, {"page": 2})  # รวม 65 งาน หน้าละ 30
        self.assertEqual(r.context["page_obj"].number, 2)
        self.assertEqual(len(r.context["page_obj"]), 30)

    def test_viewer_is_read_only(self):
        self.client.login(username="viewer", password="pw")
        r = self.client.get(reverse("servicedesk:ticket_list"))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "เพิ่มงานใหม่")
        self.assertEqual(self.client.get(reverse("servicedesk:ticket_add")).status_code, 403)

    def test_admin_can_add_edit_delete(self):
        self.client.login(username="admin", password="pw")
        data = {"branch": Branch.objects.get(code="BDPL").pk, "date": "2026-05-21", "subject": "ทดสอบ",
                "requester": "", "category": Category.objects.first().pk, "opened_at": "10:00", "closed_date": "",
                "closed_at": "10:30", "solution": "", "status": "เรียบร้อย", "remark": ""}
        self.client.post(reverse("servicedesk:ticket_add"), data)
        t = Ticket.objects.get(subject="ทดสอบ")
        self.assertEqual(t.duration_minutes, 30)
        self.assertEqual(t.closed_date, date(2026, 5, 21))  # ไม่ระบุวันที่ปิด = วันเดียวกับวันที่เปิด
        self.client.post(reverse("servicedesk:ticket_edit", args=[t.pk]), {**data, "closed_at": "11:00"})
        t.refresh_from_db()
        self.assertEqual(t.duration_minutes, 60)
        bad = self.client.post(reverse("servicedesk:ticket_edit", args=[t.pk]), {**data, "closed_at": "09:00"})
        self.assertContains(bad, "วันที่และเวลาที่ปิดต้องไม่ก่อนวันที่และเวลาที่เปิด")
        self.client.post(reverse("servicedesk:ticket_delete", args=[t.pk]))
        self.assertFalse(Ticket.objects.filter(pk=t.pk).exists())

    def test_cross_day_duration(self):
        t = Ticket.objects.create(branch=Branch.objects.first(), category=Category.objects.first(),
                                  subject="ข้ามวัน", date=date(2026, 5, 1), opened_at=time(10, 0),
                                  closed_date=date(2026, 5, 2), closed_at=time(9, 0))
        self.assertEqual(t.duration_minutes, 1380)
        self.assertTrue(t.carried_over)


class ImportCommandTests(TestCase):
    def test_requires_a_file(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("import_servicedesk")

    def test_import_from_excel_is_idempotent_and_converts_buddhist_year(self):
        try:
            from openpyxl import Workbook
        except ImportError:
            self.skipTest("ต้องติดตั้ง openpyxl ก่อน (pip install openpyxl)")
        with tempfile.TemporaryDirectory() as tmp:
            bpath, tpath = os.path.join(tmp, "branches.xlsx"), os.path.join(tmp, "tickets.xlsx")
            wb = Workbook()
            wb.active.append(["id", "DealerName"])
            wb.active.append(["BDSK", "บริษัท บีดี ออโต้ สงขลา จำกัด (สำนักงานใหญ่)"])
            wb.save(bpath)
            wb = Workbook()
            ws = wb.active
            ws.append(["รายงาน Service Desk"])  # แถวชื่อเรื่อง (แถวหัวตารางอยู่แถวที่ 2)
            ws.append(["ลำดับ", "สาขา", "เรื่อง", "ผู้ขอ", "วันที่", "เวลาเปิด", "เวลาเสร็จ",
                       "วิธีแก้ไขปัญหา", "สถานะ", "หมายเหตุ"])
            ws.append([1, "BDSK", "ระบบ Dealer Pro Error", "ผู้ทดสอบ", datetime(2569, 5, 4), time(10, 0),
                       time(10, 30), "รีสตาร์ทเครื่อง", "เรียบร้อย", None])
            wb.save(tpath)
            for _ in range(2):  # รันซ้ำต้องไม่เกิดรายการซ้ำ
                call_command("import_servicedesk", branches_excel=bpath, excel=tpath, verbosity=0)
        t = Ticket.objects.get()
        self.assertEqual(t.date, date(2026, 5, 4))  # พ.ศ. 2569 -> ค.ศ. 2026
        self.assertEqual(t.duration_minutes, 30)
        self.assertEqual(t.category.name, "Dealer Pro")
        self.assertEqual(t.branch.name, "สงขลา")
