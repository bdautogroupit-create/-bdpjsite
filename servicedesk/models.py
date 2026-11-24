# ไฟล์นี้ทำอะไร: โครงสร้างตารางในฐานข้อมูล: สาขา (Branch), หมวดปัญหา (Category), งาน (Ticket)
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
    date = models.DateField("วันที่")
    opened_at = models.TimeField("เวลาเปิด")
    closed_at = models.TimeField("เวลาเสร็จ", null=True, blank=True)
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
    def duration_minutes(self):
        """Minutes from open to close; None if unknown or the close time is earlier."""
        if not self.opened_at or not self.closed_at:
            return None
        m = (self.closed_at.hour * 60 + self.closed_at.minute) - (self.opened_at.hour * 60 + self.opened_at.minute)
        return m if m >= 0 else None

    @property
    def carried_over(self):
        return "อีกวัน" in (self.remark or "")
