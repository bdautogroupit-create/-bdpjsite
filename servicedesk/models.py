# ไฟล์นี้ทำอะไร: โครงสร้างตารางในฐานข้อมูล: สาขา (Branch), หมวดปัญหา (Category), งาน (Ticket)
from datetime import datetime

from django.db import models


class Branch(models.Model):
    code = models.CharField("รหัสสาขา", max_length=10, unique=True)
    name = models.CharField("ชื่อสาขา", max_length=120)
    company_name = models.CharField("ชื่อบริษัท", max_length=200, blank=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "สาขา"
        verbose_name_plural = "สาขา"

    def __str__(self):
        return f"{self.code} {self.name}"


class Category(models.Model):
    name = models.CharField("หมวดปัญหา", max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "หมวดปัญหา"
        verbose_name_plural = "หมวดปัญหา"

    def __str__(self):
        return self.name


class Ticket(models.Model):
    class Status(models.TextChoices):
        DONE = "เรียบร้อย", "เรียบร้อย"
        IN_PROGRESS = "กำลังดำเนินการ", "กำลังดำเนินการ"
        PENDING = "รอดำเนินการ", "รอดำเนินการ"

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="tickets", verbose_name="สาขา")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="tickets", verbose_name="หมวดปัญหา")
    subject = models.CharField("เรื่อง", max_length=255)
    requester = models.CharField("ผู้ขอ", max_length=100, blank=True)
    date = models.DateField("วันที่เปิด")
    opened_at = models.TimeField("เวลาที่เปิด")
    closed_date = models.DateField("วันที่ปิด", null=True, blank=True)
    closed_at = models.TimeField("เวลาที่ปิด", null=True, blank=True)
    solution = models.TextField("วิธีแก้ไขปัญหา", blank=True)
    status = models.CharField("สถานะ", max_length=20, choices=Status.choices, default=Status.DONE)
    remark = models.TextField("หมายเหตุ", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "งาน"
        verbose_name_plural = "งาน"
        indexes = [models.Index(fields=["date"])]

    def __str__(self):
        return f"{self.date} {self.branch.code} {self.subject}"

    @property
    def closed_on(self):
        """วันที่ปิดงาน: ถ้าไม่ได้ระบุ ถือว่าปิดในวันเดียวกับวันที่เปิด"""
        return self.closed_date or self.date

    @property
    def duration_minutes(self):
        """นาทีตั้งแต่เปิดถึงปิด (รองรับงานข้ามวัน); None ถ้าไม่ทราบเวลาปิดหรือปิดก่อนเปิด"""
        if not self.date or not self.opened_at or not self.closed_at:
            return None
        start = datetime.combine(self.date, self.opened_at)
        end = datetime.combine(self.closed_on, self.closed_at)
        m = int((end - start).total_seconds() // 60)
        return m if m >= 0 else None

    @property
    def carried_over(self):
        """งานที่แก้ต่อข้ามวัน: ปิดคนละวันกับที่เปิด หรือหมายเหตุระบุว่าแก้อีกวัน"""
        return "อีกวัน" in (self.remark or "") or (self.closed_date is not None and self.closed_date != self.date)
