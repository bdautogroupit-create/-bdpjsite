# ไฟล์นี้ทำอะไร: กำหนด URL ของแอป servicedesk (ทุกที่อยู่ขึ้นต้นด้วย /servicedesk/)
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "servicedesk"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="servicedesk:dashboard", permanent=False)),
    path("dashboard/", views.dashboard, name="dashboard"),                    # เมนูย่อย: แดชบอร์ด
    path("tickets/", views.TicketList.as_view(), name="ticket_list"),         # เมนูย่อย: แจ้งปัญหาการใช้งาน (รายการงาน)
    path("tickets/add/", views.TicketCreate.as_view(), name="ticket_add"),
    path("tickets/<int:pk>/", views.TicketDetail.as_view(), name="ticket_detail"),
    path("tickets/<int:pk>/edit/", views.TicketUpdate.as_view(), name="ticket_edit"),
    path("tickets/<int:pk>/delete/", views.TicketDelete.as_view(), name="ticket_delete"),
]
