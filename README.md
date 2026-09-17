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

## Sensor / sichqoncha rejimi

O'ng yuqoridagi **richag** ikki rejimni almashtiradi (tanlov brauzerda saqlanadi):

| | Sichqoncha rejimi | Sensor rejimi |
|---|---|---|
| Tugma balandligi | 56 px | 82 px |
| Shrift | 17 px | 21 px |
| Raqam maydoni bosilganda | klaviaturadan yoziladi | ekranda numpad chiqadi |
| Klaviatura yorliqlari (F2, Enter) | ko'rinadi | yashiriladi |

## Tuzilishi

- `qarz/` — Hudud, Qarzdor, Qarz, QarzQator, Tolov
- `ombor/` — Mahsulot, OmborHarakati (kirim/chiqim tarixi)
- `templates/`, `static/css/uslub.css`, `static/js/` — sodda kassa uslubidagi interfeys

## Keyin qilinadigan ishlar

- 13 ta hududning haqiqiy nomlarini qo'yish (`qarz/management/commands/boshlangich.py`)
- Foydalanuvchi (receptionist) hisobi va parol bilan kirish
- Chek chop etish, hisobotlar
