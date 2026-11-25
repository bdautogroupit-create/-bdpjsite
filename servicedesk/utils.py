# ไฟล์นี้ทำอะไร: ฟังก์ชันช่วยคำนวณ: จัดหมวดปัญหาอัตโนมัติ, เวลาที่ใช้, ค่ากลาง/ค่าเฉลี่ยของ KPI
from datetime import timedelta
from statistics import median

SHORT_NAMES = {
    "BDBP": "ภูเก็ต (สาขา 00001)",
    "BDKB": "กระบี่",
    "BDLB": "สงขลา (สาขา 00001)",
    "BDNK": "นครศรีธรรมราช",
    "BDNR": "นราธิวาส",
    "BDPK": "ภูเก็ต",
    "BDPL": "พัทลุง",
    "BDSK": "สงขลา",
    "BDST": "สตูล",
    "BDTR": "ตรัง",
    "DZPK": "BD Ultimate ภูเก็ต",
    "DZSK": "BD Ultimate สงขลา",
}

DEFAULT_CATEGORIES = [
    "เครื่องพิมพ์ / ถ่ายเอกสาร",
    "เว็บไซต์ลา Online",
    "Dealer Pro",
    "อินเทอร์เน็ต",
    "Drive กลาง",
    "Office / Email",
    "อุปกรณ์ / ฮาร์ดแวร์",
]


def guess_category(subject):
    """Pick a category from keywords in the subject (same rules as the dashboard)."""
    s = (subject or "").lower()
    if "ลา online" in s:
        return "เว็บไซต์ลา Online"
    if "dealer" in s:
        return "Dealer Pro"
    if "internet" in s:
        return "อินเทอร์เน็ต"
    if "drive" in s:
        return "Drive กลาง"
    if "office" in s or "e-mail" in s or "email" in s:
        return "Office / Email"
    if "พิมพ์" in s or "ถ่าย" in s:
        return "เครื่องพิมพ์ / ถ่ายเอกสาร"
    return "อุปกรณ์ / ฮาร์ดแวร์"


def week_start(d):
    """Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


def fmt_minutes(m):
    if m is None:
        return "ไม่ระบุ"
    m = int(round(m))
    if m < 60:
        return f"{m} นาที"
    h, r = divmod(m, 60)
    if h >= 24:
        d, h = divmod(h, 24)
        return f"{d} วัน {h} ชม." if h else f"{d} วัน"
    return f"{h} ชม. {r} นาที" if r else f"{h} ชม."


def compute_kpis(tickets):
    n = len(tickets)
    durs = [t.duration_minutes for t in tickets if t.duration_minutes is not None]
    return {
        "total": n,
        "branches": len({t.branch_id for t in tickets}),
        "done": sum(1 for t in tickets if t.status == "เรียบร้อย"),
        "median": median(durs) if durs else None,
        "mean": sum(durs) / len(durs) if durs else None,
        "within30": round(sum(1 for d in durs if d <= 30) / len(durs) * 100) if durs else None,
        "longest": max(durs) if durs else None,
        "carry": sum(1 for t in tickets if t.carried_over),
        "no_time": n - len(durs),
    }
