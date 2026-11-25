# ไฟล์นี้ทำอะไร: ฟอร์มเพิ่ม/แก้ไขงาน พร้อมตรวจวันที่และเวลาเปิด-ปิดให้สัมพันธ์กัน
from datetime import datetime

from django import forms

from .models import Ticket


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["branch", "category", "subject", "requester", "status",
                  "date", "opened_at", "closed_date", "closed_at", "solution", "remark"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "closed_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "opened_at": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "closed_at": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "solution": forms.Textarea(attrs={"rows": 3}),
            "remark": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        data = super().clean()
        d, o = data.get("date"), data.get("opened_at")
        cd, ct = data.get("closed_date"), data.get("closed_at")
        if cd and not ct:
            self.add_error("closed_at", "กรอกเวลาที่ปิดด้วย เมื่อระบุวันที่ปิด")
        elif ct and not cd and d:
            data["closed_date"] = cd = d  # ไม่ระบุวันที่ปิด = ปิดในวันเดียวกับวันที่เปิด
        if d and o and cd and ct and datetime.combine(cd, ct) < datetime.combine(d, o):
            self.add_error("closed_at", "วันที่และเวลาที่ปิดต้องไม่ก่อนวันที่และเวลาที่เปิด")
        return data
