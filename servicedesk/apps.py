# ไฟล์นี้ทำอะไร: ตั้งชื่อแอป servicedesk ให้ Django รู้จัก
from django.apps import AppConfig


class ServicedeskConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "servicedesk"
    verbose_name = "IT Service Desk"
