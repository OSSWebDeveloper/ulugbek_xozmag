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

### Kirish

Sayt butunlay yopiq — har qanday sahifa login talab qiladi
(`LoginRequiredMiddleware`). Xodim hisobi shu buyruq bilan yaratiladi:

```bash
python manage.py xodim reception
```

Parol berilmasa login bilan bir xil bo'ladi. **Do'konga o'rnatilgach
almashtiring** — ombor ochiq, ya'ni bu qoida hammaga ma'lum:

```bash
python manage.py xodim reception --parol <yangi parol>
```

Admin panelga ham kiradigan hisob kerak bo'lsa `--boshqaruvchi` qo'shing.
Chiqish — yon menyu pastidagi tugma. Seans 12 soatdan keyin tugaydi.

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

## O'rnatuvchi (mijoz kompyuteriga)

Mijozda Python ham, Django ham bo'lishi shart emas — hammasi bitta faylning
ichida.

Yig'ish (bir marta, o'zimizda):

    python -m pip install pyinstaller pillow
    python ornatuvchi/qur.py

Natija: `dist/XozmagOrnatish.exe` — mijozga beriladigan yagona fayl.

O'rnatgich nima qiladi:

- dasturni `%LOCALAPPDATA%\Programs\UlugbekXozmag` ga qo'yadi (administrator
  huquqi kerak emas);
- ish stoliga va Boshlash menyusiga yorliq qo'yadi;
- «Dasturlar va imkoniyatlar» ro'yxatiga yozadi;
- yoniga `Ochirish.exe` va `OCHIRISH.bat` qo'yadi.

Dastur ochilganda o'zi Django serverini ko'taradi, bo'sh portni topadi (8000
dan boshlab) va brauzerni ochadi. Ekranda kichkina oyna qoladi — u yopilsa
server ham to'xtaydi.

Baza dastur papkasida emas, `%LOCALAPPDATA%\UlugbekXozmag\db.sqlite3` da
turadi. Shuning uchun dasturni ustidan qayta o'rnatish bazaga tegmaydi.

### O'chirish

Uch yo'ldan biri:

- Boshlash → Parametrlar → Ilovalar → «Ulug'bek Xozmag» → O'chirish;
- dastur papkasidagi `Ochirish.exe`;
- dastur papkasidagi `OCHIRISH.bat` — savol-javobli oddiy skript.

Uchalasi ham bazani o'chirishni alohida so'raydi: «yo'q» deyilsa qarzdorlar
va sotuvlar joyida qoladi.

## Ish tartibi (receptionist uchun)

1. **Bosh sahifa** — qarzdor keldi: *Oldin qarz olgan* yoki *Yangi qarzdor*.
2. **Oldin olgan** → ikki yo'l: butun ro'yxatni ochish yoki **hududni tanlash**.
   Hududlar 13 ta katta tugma bo'lib chiqadi, har birida nechta qarzdor va qancha
   qarz borligi yozilgan; hudud bosilsa o'sha hududning qarzdorlari ko'rinadi.
   **Qarzdor** bo'limi ham xuddi shunday ochiladi. Ism yozib qidirish yo'q —
   do'konda qarzdor hudud bo'yicha eslanadi.
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
   Qarzdan ortiq to'lov qabul qilinmaydi: balans manfiyga ketib «−5 000 so'm»
   kabi ma'nosiz son chiqmasligi uchun.

## Ikkita richag

Yon menyu ostida ikkita richag bor, ikkalasining tanlovi ham brauzerda saqlanadi.

**Sensor** — o'lchamlar va joylashuvni **o'zgartirmaydi**, faqat:

| | O'chiq | Yoniq |
|---|---|---|
| O'ngdagi raqamlar klaviaturasi | yo'q | bor |
| Kirim ekranida | numpad yo'q | numpad maydon yonida turadi |
| Matn maydoni bosilganda | klaviaturadan yoziladi | saytning o'z ekran klaviaturasi chiqadi |
| Klaviatura yorliqlari (F2, Enter) | ko'rinadi | yashiriladi |

**Kechki** — quyuq (yoqiq) va yorug' (o'chiq) ko'rinish o'rtasida almashtiradi.

