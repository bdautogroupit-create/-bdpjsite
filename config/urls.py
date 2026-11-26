# ไฟล์นี้ทำอะไร: ศูนย์รวม URL ของทั้งเว็บ
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),   # ล็อกอิน/ออกจากระบบ
    path("", include("servicedesk.urls")),                     # หน้าแรก "/" และทุกหน้าของระบบ
]
