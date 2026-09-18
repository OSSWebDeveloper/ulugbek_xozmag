# Ulug'bek Xozmag

Xozmag (qurilish mollari do'koni) uchun **qarz daftari + ombor organiseri**.
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

### Maxfiy kalit

Ombor ochiq bo'lgani uchun `SECRET_KEY` kodda turmaydi. Birinchi ishga
tushirishda `.secret_key` fayli o'zi yasaladi va shu kompyuterda qoladi
(git'ga tushmaydi). Xohlasangiz `XOZMAG_SECRET_KEY` muhit o'zgaruvchisi
bilan berish mumkin.

Ma'lumotlar bazasi (`db.sqlite3`) ham git'ga tushmaydi — mijoz ma'lumoti
hech qachon omborga chiqmaydi.

## Versiya

Dastur versiyasi **yon menyu pastida** ko'rinib turadi (`v1.0.0`) — mijoz
«qaysi versiya ishlayapti?» deganda aytishi oson.

Yagona manba — `versiya.txt`. Uni qo'lda tahrirlamang:

```bash
python versiya.py                        # hozirgi versiyani ko'rsatadi
python versiya.py 1.1.0 "Qisqa izoh"     # versiyani oshiradi
python versiya.py 1.1.0 "Izoh" --push    # + GitHub'ga yuboradi
```

Skript `versiya.txt` ni yangilaydi, `VERSIYALAR.md` tepasiga sana bilan yangi
qator qo'shadi, shu ikki faylni commit qiladi va `v1.1.0` degan teg qo'yadi.
Boshqa o'zgargan fayllar commitga tushmaydi — avval ularni o'zingiz commit
qiling (yoki `--hammasi` bayrog'ini bering).

CSS va JS manzillariga fayl vaqti qo'shiladi (`uslub.css?v=1789704728`,
`qarz/templatetags/statik_versiya.py`) — yangilanishdan keyin mijoz brauzeri
eski uslubni ushlab qolmaydi.

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

## Ikkita richag

Yon menyu ostida ikkita richag bor, ikkalasining tanlovi ham brauzerda saqlanadi.

**Sensor** — o'lchamlar va joylashuvni **o'zgartirmaydi**, faqat:

| | O'chiq | Yoniq |
|---|---|---|
| O'ngdagi raqamlar klaviaturasi | yo'q | bor |
| Raqamli maydon bosilganda | klaviaturadan yoziladi | numpad qalqib chiqadi |
| Kirim ekranida | numpad yo'q | numpad maydon ostida doim turadi |
| Matn maydoni bosilganda | klaviaturadan yoziladi | saytning o'z ekran klaviaturasi chiqadi |
| Klaviatura yorliqlari (F2, Enter) | ko'rinadi | yashiriladi |

**Kechki** — quyuq (yoqiq) va yorug' (o'chiq) ko'rinish o'rtasida almashtiradi.

Ekran klaviaturasi (`static/js/klaviatura.js`) Windows klaviaturasi emas, saytning o'ziniki:
QWERTY, katta harf (⇧), raqam/belgi rejimi (123) va o'zbekcha apostrof (`o'`, `g'`) uchun
alohida tugma.

## Ish tartibi: naqd sotuv

Bosh sahifadagi **Sotuv** — qarzga yozilmaydigan savdo: tovarlar qo'shiladi,
«Mijoz berdi» ga olingan pul kiritiladi, qaytim o'zi hisoblanadi, yakunlangach
tovarlar ombordan ayriladi. Kunlik tushum **Sotuvlar** sahifasida ko'rinadi.

## Bir birlikda olinib boshqasida sotiladigan tovarlar

Ba'zi tovar do'konga bir birlikda keladi, mijozga boshqa birlikda sotiladi —
masalan **polietilen lenta rulonda olinib metrda sotiladi**.

Qoida oddiy: **ombor qoldig'i har doim sotuv birligida yuritiladi.** Sotuv, qarz,
qoldiq va narx — hammasi metrda. Faqat **kirim** paytida rulondan metrga o'tkaziladi.

Tovar kartochkasida (`Ombor → tovar → ✏`) «Boshqa birlikda olinadimi?» bo'limi bor:

| Maydon | Ma'nosi | Misol |
|---|---|---|
| Sotuv birligi | mijozga qanday sotiladi | `metr` |
| Olish birligi | do'konga qanday keladi (bo'sh bo'lsa — bir xil) | `rulon` |
| 1 rulonda nechta metr | o'tkazish koeffitsiyenti | `100` |
| Narxi | **bitta sotuv birligi** narxi | `3 500 so'm / metr` |

Shundan keyin:

- **Kirim ekranida** «Qaysi birlikda» degan ikkita tugma chiqadi — `rulon` yoki `metr`.
  `2 rulon` yozilsa omborga **200 metr** tushadi; yarim rulon qolsa `metr` tanlab
  `40` deb yoziladi. Pastda jonli izoh: *«2 rulon = 200 metr qo'shiladi · yangi
  qoldiq: 500 metr (5 rulon)»*. Sensorli rejimda maydon ostida raqamlar
  klaviaturasi doim turadi — qalqib chiquvchi oyna izohni to'sib qo'ymaydi.
- **Ombor ro'yxatida** ikkala son ham ko'rinadi: `500` metr / `5 rulon`, yonida
  `1 rulon = 100 metr` nishoni.
- **Kirim/chiqim tarixida** asl yozuv saqlanadi: `2 rulon = 200 metr`.
- **Kassada** tovar tanlanganda «Omborda: 500 metr · 5 rulon» yoziladi, lekin
  sotish faqat metrda — kassirning ishi o'zgarmaydi.

Olish birligi tanlanmagan tovar (g'isht, rozetka) avvalgidek ishlaydi — kirim
ekranida hech qanday qo'shimcha savol chiqmaydi.

Birliklar ro'yxati (`ombor/models.py`, `Birlik`): dona, kg, metr, litr, qop, quti,
rulon, buxta, pachka, list, tonna. Yangi birlik kerak bo'lsa shu ro'yxatga qo'shiladi.

## Tuzilishi

- `qarz/` — Hudud, Qarzdor, Qarz, QarzQator, Tolov
- `sotuv/` — Sotuv, SotuvQator (naqd savdo)
- `ombor/` — Mahsulot, OmborHarakati; `ombor/xizmat.py` — qoldiqni o'zgartiruvchi
  yagona joy (qarz ham, sotuv ham shuni chaqiradi).
  Birlik o'tkazish: `Mahsulot.sotuvga_aylantir()` — boshqa hech qayerda ko'paytirilmaydi
- `templates/`, `static/css/uslub.css`, `static/js/` — interfeys
- `templates/ikonlar.html` — SVG ikonlar to'plami (`<use href="#i-...">`)
- `static/js/ombor.js` — ombor ekranlaridagi jonli hisob va kirim numpadi
- `versiya.py`, `versiya.txt`, `VERSIYALAR.md` — versiyalash
- `qarz/templatetags/statik_versiya.py` — CSS/JS kesh yangilash (`{% statik '...' %}`)

## Keyin qilinadigan ishlar

- 13 ta hududning haqiqiy nomlarini qo'yish (`qarz/management/commands/boshlangich.py`)
- Foydalanuvchi (receptionist) hisobi va parol bilan kirish
- Chek chop etish, hisobotlar
