# ไฟล์นี้ทำอะไร: ตัวแปลงการแสดงผลในหน้าเว็บ: วันที่แบบ พ.ศ. และเวลาที่ใช้เป็นนาที/ชั่วโมง
from django import template

from servicedesk.utils import fmt_minutes

register = template.Library()
MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


@register.filter
def thai_date(d):
    """2026-04-20 -> 20 เม.ย. 2569"""
    if not d:
        return ""
    return f"{d.day} {MONTHS[d.month - 1]} {d.year + 543}"


@register.filter
def thai_short(d):
    if not d:
        return ""
    return f"{d.day} {MONTHS[d.month - 1]}"


@register.filter
def minutes_th(m):
    return fmt_minutes(m)
