# ไฟล์นี้ทำอะไร: ส่งเมนู (จาก navigation.py) ไปให้ทุกหน้า พร้อมบอกว่าเมนูไหนกำลังเปิดอยู่
from django.urls import reverse

from .navigation import MENU


def _allowed(user, item):
    perm = item.get("perm")
    return not perm or user.has_perm(perm)


def _build(item, path):
    url = reverse(item["url_name"])
    # หน้าแรก ("/") ต้องตรงเป๊ะ ส่วนหน้าอื่นนับรวมหน้าย่อย เช่น /servicedesk/tickets/5/ ก็ถือว่าอยู่ในเมนู "แจ้งปัญหาการใช้งาน"
    active = path == url if url == "/" else path.startswith(url)
    return {"label": item["label"], "url": url, "active": active}


def menu(request):
    if not request.user.is_authenticated:
        return {"menu": []}
    items = []
    for item in MENU:
        if "children" in item:
            kids = [_build(c, request.path) for c in item["children"] if _allowed(request.user, c)]
            if kids:
                items.append({"label": item["label"], "children": kids, "active": any(k["active"] for k in kids)})
        elif _allowed(request.user, item):
            items.append(_build(item, request.path))
    return {"menu": items}
