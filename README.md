# Ulug'bek Xozmak

Xozmak (qurilish mollari do'koni) uchun **qarz daftari + ombor organiseri**.
Eskirgan qog'oz daftar o'rniga ishlaydi.

## Ishga tushirish

```bash
python manage.py migrate
python manage.py boshlangich   # 13 ta hudud + sinov tovarlari
python manage.py runserver
```

Sayt: http://127.0.0.1:8000/

Admin panel kerak bo'lsa:

```bash
python manage.py createsuperuser
```

## Ish tartibi (receptionist uchun)

1. **Bosh sahifa** — qarzdor keldi: *Oldin qarz olgan* yoki *Yangi qarzdor*.
2. **Oldin olgan** → ism/familiya/telefon bo'yicha qidiriladi, hudud bo'yicha filtr bor.
3. **Yangi** → Ism, Familiya, Telefon, Hudud to'ldiriladi → **Yaratish** bosilgach darrov
   qarz yozish ekraniga o'tadi.
4. **Qarz yozish ekrani** (kassa ko'rinishi):
   - **+ Yangi tovar** → skladdagi tovarlar katta kartalar bo'lib chiqadi, bittasi tanlanadi;
   - narx avtomatik qo'yiladi (kerak bo'lsa o'zgartiriladi), miqdor kiritiladi;
   - summa jonli hisoblanadi → **Qo'shish**;
   - qator qo'shilganda tovar **ombordan ayriladi** (kirim/chiqim tarixi yoziladi);
   - qator o'chirilsa tovar omborga **qaytadi**;
   - oxirida **Yakunlash** — qarz daftarga yoziladi.
5. **Qarzdor kartasi** — jami olgan / to'lagan / qolgan qarz, qarzlar tarixi, to'lov qabul qilish.

## Sensor rejimi

Yon menyu ostidagi **richag** sensor rejimini yoqadi/o'chiradi (tanlov brauzerda saqlanadi).
U faqat shu narsalarni o'zgartiradi — o'lchamlar va joylashuv **o'zgarmaydi**:

| | O'chiq (sichqoncha) | Yoniq (sensor) |
|---|---|---|
| O'ngdagi raqamlar klaviaturasi | yo'q | bor |
| Raqam maydoni bosilganda | klaviaturadan yoziladi | ekranda numpad qalqib chiqadi |
| Klaviatura yorliqlari (F2, Enter) | ko'rinadi | yashiriladi |

## Ish tartibi: naqd sotuv

Bosh sahifadagi **Sotuv** — qarzga yozilmaydigan savdo: tovarlar qo'shiladi,
«Mijoz berdi» ga olingan pul kiritiladi, qaytim o'zi hisoblanadi, yakunlangach
tovarlar ombordan ayriladi. Kunlik tushum **Sotuvlar** sahifasida ko'rinadi.

## Tuzilishi

- `qarz/` — Hudud, Qarzdor, Qarz, QarzQator, Tolov
- `sotuv/` — Sotuv, SotuvQator (naqd savdo)
- `ombor/` — Mahsulot, OmborHarakati; `ombor/xizmat.py` — qoldiqni o'zgartiruvchi
  yagona joy (qarz ham, sotuv ham shuni chaqiradi)
- `templates/`, `static/css/uslub.css`, `static/js/` — interfeys
- `templates/ikonlar.html` — SVG ikonlar to'plami (`<use href="#i-...">`)

## Keyin qilinadigan ishlar

- 13 ta hududning haqiqiy nomlarini qo'yish (`qarz/management/commands/boshlangich.py`)
- Foydalanuvchi (receptionist) hisobi va parol bilan kirish
- Chek chop etish, hisobotlar
