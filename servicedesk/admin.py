# ไฟล์นี้ทำอะไร: หน้า /admin สำหรับจัดการข้อมูลสาขา หมวดปัญหา และงาน
from django.contrib import admin

from .models import Branch, Category, Ticket


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "company_name")
    search_fields = ("code", "name", "company_name")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("date", "branch", "subject", "category", "requester", "status")
    list_filter = ("branch", "category", "status")
    search_fields = ("subject", "requester", "solution", "remark")
    date_hierarchy = "date"
