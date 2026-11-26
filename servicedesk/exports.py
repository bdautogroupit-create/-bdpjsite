# ไฟล์นี้ทำอะไร: สร้างไฟล์ Excel (.xlsx) ของรายการงาน สำหรับปุ่ม "ส่งออก Excel" (ต้องติดตั้ง openpyxl)
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .templatetags.thai import thai_date
from .utils import compute_kpis, fmt_minutes

# (หัวคอลัมน์, ความกว้าง) เรียงตามคอลัมน์ในชีต "รายการงาน"
COLUMNS = [
    ("ลำดับ", 7), ("วันที่เปิด", 15), ("เวลาที่เปิด", 11), ("วันที่ปิด", 15), ("เวลาที่ปิด", 11),
    ("สาขา", 26), ("เรื่อง", 40), ("ผู้ขอ", 16), ("หมวดปัญหา", 24), ("วิธีแก้ไขปัญหา", 45),
    ("สถานะ", 15), ("เวลาที่ใช้", 15), ("เวลาที่ใช้ (นาที)", 16), ("หมายเหตุ", 32),
]
HEADER_FILL = PatternFill("solid", fgColor="1F6F5C")


def _protect_text(ws):
    """ข้อความที่ผู้ใช้พิมพ์แล้วขึ้นต้นด้วย "=" ต้องเป็นข้อความธรรมดา ไม่ให้ Excel ตีความเป็นสูตร"""
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith("="):
                cell.data_type = "s"


def build_tickets_workbook(tickets, conditions, exported_by, now):
    """tickets: รายการงานที่เรียงแล้ว | conditions: [(ชื่อเงื่อนไข, ค่า)] | now: เวลาที่ส่งออก"""
    tickets = list(tickets)
    wb = Workbook()

    # ---- ชีต 1: รายการงาน ----
    ws = wb.active
    ws.title = "รายการงาน"
    ws.append([name for name, _ in COLUMNS])
    for i, t in enumerate(tickets, 1):
        done = t.closed_at is not None
        ws.append([
            i, thai_date(t.date), t.opened_at.strftime("%H:%M"),
            thai_date(t.closed_on) if done else "", t.closed_at.strftime("%H:%M") if done else "",
            str(t.branch), t.subject, t.requester, t.category.name, t.solution, t.status,
            fmt_minutes(t.duration_minutes), t.duration_minutes, t.remark,
        ])
    for col, (_, width) in enumerate(COLUMNS, 1):
        ws.column_dimensions[get_column_letter(col)].width = width
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{len(tickets) + 1}"
    _protect_text(ws)

    # ---- ชีต 2: สรุป ----
    k = compute_kpis(tickets)
    sm = wb.create_sheet("สรุป")
    rows = [
        ("รายงานงาน IT Service Desk", None),
        ("ส่งออกเมื่อ", f"{thai_date(now.date())} เวลา {now:%H:%M} น."),
        ("ส่งออกโดย", exported_by),
        (None, None),
        ("เงื่อนไขที่กรอง", None),
        *conditions,
        (None, None),
        ("ผลสรุปของรายการที่ส่งออก", None),
        ("จำนวนงาน", k["total"]),
        ("ค่ากลางเวลาแก้ไขต่องาน", fmt_minutes(k["median"])),
        ("เวลาเฉลี่ยต่องาน", fmt_minutes(k["mean"])),
        ("ปิดได้ภายใน 30 นาที", f"{k['within30']}%" if k["within30"] is not None else "-"),
        ("งานที่ใช้เวลานานที่สุด", fmt_minutes(k["longest"])),
        ("งานที่แก้ต่อข้ามวัน", k["carry"]),
        ("งานที่ไม่มีเวลาปิด (ไม่นับในการคำนวณเวลา)", k["no_time"]),
    ]
    for r in rows:
        sm.append(list(r))
        if r[0] is not None and r[1] is None:  # แถวที่เป็นหัวข้อ
            sm.cell(row=sm.max_row, column=1).font = Font(bold=True)
    sm.column_dimensions["A"].width = 42
    sm.column_dimensions["B"].width = 38
    for row in sm.iter_rows():
        row[0].alignment = Alignment(vertical="top")
        if len(row) > 1:
            row[1].alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    _protect_text(sm)
    return wb
