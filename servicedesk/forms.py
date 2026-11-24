# ไฟล์นี้ทำอะไร: ฟอร์มเพิ่ม/แก้ไขงาน พร้อมตรวจว่าเวลาเสร็จต้องไม่ก่อนเวลาเปิด
from django import forms

from .models import Ticket


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["branch", "date", "subject", "requester", "category",
                  "opened_at", "closed_at", "solution", "status", "remark"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "opened_at": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "closed_at": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "solution": forms.Textarea(attrs={"rows": 3}),
            "remark": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        data = super().clean()
        o, e = data.get("opened_at"), data.get("closed_at")
        if o and e and e < o:
            self.add_error("closed_at", "เวลาเสร็จต้องไม่ก่อนเวลาเปิด")
        return data
