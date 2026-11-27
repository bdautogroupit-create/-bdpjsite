# ไฟล์นี้ทำอะไร: กำหนด URL ของระบบ (หน้าแรก "/", แดชบอร์ด, รายการงาน และ เพิ่ม/แก้ไข/ดู/ลบ งาน)
from django.urls import path

from . import views

app_name = "servicedesk"

urlpatterns = [
    path("", views.home, name="home"),                                        # หน้าแรก
    path("dashboard/", views.dashboard, name="dashboard"),                    # เมนูย่อย: แดชบอร์ด
    path("tickets/", views.TicketList.as_view(), name="ticket_list"),         # เมนูย่อย: แจ้งปัญหาการใช้งาน (รายการงาน)
    path("tickets/export/", views.export_tickets, name="ticket_export"),     # ปุ่มส่งออก Excel
    path("tickets/add/", views.TicketCreate.as_view(), name="ticket_add"),
    path("tickets/<int:pk>/", views.TicketDetail.as_view(), name="ticket_detail"),
    path("tickets/<int:pk>/edit/", views.TicketUpdate.as_view(), name="ticket_edit"),
    path("tickets/<int:pk>/delete/", views.TicketDelete.as_view(), name="ticket_delete"),

    # หน้าตั้งค่า: จัดการสาขาและหมวดปัญหา
    path("settings/branches/", views.BranchList.as_view(), name="branch_list"),
    path("settings/branches/add/", views.BranchCreate.as_view(), name="branch_add"),
    path("settings/branches/<int:pk>/edit/", views.BranchUpdate.as_view(), name="branch_edit"),
    path("settings/branches/<int:pk>/delete/", views.BranchDelete.as_view(), name="branch_delete"),
    path("settings/categories/", views.CategoryList.as_view(), name="category_list"),
    path("settings/categories/add/", views.CategoryCreate.as_view(), name="category_add"),
    path("settings/categories/<int:pk>/edit/", views.CategoryUpdate.as_view(), name="category_edit"),
    path("settings/categories/<int:pk>/delete/", views.CategoryDelete.as_view(), name="category_delete"),
]
