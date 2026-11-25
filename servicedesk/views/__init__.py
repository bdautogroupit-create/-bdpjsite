# ไฟล์นี้ทำอะไร: รวมหน้าทั้งหมดของแอป servicedesk ให้ urls.py เรียกใช้ได้ที่เดียว
from .dashboard_views import dashboard
from .ticket_views import TicketCreate, TicketDelete, TicketDetail, TicketList, TicketUpdate

__all__ = ["dashboard", "TicketList", "TicketDetail", "TicketCreate", "TicketUpdate", "TicketDelete"]
