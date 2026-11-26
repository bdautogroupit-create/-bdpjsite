# ไฟล์นี้ทำอะไร: ตรรกะของทุกหน้าในระบบ: หน้าแรก, แดชบอร์ด, รายการงาน และ เพิ่ม-แก้ไข-ดูรายละเอียด-ลบ งาน
from collections import Counter
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import urlencode
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import TicketForm
from .models import Branch, Category, Ticket
from .templatetags.thai import thai_date, thai_short
from .utils import compute_kpis, fmt_minutes, week_start


# ======================================================================
# 1) ตัวช่วยสร้างลิงก์ที่เก็บตัวกรอง/เลขหน้าไว้ใน URL
# ======================================================================
def _params(request):
    p = request.GET.copy()
    p.pop("page", None)  # เปลี่ยนตัวกรองแล้วให้กลับไปหน้า 1
    return p


def qs_toggle(request, key, value):
    """ลิงก์ที่เปิด/ปิดตัวกรอง key=value (คลิกแท่งกราฟ)"""
    p = _params(request)
    vals = p.getlist(key)
    if value in vals:
        vals.remove(value)
    else:
        vals.append(value)
    p.setlist(key, vals)
    return "?" + p.urlencode()


def qs_set(request, key, values):
    """ลิงก์ที่ตั้งค่าตัวกรอง key ใหม่ทั้งหมด (dropdown เลือกสาขา)"""
    p = _params(request)
    p.setlist(key, values)
    return "?" + p.urlencode()


def qs_page(request, n):
    """ลิงก์ไปหน้า n โดยคงตัวกรองเดิมไว้"""
    p = request.GET.copy()
    p["page"] = n
    return "?" + p.urlencode()


def page_links(request, page_obj):
    """คืน (เลขหน้าที่จะแสดง, ลิงก์ก่อนหน้า, ลิงก์ถัดไป) ตัวอย่าง: 1 ... 4 [5] 6 ... 20"""
    last = page_obj.paginator.num_pages
    shown = [i for i in range(1, last + 1) if i in (1, last) or abs(i - page_obj.number) <= 1]
    pages, prev = [], None
    for i in shown:
        if prev and i - prev > 1:
            pages.append({"gap": True})
        pages.append({"n": i, "url": qs_page(request, i), "current": i == page_obj.number})
        prev = i
    prev_url = qs_page(request, page_obj.previous_page_number()) if page_obj.has_previous() else ""
    next_url = qs_page(request, page_obj.next_page_number()) if page_obj.has_next() else ""
    return pages, prev_url, next_url


# ======================================================================
# 2) หน้าแรก
# ======================================================================
@login_required
def home(request):
    return render(request, "servicedesk/home.html")


# ======================================================================
# 3) แดชบอร์ด (KPI กราฟ ข้อสังเกต) กรองได้โดยคลิกแท่งกราฟหรือเลือกสาขา
# ======================================================================
def _bars(request, key, items, counts, selected):
    """แท่งกราฟที่คลิกแล้วเปิด/ปิดตัวกรอง items: [(ค่า, ป้ายชื่อ)]  counts: {ค่า: จำนวน}"""
    mx = max(list(counts.values()) + [1])
    return [{
        "label": label,
        "count": counts.get(value, 0),
        "pct": round(counts.get(value, 0) / mx * 100),
        "selected": value in selected,
        "dim": bool(selected) and value not in selected,
        "url": qs_toggle(request, key, value),
    } for value, label in items]


