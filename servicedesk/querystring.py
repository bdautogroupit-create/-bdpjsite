# ไฟล์นี้ทำอะไร: ตัวช่วยสร้างลิงก์ที่เก็บตัวกรอง/เลขหน้าไว้ใน URL (ใช้ร่วมกันทั้งหน้าแดชบอร์ดและหน้ารายการงาน)


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
