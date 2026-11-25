# ไฟล์นี้ทำอะไร: หน้า "รายการงาน" (ค้นหา/กรอง/แบ่งหน้า) และ เพิ่ม-แก้ไข-ดูรายละเอียด-ลบ งาน
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from ..forms import TicketForm
from ..models import Branch, Category, Ticket
from ..querystring import page_links

LIST_URL = reverse_lazy("servicedesk:ticket_list")  # ทำรายการเสร็จแล้วกลับมาหน้ารายการงาน


class TicketList(LoginRequiredMixin, ListView):
    """รายการงาน: ค้นหาคำ + กรองสาขา/หมวด/สถานะ แบ่งหน้าละ 30 รายการ"""
    template_name = "servicedesk/ticket_list.html"
    paginate_by = 30

    def get_queryset(self):
        qs = Ticket.objects.select_related("branch", "category")  # เรียงใหม่→เก่าตาม Meta ของโมเดล
        g = self.request.GET
        if g.get("branch"):
            qs = qs.filter(branch__code=g["branch"])
        if g.get("category"):
            qs = qs.filter(category__name=g["category"])
        if g.get("status"):
            qs = qs.filter(status=g["status"])
        q = g.get("q", "").strip()
        if q:
            qs = qs.filter(Q(subject__icontains=q) | Q(requester__icontains=q) | Q(solution__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        g = self.request.GET
        ctx.update({
            "branches": Branch.objects.all(),
            "categories": Category.objects.all(),
            "statuses": Ticket.Status.choices,
            "f": {k: g.get(k, "") for k in ("q", "branch", "category", "status")},
            "has_filter": any(g.get(k) for k in ("q", "branch", "category", "status")),
            "total": ctx["paginator"].count,
        })
        ctx["pages"], ctx["prev_url"], ctx["next_url"] = page_links(self.request, ctx["page_obj"])
        return ctx


class TicketDetail(LoginRequiredMixin, DetailView):
    queryset = Ticket.objects.select_related("branch", "category")
    template_name = "servicedesk/ticket_detail.html"


class TicketCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = "servicedesk/ticket_form.html"
    permission_required = "servicedesk.add_ticket"
    success_url = LIST_URL
    success_message = "เพิ่มงานเรียบร้อยแล้ว"

    def get_initial(self):
        return {"date": timezone.localdate()}


class TicketUpdate(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Ticket
    form_class = TicketForm
    template_name = "servicedesk/ticket_form.html"
    permission_required = "servicedesk.change_ticket"
    success_url = LIST_URL
    success_message = "บันทึกการแก้ไขเรียบร้อยแล้ว"


class TicketDelete(PermissionRequiredMixin, DeleteView):
    model = Ticket
    template_name = "servicedesk/ticket_confirm_delete.html"
    permission_required = "servicedesk.delete_ticket"
    success_url = LIST_URL

    def form_valid(self, form):
        messages.success(self.request, "ลบงานเรียบร้อยแล้ว")
        return super().form_valid(form)
