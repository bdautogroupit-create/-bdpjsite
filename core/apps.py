# ไฟล์นี้ทำอะไร: ตั้งชื่อแอป core (ระบบกลาง: หน้าแรก เมนู และเลย์เอาต์ที่ทุกโมดูลใช้ร่วมกัน)
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "ระบบกลาง (หน้าแรกและเมนู)"
