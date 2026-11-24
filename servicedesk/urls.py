# ไฟล์นี้ทำอะไร: กำหนด URL ของแอป เช่น /servicedesk/ และ /servicedesk/tickets/add/
from django.urls import path

from . import views

app_name = "servicedesk"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tickets/add/", views.TicketCreate.as_view(), name="ticket_add"),
    path("tickets/<int:pk>/", views.TicketDetail.as_view(), name="ticket_detail"),
    path("tickets/<int:pk>/edit/", views.TicketUpdate.as_view(), name="ticket_edit"),
    path("tickets/<int:pk>/delete/", views.TicketDelete.as_view(), name="ticket_delete"),
]