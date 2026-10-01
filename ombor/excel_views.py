"""Omborni Excel orqali yangilash sahifalari (v3.0.0).

Mexanizmi `ombor/excel.py` da: fayl -> qoralama -> qo'llash -> bekor qilish.
"""
from datetime import date
from urllib.parse import quote, urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import excel
from .forms import ExcelYuklashForm, QatorForm
from .models import OmborYangilanish, YangilanishQatori

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
Qator = YangilanishQatori


def filtrlar(request):
    """Ro'yxat va yuklab olish uchun bir xil filtr (GET dan)."""
    g = request.GET
    return {"q": (g.get("q") or "").strip(), "valyuta": g.get("valyuta") or "",
            "kam_birinchi": g.get("kam") == "1", "tugagan": g.get("tugagan") == "1",
            "yashirilgan": g.get("yashirilgan") == "1"}


def _xlsx(baytlar, nom):
    javob = HttpResponse(baytlar, content_type=XLSX)
    javob["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(nom)}"
    return javob


def eksport(request):
    """Omborni Excel'ga — ro'yxatdagi filtr va tartib bilan."""
    f = filtrlar(request)
    qism = " (kam qolganlar birinchi)" if f["kam_birinchi"] else ""
    return _xlsx(excel.excel_yoz(excel.tovarlar(**f).iterator(chunk_size=2000)),
                 f"Ombor {date.today():%d.%m.%Y}{qism}.xlsx")


def shablon(request):
    return _xlsx(excel.excel_yoz([]), "Ombor shabloni.xlsx")


def yuklash(request):
    form = ExcelYuklashForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            y = excel.fayldan_qoralama(d["fayl"], d["yoqlarini_yashir"], d["izoh"])
        except excel.ExcelXatosi as e:
            for sabab in e.sabablar:
                form.add_error("fayl", sabab)
        else:
            messages.success(request, "Fayl o'qildi. Ombor hali o'zgarmadi — o'zgarishlarni "
                                      "ko'rib chiqib «Qo'llash»ni bosing.")
            return redirect("ombor:yangilanish", y.pk)
    return render(request, "ombor/excel_yuklash.html", {"form": form})


def yangilanishlar(request):
    holat = request.GET.get("holat") or ""
    qs = OmborYangilanish.objects.all()
    if holat:
        qs = qs.filter(holat=holat)
    hisob = {f"n_{a}": Count("qatorlar", filter=Q(qatorlar__amal=a, qatorlar__chiqarilgan=False))
             for a in (Qator.YANGI, Qator.OZGARDI, Qator.YASHIRILDI, Qator.XATO)}
    qs = qs.annotate(**hisob).order_by("-yaratilgan")
    return render(request, "ombor/yangilanishlar.html", {
        "yangilanishlar": Paginator(qs, 30).get_page(request.GET.get("page")),
        "holat": holat, "holatlar": OmborYangilanish.HOLATLAR,
    })


TURLAR = [(Qator.YANGI, "Yangi"), (Qator.OZGARDI, "O'zgargan"), (Qator.YASHIRILDI, "Yashirilgan"),
          (Qator.XATO, "Xato"), ("chiqarilgan", "Chiqarilgan")]


def yangilanish(request, pk):
    y = get_object_or_404(OmborYangilanish, pk=pk)
    turi = request.GET.get("turi") or ""
    matn = (request.GET.get("q") or "").strip()
    qs = y.qatorlar.select_related("mahsulot")
    if turi == "chiqarilgan":
        qs = qs.filter(chiqarilgan=True)
    elif turi:
        qs = qs.filter(amal=turi, chiqarilgan=False)
    if matn:
        qs = qs.filter(Q(kod__startswith=matn) | Q(yangi__nom__icontains=matn)
                       | Q(eski__nom__icontains=matn))
    sanoq = y.sanoq()
    soralgan = {k: v for k, v in request.GET.items() if k != "page" and v}
    return render(request, "ombor/yangilanish.html", {
        "y": y, "sanoq": sanoq, "turi": turi, "matn": matn,
        "qatorlar": Paginator(qs, 100).get_page(request.GET.get("page")),
        "toqnash": excel.bekor_toqnashuvlari(y) if y.holat == y.QOLLANDI else [],
        "turlar": [(k, n, sanoq[k]) for k, n in TURLAR if sanoq[k]],
        "qidiruv_satri": urlencode(soralgan),
        "qollasa_boladi": any(sanoq[k] for k in (Qator.YANGI, Qator.OZGARDI, Qator.YASHIRILDI)),
    })


@require_POST
def yangilanish_amal(request, pk):
    y = get_object_or_404(OmborYangilanish, pk=pk)
    amal = request.POST.get("amal")
    try:
        if amal == "qollash":
            excel.qollash(y)
            s = y.sanoq()
            messages.success(request, f"Ombor yangilandi: {s['yangi']} ta yangi, "
                                      f"{s['ozgardi']} ta o'zgargan, {s['yashirildi']} ta yashirilgan.")
        elif amal == "bekor":
            excel.bekor_qil(y)
            messages.success(request, "Yangilanish bekor qilindi — ombor avvalgi holatiga qaytdi.")
        elif amal == "ochirish":
            if y.holat != y.QORALAMA:
                raise excel.ExcelXatosi("Faqat qoralamani o'chirish mumkin.")
            y.delete()
            messages.success(request, "Qoralama o'chirildi, ombor o'zgarmadi.")
            return redirect("ombor:yangilanishlar")
        elif amal == "xatolarni_chiqar":
            if y.holat != y.QORALAMA:
                raise excel.ExcelXatosi("Faqat qoralamani o'zgartirish mumkin.")
            n = y.qatorlar.filter(amal=Qator.XATO, chiqarilgan=False).update(chiqarilgan=True)
            messages.info(request, f"{n} ta xato qator chiqarib tashlandi.")
        else:
            raise Http404
    except excel.ExcelXatosi as e:
        for sabab in e.sabablar:
            messages.error(request, sabab)
    return redirect("ombor:yangilanish", y.pk)


def _keyingi(request, qator=None):
    manzil = request.POST.get("keyingi") or request.GET.get("keyingi") or ""
    if manzil.startswith("/") and not manzil.startswith("//"):
        return manzil
    return None


def _qoralama_qatori(request, pk):
    q = get_object_or_404(Qator.objects.select_related("yangilanish", "mahsulot"), pk=pk)
    if q.yangilanish.holat != OmborYangilanish.QORALAMA:
        messages.error(request, "Qo'llangan yangilanishni tahrirlab bo'lmaydi — kerak bo'lsa "
                                "uni bekor qiling.")
        return q, redirect("ombor:yangilanish", q.yangilanish_id)
    return q, None


def qator_tahrir(request, pk):
    q, rad = _qoralama_qatori(request, pk)
    if rad:
        return rad
    if q.amal == Qator.YASHIRILDI:
        messages.info(request, "Yashiriladigan qatorni faqat chiqarib tashlash mumkin.")
        return redirect("ombor:yangilanish", q.yangilanish_id)
    form = QatorForm(request.POST or None, initial=excel.qator_formasi_uchun(q))
    if request.method == "POST" and form.is_valid():
        xato = excel.qatorni_yangila(q, form.cleaned_data["holat"],
                                     form.cleaned_data["ogohlantirish"])
        if xato:
            form.add_error(None, xato)
        else:
            messages.success(request, f"Qator saqlandi (kod {q.kod}).")
            return redirect(_keyingi(request, q) or reverse("ombor:yangilanish", args=[q.yangilanish_id]))
    return render(request, "ombor/qator_tahrir.html", {
        "q": q, "form": form, "keyingi": _keyingi(request, q) or ""})


@require_POST
def qator_chiqar(request, pk):
    q, rad = _qoralama_qatori(request, pk)
    if rad:
        return rad
    q.chiqarilgan = not q.chiqarilgan
    q.save(update_fields=["chiqarilgan"])
    return redirect(_keyingi(request, q) or reverse("ombor:yangilanish", args=[q.yangilanish_id]))
