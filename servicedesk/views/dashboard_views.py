# ไฟล์นี้ทำอะไร: หน้า "แดชบอร์ด" (KPI กราฟ ข้อสังเกต) กรองได้โดยคลิกแท่งกราฟหรือเลือกสาขา
from collections import Counter
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from ..models import Branch, Category, Ticket
from ..querystring import qs_set, qs_toggle
from ..templatetags.thai import thai_date, thai_short
from ..utils import compute_kpis, fmt_minutes, week_start


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