Ekran klaviaturasi (`static/js/klaviatura.js`) Windows klaviaturasi emas, saytning
o'ziniki: planshetdagidek pastda, butun enlikda turadi va mavzu bilan birga rangini
o'zgartiradi. **Faqat harf** — QWERTY, katta harf (⇧), o'zbekcha apostrof (`o'`, `g'`)
uchun alohida tugma, bo'sh joy va «Tayyor». Raqam va maxsus belgi yo'q.

Raqamli maydonlar uchun **qalqib chiquvchi oyna yo'q**: raqamlar klaviaturasi maydon
yonida, sahifaning o'zida turadi (kassaning o'ng paneli, kirim ekranining o'ng ustuni).
Oyna bo'lib chiqqanda u jonli izohni to'sib qo'yardi.

## Ish tartibi: naqd sotuv

Bosh sahifadagi **Sotuv** — qarzga yozilmaydigan savdo: tovarlar qo'shiladi,
«Mijoz berdi» ga olingan pul kiritiladi, qaytim o'zi hisoblanadi, yakunlangach
tovarlar ombordan ayriladi. Kunlik tushum **Sotuvlar** sahifasida ko'rinadi.

## Bir birlikda olinib boshqasida sotiladigan tovarlar

Ba'zi tovar do'konga bir birlikda keladi, mijozga boshqa birlikda sotiladi —
masalan **polietilen lenta rulonda olinib metrda sotiladi**.

Qoida oddiy: **ombor qoldig'i har doim sotuv birligida yuritiladi.** Sotuv, qarz,
qoldiq va narx — hammasi metrda. Faqat **kirim** paytida rulondan metrga o'tkaziladi.

Yangi tovar qo'shishda **«Birlik o'zgaradi»** degan richag bor. O'chiq bo'lsa
forma oddiy: birlik, narx, qoldiq. Yoqilsa forma qadoq bo'yicha savol beradi va
qoldiqni o'zi hisoblaydi — operator metrni ko'paytirib o'tirmaydi:

| Savol | Misol | Nima bo'ladi |
|---|---|---|
| Necha rulon keldi | `3` | boshlang'ich qoldiq shundan chiqadi |
| Kelgan birligi | `rulon` | do'konga shu ko'rinishda keladi |
| Sotiladigan birligi | `metr` | mijozga shunda sotiladi, qoldiq ham shunda |
| 1 rulonda nechta metr | `100` | o'tkazish koeffitsiyenti |
| Narxi | `3 500` | bitta **sotuv** birligi uchun |

Pastda jonli izoh turadi:
*«1 rulon = 100 metr · 3 rulon = 300 metr omborga tushadi · 1 metr 3 500 so'm ·
1 rulon 350 000 so'm»*. Saqlangach tarixga ham `3 rulon = 300 metr` deb yoziladi.

**Tahrirlashda** «necha qadoq keldi» so'ralmaydi — qoldiq allaqachon bor, yangi
partiya Kirim ekranidan kiritiladi. O'sha yerda qoldiq sotuv birligida
ko'rsatiladi va yonida `= 3 rulon` deb turadi.

Shundan keyin:

- **Kirim ekranida** «Qaysi birlikda» degan ikkita tugma chiqadi — `rulon` yoki `metr`.
  `2 rulon` yozilsa omborga **200 metr** tushadi; yarim rulon qolsa `metr` tanlab
  `40` deb yoziladi. Pastda jonli izoh: *«2 rulon = 200 metr qo'shiladi · yangi
  qoldiq: 500 metr (5 rulon)»*. Sensorli rejimda maydon ostida raqamlar
  klaviaturasi doim turadi — qalqib chiquvchi oyna izohni to'sib qo'ymaydi.
- **Ombor ro'yxatida** ikkala son ham ko'rinadi, yonida `1 rulon = 100 metr`
  nishoni.

**Qoldiq butun qadoq bilan aytiladi.** Mix dona bilan sotilib pachkada olinsa
va 1 pachkada 1000 ta bo'lsa, omborda 5020 ta qolganda `5,02 pachka` emas,
**`5 pachka 20 dona`** deb yoziladi — do'konda shunday sanaladi. Butun qadoq
chiqsa ortig'i aytilmaydi (`3 rulon`), bitta qadoqqa yetmasa faqat ortig'i
(`40 metr`). Kasr ham ishlaydi: `7 rulon 37,5 metr`.

