# ไฟล์นี้ทำอะไร: ตรรกะของแต่ละหน้า: dashboard (กรอง, แบ่งหน้า, KPI) และเพิ่ม-แก้ไข-ดูรายละเอียด-ลบงาน
from collections import Counter
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from .forms import TicketForm
from .models import Branch, Category, Ticket
from .templatetags.thai import thai_date, thai_short
from .utils import compute_kpis, fmt_minutes, week_start

PAGE_SIZE = 30


# ---- query-string helpers (filters live in the URL so every view is a shareable link) ----
def _params(request):
    p = request.GET.copy()
    p.pop("page", None)
    return p


def qs_toggle(request, key, value):
    p = _params(request)
    vals = p.getlist(key)
    if value in vals:
        vals.remove(value)
    else:
        vals.append(value)
    p.setlist(key, vals)
    return "?" + p.urlencode()


def qs_set(request, key, values):
    p = _params(request)
    p.setlist(key, values)
    return "?" + p.urlencode()


def qs_page(request, n):
    p = request.GET.copy()
    p["page"] = n
    return "?" + p.urlencode()


def _bars(request, key, items, counts, selected):
    """items: [(value, label)]; counts: {value: n}. Returns clickable bars that toggle a filter."""
    mx = max(list(counts.values()) + [1])
    bars = []
    for value, label in items:
        n = counts.get(value, 0)
        bars.append({
            "label": label,
            "count": n,
            "pct": round(n / mx * 100),
            "selected": value in selected,
            "dim": bool(selected) and value not in selected,
            "url": qs_toggle(request, key, value),
        })
    return bars


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
        """All active filters except `exclude`, so each chart still shows its alternatives."""
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
        w = week_start(min(all_dates))
        last = week_start(max(all_dates))
        while w <= last:
            n = week_counts.get(w, 0)
            week_cols.append({
                "label": thai_short(w), "count": n, "pct": round(n / mx * 100),
                "selected": w.isoformat() in sel["week"],
                "dim": bool(sel["week"]) and w.isoformat() not in sel["week"],
                "url": qs_toggle(request, "week", w.isoformat()),
            })
            w += timedelta(days=7)

    tickets = list(filtered().order_by("-date", "-id"))
    k = compute_kpis(tickets)
    paginator = Paginator(tickets, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    pages, shown = [], []
    for i in range(1, paginator.num_pages + 1):
        if i == 1 or i == paginator.num_pages or abs(i - page_obj.number) <= 1:
            shown.append(i)
    prev = None
    for i in shown:
        if prev and i - prev > 1:
            pages.append({"gap": True})
        pages.append({"n": i, "url": qs_page(request, i), "current": i == page_obj.number})
        prev = i

    # insights are generated from the data, never hardcoded
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

    chips = ([f"{b}" for b in branches if b.code in sel["branch"]] + sel["category"]
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
    all_range = list(base.order_by("date").values_list("date", flat=True))
    period = ""
    if all_range:
        period = (f"งานสนับสนุนด้านไอที {thai_date(all_range[0])} ถึง {thai_date(all_range[-1])} "
                  f"จากสาขาที่แจ้งงาน {len(set(base.values_list('branch_id', flat=True)))} จาก {len(branches)} สาขา")

    return render(request, "servicedesk/dashboard.html", {
        "period": period, "chips": chips, "branch_options": branch_options,
        "kpi": k, "kpi_cards": kpi_cards, "branch_bars": branch_bars, "cat_bars": cat_bars,
        "week_cols": week_cols, "insights": insights, "page_obj": page_obj, "pages": pages,
        "prev_url": qs_page(request, page_obj.previous_page_number()) if page_obj.has_previous() else "",
        "next_url": qs_page(request, page_obj.next_page_number()) if page_obj.has_next() else "",
        "total": paginator.count,
    })


# ---- CRUD: login required; add/change/delete need the matching Django permission ----
class TicketDetail(LoginRequiredMixin, DetailView):
    queryset = Ticket.objects.select_related("branch", "category")
    template_name = "servicedesk/ticket_detail.html"


class TicketCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = "servicedesk/ticket_form.html"
    permission_required = "servicedesk.add_ticket"
    success_url = reverse_lazy("servicedesk:dashboard")
    success_message = "เพิ่มงานเรียบร้อยแล้ว"

    def get_initial(self):
        return {"date": timezone.localdate()}


class TicketUpdate(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Ticket
    form_class = TicketForm
    template_name = "servicedesk/ticket_form.html"
    permission_required = "servicedesk.change_ticket"
    success_url = reverse_lazy("servicedesk:dashboard")
    success_message = "บันทึกการแก้ไขเรียบร้อยแล้ว"


class TicketDelete(PermissionRequiredMixin, DeleteView):
    model = Ticket
    template_name = "servicedesk/ticket_confirm_delete.html"
    permission_required = "servicedesk.delete_ticket"
    success_url = reverse_lazy("servicedesk:dashboard")

    def form_valid(self, form):
        messages.success(self.request, "ลบงานเรียบร้อยแล้ว")
        return super().form_valid(form)