@login_required
def dashboard(request):
    sel = {k: [v for v in request.GET.getlist(k) if v] for k in ("branch", "category", "week")}
    weeks_sel = []
    for w in sel["week"]:
        try:
            weeks_sel.append(date.fromisoformat(w))
        except ValueError:
            pass

    base = Ticket.objects.select_related("branch", "category")

    def filtered(exclude=None):
        """ใช้ตัวกรองทั้งหมดยกเว้น `exclude` เพื่อให้แต่ละกราฟยังเห็นตัวเลือกอื่นอยู่"""
        qs = base
        if sel["branch"] and exclude != "branch":
            qs = qs.filter(branch__code__in=sel["branch"])
        if sel["category"] and exclude != "category":
            qs = qs.filter(category__name__in=sel["category"])
        if weeks_sel and exclude != "week":
            q = Q()
            for w in weeks_sel:
                q |= Q(date__gte=w, date__lt=w + timedelta(days=7))
            qs = qs.filter(q)
        return qs

    branches = list(Branch.objects.all())
    categories = list(Category.objects.all())

    branch_counts = Counter(filtered("branch").values_list("branch__code", flat=True))
    cat_counts = Counter(filtered("category").values_list("category__name", flat=True))
    week_counts = Counter(week_start(d) for d in filtered("week").values_list("date", flat=True))

    branch_items = sorted(((b.code, str(b)) for b in branches), key=lambda x: (-branch_counts.get(x[0], 0), x[0]))
    cat_items = sorted(((c.name, c.name) for c in categories), key=lambda x: (-cat_counts.get(x[0], 0), x[0]))
    branch_bars = _bars(request, "branch", branch_items, branch_counts, sel["branch"])
    cat_bars = _bars(request, "category", cat_items, cat_counts, sel["category"])

    all_dates = list(base.values_list("date", flat=True))
    week_cols = []
    if all_dates:
        mx = max(list(week_counts.values()) + [1])
        w, last = week_start(min(all_dates)), week_start(max(all_dates))
        while w <= last:
            n = week_counts.get(w, 0)
            week_cols.append({
                "label": thai_short(w), "count": n, "pct": round(n / mx * 100),
                "selected": w.isoformat() in sel["week"],
                "dim": bool(sel["week"]) and w.isoformat() not in sel["week"],
                "url": qs_toggle(request, "week", w.isoformat()),
            })
            w += timedelta(days=7)

    tickets = list(filtered())
    k = compute_kpis(tickets)

    # ข้อสังเกตสร้างจากข้อมูลจริง ไม่เขียนตายตัว
    insights = []
    if tickets:
        tb = Counter(str(t.branch) for t in tickets).most_common(1)[0]
        tc = Counter(t.category.name for t in tickets).most_common(1)[0]
        insights.append(f"สาขาที่แจ้งงานมากที่สุด คือ {tb[0]} จำนวน {tb[1]} งาน")
        insights.append(f"หมวดปัญหาที่พบบ่อยที่สุด คือ {tc[0]} จำนวน {tc[1]} งาน")
        longest = max((t for t in tickets if t.duration_minutes is not None),
                      key=lambda t: t.duration_minutes, default=None)
        if longest:
            insights.append(f"งานที่ใช้เวลานานที่สุด คือ {longest.subject} ({longest.branch}, "
                            f"{thai_short(longest.date)}) ใช้เวลา {fmt_minutes(longest.duration_minutes)}")
        idle = [str(b) for b in branches if branch_counts.get(b.code, 0) == 0]
        if idle and len(idle) < len(branches):
            insights.append("สาขาที่ไม่มีงานในมุมมองนี้ " + ", ".join(idle))
        if k["mean"] and k["median"] and k["mean"] > k["median"] * 1.5:
            insights.append("ค่าเฉลี่ยสูงกว่าค่ากลางมาก เพราะมีงานใช้เวลานานบางงานดึงค่าขึ้น ค่ากลางสะท้อนงานทั่วไปได้ดีกว่า")

    chips = ([str(b) for b in branches if b.code in sel["branch"]] + sel["category"]
             + [f"สัปดาห์ {thai_short(w)}" for w in weeks_sel])
    branch_options = [{"label": "ทุกสาขา", "url": qs_set(request, "branch", []), "selected": not sel["branch"]}]
    branch_options += [{"label": str(b), "url": qs_set(request, "branch", [b.code]),
                        "selected": sel["branch"] == [b.code]} for b in branches]
    if len(sel["branch"]) > 1:
        branch_options.insert(0, {"label": f"เลือกหลายสาขา ({len(sel['branch'])})", "url": "", "selected": True})

    kpi_cards = [
        (k["total"], "งานทั้งหมด"),
        (k["branches"], "สาขาที่แจ้งงาน"),
        (f"{k['within30']}%" if k["within30"] is not None else "-", "ปิดได้ภายใน 30 นาที"),
        (fmt_minutes(k["mean"]), "เวลาเฉลี่ยต่องาน"),
        (k["carry"], "งานที่ต้องแก้ต่อข้ามวัน"),
        (fmt_minutes(k["longest"]), "งานที่ใช้เวลานานที่สุด"),
    ]
    period = ""
    if all_dates:
        period = (f"งานสนับสนุนด้านไอที {thai_date(min(all_dates))} ถึง {thai_date(max(all_dates))} "
                  f"จากสาขาที่แจ้งงาน {len(set(base.values_list('branch_id', flat=True)))} จาก {len(branches)} สาขา")

    return render(request, "servicedesk/dashboard.html", {
        "period": period, "chips": chips, "branch_options": branch_options,
        "kpi": k, "kpi_cards": kpi_cards, "branch_bars": branch_bars, "cat_bars": cat_bars,
        "week_cols": week_cols, "insights": insights,
    })


