# ไฟล์นี้ทำอะไร: ศูนย์รวม URL ของทั้งเว็บ (แต่ละแอปมี urls.py ของตัวเอง แล้วนำมาต่อที่นี่)
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),   # ล็อกอิน/ออกจากระบบ
    path("servicedesk/", include("servicedesk.urls")),         # /servicedesk/dashboard/ และ /servicedesk/tickets/
    path("", include("core.urls")),                            # หน้าแรก "/"
]
