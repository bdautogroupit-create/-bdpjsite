# ไฟล์นี้ทำอะไร: ทดสอบหน้าแรกและเมนู รันด้วย: python manage.py test core
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class CoreTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_user("tester", password="pw")

    def test_home_needs_login(self):
        r = self.client.get(reverse("core:home"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/accounts/login/", r["Location"])

    def test_home_shows_welcome_and_menu(self):
        self.client.login(username="tester", password="pw")
        r = self.client.get(reverse("core:home"))
        self.assertContains(r, "ยินดีต้อนรับเข้าสู่ระบบ Computer Support")
        for label in ("แจ้งปัญหาในการใช้งาน", "แดชบอร์ด", "แจ้งปัญหาการใช้งาน"):
            self.assertContains(r, label)

    def test_menu_marks_active_page(self):
        self.client.login(username="tester", password="pw")
        r = self.client.get(reverse("servicedesk:ticket_list"))
        group = [m for m in r.context["menu"] if m.get("children")][0]
        self.assertTrue(group["active"])
        self.assertEqual([c["active"] for c in group["children"]], [False, True])