# ======================================================================
# 4) รายการงาน (ค้นหา/กรอง/แบ่งหน้า) และ เพิ่ม-แก้ไข-ดูรายละเอียด-ลบ งาน
# ======================================================================
LIST_URL = reverse_lazy("servicedesk:ticket_list")  # ทำรายการเสร็จแล้วกลับมาหน้ารายการงาน


FILTER_KEYS = ("q", "branch", "category", "status")  # ตัวกรองที่ใช้ในหน้ารายการงาน


def filter_tickets(request):
    """งานที่ตรงกับตัวกรองใน URL (คำค้น/สาขา/หมวด/สถานะ) ใช้ร่วมกันทั้งหน้ารายการงานและปุ่มส่งออก Excel"""
    qs = Ticket.objects.select_related("branch", "category")  # เรียงใหม่→เก่าตาม Meta ของโมเดล
    g = request.GET
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


class TicketList(LoginRequiredMixin, ListView):
    """รายการงาน: ค้นหาคำ + กรองสาขา/หมวด/สถานะ แบ่งหน้าละ 30 รายการ"""
    template_name = "servicedesk/ticket_list.html"
    paginate_by = 30

    def get_queryset(self):
        return filter_tickets(self.request)

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
        ctx["export_qs"] = urlencode({k: g[k] for k in FILTER_KEYS if g.get(k)})  # ส่งตัวกรองเดียวกันไปให้ปุ่มส่งออก
        return ctx


@login_required
def export_tickets(request):
    """ปุ่ม "ส่งออก Excel": ส่งออกงานที่กรองอยู่ทั้งหมด (ไม่ใช่แค่หน้าที่เห็น) เป็นไฟล์ .xlsx"""
    try:
        from .exports import build_tickets_workbook
    except ImportError:
        messages.error(request, "ส่งออก Excel ไม่ได้ เพราะยังไม่ได้ติดตั้ง openpyxl (เพิ่มบรรทัด openpyxl ใน requirements.txt)")
        return redirect("servicedesk:ticket_list")

    g = request.GET
    branch = Branch.objects.filter(code=g["branch"]).first() if g.get("branch") else None
    conditions = [
        ("คำค้น", g.get("q", "").strip() or "ทั้งหมด"),
        ("สาขา", str(branch) if branch else (g.get("branch") or "ทุกสาขา")),
        ("หมวดปัญหา", g.get("category") or "ทุกหมวด"),
        ("สถานะ", g.get("status") or "ทุกสถานะ"),
    ]
    now = timezone.localtime()
    wb = build_tickets_workbook(filter_tickets(request), conditions, request.user.get_username(), now)
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="service_desk_{now:%Y%m%d_%H%M}.xlsx"'
    wb.save(response)
    return response


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
