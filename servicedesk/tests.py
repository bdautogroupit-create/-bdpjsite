# ไฟล์นี้ทำอะไร: ชุดทดสอบอัตโนมัติของ servicedesk รันด้วย: python manage.py test servicedesk
from datetime import date, time

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Branch, Category, Ticket
from .utils import compute_kpis


class ServiceDeskTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("import_servicedesk", verbosity=0)
        User = get_user_model()
        User.objects.create_superuser("admin", "a@example.com", "pw")
        User.objects.create_user("viewer", password="pw")

    def test_seed_and_idempotent_import(self):
        self.assertEqual(Branch.objects.count(), 12)
        self.assertEqual(Ticket.objects.count(), 21)
        call_command("import_servicedesk", verbosity=0)
        self.assertEqual(Ticket.objects.count(), 21)

    def test_kpis_match_the_excel_numbers(self):
        k = compute_kpis(list(Ticket.objects.select_related("branch")))
        self.assertEqual(k["total"], 21)
        self.assertEqual(k["branches"], 11)
        self.assertEqual(k["median"], 22)
        self.assertEqual(k["within30"], 63)
        self.assertEqual(k["longest"], 551)
        self.assertEqual(k["no_time"], 2)

    def test_pages_need_login(self):
        for name in ("dashboard", "ticket_list"):
            r = self.client.get(reverse(f"servicedesk:{name}"))
            self.assertEqual(r.status_code, 302)
            self.assertIn("/accounts/login/", r["Location"])

    def test_dashboard_filter_by_branch(self):
        self.client.login(username="admin", password="pw")
        r = self.client.get(reverse("servicedesk:dashboard"), {"branch": "BDSK"})
        self.assertEqual(r.context["kpi"]["total"], 5)

    def test_ticket_list_filter_search_and_pagination(self):
        self.client.login(username="admin", password="pw")
        url = reverse("servicedesk:ticket_list")
        self.assertEqual(self.client.get(url).context["paginator"].count, 21)
        self.assertEqual(self.client.get(url, {"branch": "BDSK"}).context["paginator"].count, 5)
        self.assertEqual(self.client.get(url, {"q": "Dealer"}).context["paginator"].count, 3)
        branch, cat = Branch.objects.get(code="BDSK"), Category.objects.first()
        for i in range(40):
            Ticket.objects.create(branch=branch, category=cat, subject=f"x{i}", date="2026-05-01", opened_at="09:00")
        r = self.client.get(url, {"page": 2})
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
