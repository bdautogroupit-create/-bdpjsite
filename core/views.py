# ไฟล์นี้ทำอะไร: หน้าแรกของระบบ (หน้าต้อนรับ)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    return render(request, "core/home.html")