Bu `Mahsulot.qadoq_matni` da hisoblanadi; `static/js/ombor.js` dagi
`qadoqMatni()` xuddi shu qoidani jonli izohlar uchun takrorlaydi.
- **Kirim/chiqim tarixida** asl yozuv saqlanadi: `2 rulon = 200 metr`.
- **Kassada** tovar tanlanganda «Omborda: 500 metr · 5 rulon» yoziladi, lekin
  sotish faqat metrda — kassirning ishi o'zgarmaydi.

Olish birligi tanlanmagan tovar (g'isht, rozetka) avvalgidek ishlaydi — kirim
ekranida hech qanday qo'shimcha savol chiqmaydi.

Birliklar ro'yxati (`ombor/models.py`, `Birlik`): dona, kg, metr, litr, qop, quti,
rulon, o'ram, pachka, list, tonna. Yangi birlik kerak bo'lsa shu ro'yxatga qo'shiladi.

## Kirim — alohida sahifa emas

Ombor ro'yxatida tovar satriga bosilsa kirim **ichki oyna** bo'lib ochiladi:
`/ombor/<pk>/kirim/?oyna=1` faqat forma qismini qaytaradi (`kirim_forma.html`),
JS uni oynaga joylaydi. Forma oddiy POST bilan yuboriladi — server mantig'i
o'zgarmagan. Qalam va soat tugmalari (`data-kirimsiz`) o'z sahifalariga olib
boradi. `/ombor/<pk>/kirim/` manzili ham ishlaydi, u to'liq sahifa qaytaradi.

## Joylashuv qoidasi: scrollsiz

Sayt bitta ekranga sig'ishi kerak — kassir sichqoncha g'ildiragini aylantirib
o'tirmasin. Buning uchun:

- Butun sayt **90% o'lchamda** chiziladi: `:root { --kolam: .9; zoom: var(--kolam) }`.
  Shu bilan brauzerning **o'z** ochiluvchi ro'yxatlari (`<select>`) ham kichrayadi —
  11 ta birlik endi scrollsiz sig'adi. O'lchamni o'zgartirish uchun faqat
  `--kolam` ni almashtiring.
- `body` balandligi `calc(100vh / var(--kolam))` — aks holda pastda bo'sh
  chiziq qolardi. `body` ning o'zi hech qachon siljimaydi (`overflow: hidden`).
- Media so'rovlar chegaralari ham `--kolam` ga ko'paytirilgan: `zoom` ular
  baholangandan keyin qo'llanadi, ya'ni 1080 CSS px = 972 haqiqiy piksel.
- Tovar kartochkasi ikki ustunli (`.forma-setka`) — bir ustunda bo'lganda
  1290×630 ekranga sig'masdi.
- Kirim ekranida sensorli rejimda maydonlar chapda, raqamlar klaviaturasi
  o'ngda (`.kirim-setka`).
- Ro'yxat sahifalarida (`.sahifa-toliq`) sarlavha va qidiruv joyida turadi,
  faqat jadval ichi siljiydi; jadval sarlavhasi tepada yopishib qoladi.
- Qarzdor kartasida ham ko'rsatkichlar joyida, ro'yxatlar o'z ustunida siljiydi.

Yangi sahifa qo'shganda 1290×630 da tekshiring: `.sahifa` ning
`scrollHeight` va `clientHeight` i teng bo'lishi kerak.

## Ishlab chiqish eslatmasi

Django 6 dan boshlab shablonlar `DEBUG=True` da ham keshlanadi. Shuning uchun
`config/settings.py` da DEBUG rejimida keshsiz yuklagichlar qo'yilgan — aks
holda shablon o'zgarsa sayt qayta ishga tushirilmaguncha eski holat ko'rinadi.
Python fayllari o'zgarsa baribir qayta ishga tushirish kerak.

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
- `config/sinov.py` — testlar uchun asos (sayt login talab qilgani uchun
  har bir test kirib oladi)
- `qarz/management/commands/xodim.py` — xodim hisobi
- `qarz/templatetags/statik_versiya.py` — CSS/JS kesh yangilash (`{% statik '...' %}`)

## Keyin qilinadigan ishlar

- 13 ta hududning haqiqiy nomlarini qo'yish (`qarz/management/commands/boshlangich.py`)
- Foydalanuvchi (receptionist) hisobi va parol bilan kirish
- Chek chop etish, hisobotlar
