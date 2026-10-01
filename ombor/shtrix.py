"""Etiketkadagi shtrix kod — Code 128 (C to'plami).

Nega EAN-13 emas: uning oxirgi raqami har doim nazorat raqami. Etiketkada
esa kassir yozuvdan **oxirgi 4 raqamni** o'qib uradi — ular tovar kodining
oxiri bo'lishi shart. Code 128 ning nazorat belgisi chiziqlar ichida turadi,
yozuvga chiqmaydi, ya'ni etiketkada tovar kodi aynan o'zicha ko'rinadi:

    ║▌║│▌║║│║▌│║   <- skaner o'qisa kassaga «0000000027» tushadi
    000000 0027     <- kassir «0027» ni uradi

Ikkala yo'l ham `ombor/kod.py` dagi bitta qoidaga boradi (kodning oxiri).
C to'plami raqamlarni juftlab yozadi — 10 raqamli kod bor-yo'g'i 5 belgi,
shtrix kichik etiketkaga ham sig'adi. Deyarli barcha skanerlarda Code 128
zavoddan yoqilgan bo'ladi.
"""

# Har bir belgi: chiziq, oraliq, chiziq, oraliq, chiziq, oraliq kengliklari
# (modulda, jami 11). 103–105 — boshlanish (A, B, C), 106 — tugash (13 modul).
NAQSHLAR = (
    "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312",
    "132212", "221213", "221312", "231212", "112232", "122132", "122231", "113222",
    "123122", "123221", "223211", "221132", "221231", "213212", "223112", "312131",
    "311222", "321122", "321221", "312212", "322112", "322211", "212123", "212321",
    "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
    "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121",
    "313121", "211331", "231131", "213113", "213311", "213131", "311123", "311321",
    "331121", "312113", "312311", "332111", "314111", "221411", "431111", "111224",
    "111422", "121124", "121421", "141122", "141221", "112214", "112412", "122114",
    "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
    "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112",
    "421211", "212141", "214121", "412121", "111143", "111341", "131141", "114113",
    "114311", "411113", "411311", "113141", "114131", "311141", "411131", "211412",
    "211214", "211232", "2331112",
)
BOSHLASH_C = 105
TUGASH = 106
JIM_ZONA = 10          # ikki chetdagi bo'sh joy, modulda (standart: kamida 10)


def belgilar(raqamlar):
    """Raqamlar qatorini Code 128-C belgilariga aylantiradi (nazorat belgisi bilan)."""
    if not raqamlar.isdigit() or len(raqamlar) % 2:
        raise ValueError("Code 128-C uchun juft sonli raqamlar kerak.")
    qiymatlar = [BOSHLASH_C] + [int(raqamlar[i:i + 2]) for i in range(0, len(raqamlar), 2)]
    nazorat = (qiymatlar[0] + sum(q * i for i, q in enumerate(qiymatlar[1:], 1))) % 103
    return qiymatlar + [nazorat, TUGASH]


def chiziqlar(raqamlar):
    """Qora chiziqlar: [(boshlanishi, eni), ...] modulda, jim zona hisobga olingan.

    Ikkinchi qiymat — butun shtrixning eni (jim zonalar bilan).
    """
    natija, x = [], JIM_ZONA
    for belgi in belgilar(raqamlar):
        for i, en in enumerate(NAQSHLAR[belgi]):
            en = int(en)
            if i % 2 == 0:                      # juft o'rinlar — qora chiziq
                natija.append((x, en))
            x += en
    return natija, x + JIM_ZONA


def svg(raqamlar):
    """Shtrixning SVG si. O'lchami viewBox da modulda — etiketkada CSS uni mm ga
    cho'zadi (modul eni etiketka o'lchamiga qarab tanlanadi)."""
    qora, eni = chiziqlar(raqamlar)
    rects = "".join(f'<rect x="{x}" width="{en}" height="1"/>' for x, en in qora)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {eni} 1" '
            f'preserveAspectRatio="none" shape-rendering="crispEdges" '
            f'data-modullar="{eni}" role="img" aria-label="Shtrix kod {raqamlar}">'
            f'<rect width="{eni}" height="1" fill="#fff"/><g fill="#000">{rects}</g></svg>')
