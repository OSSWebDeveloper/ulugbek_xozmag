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
server ham to'xtaydi. Server do'kon Wi-Fi'iga ham ochiq, oynada boshqa
kompyuterlar uchun manzil yoziladi (pastdagi «Ichki tarmoq (Wi-Fi)»).

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
   - miqdor kiritiladi → **Qo'shish** (narx so'ralmaydi);
   - qator qo'shilganda tovar **ombordan ayriladi** (kirim/chiqim tarixi yoziladi);
   - qator o'chirilsa tovar omborga **qaytadi**;
   - oxirida pastdagi **Jami** maydonlariga kelishilgan summa yoziladi
     (so'mlik alohida, dollarlik alohida) va **Yakunlash** bosiladi.
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

## Narx qayerda yoziladi

**Tovar kartochkasida narx bor** (`Mahsulot.narx`) — 1 sotuv birligi uchun,
tovarning valyutasida. U ombor ro'yxatida va kassadagi tovar kartasida
ko'rinib turadi, keyinchalik **elektron tarozi** shu narxdan foydalanadi.

Lekin narx **hisob-kitobga aralashmaydi**: chek va qarz summasi baribir
qo'lda yoziladi. Sabab do'kondagi savdolashuv — 183 000 so'mlik tovar
kelishilsa 180 000 ga ham ketadi. Narxlar kalkulyatorda uriladi, tizim esa
kelishilgan sonni yozib qo'yadi.

Shuning uchun kassada narx maydoni yo'q: tovar tanlanadi, miqdor yoziladi,
«Qo'shish». Pastdagi **Jami** maydoniga summa kiritilmaguncha chek ham,
qarz hujjati ham yakunlanmaydi.

Summa `Sotuv.jami` va `Qarz.jami` da saqlanadi, qatorlarda (`SotuvQator`,
`QarzQator`) faqat tovar va miqdor qoladi. Qarzdorning balansi qarz
hujjatlarining `jami` yig'indisidan chiqadi.

Shtrix kod va tarozi qo'shilgandan keyin ham shu qoida qoladi: kod tovarni
topadi, summa baribir qo'lda yoziladi (pastdagi «Kod, skaner va tarozi»).

## Kod, skaner va tarozi

Har bir tovarga **turgan joyiga qarab 5 xonali kod** beriladi: `00001` …
`99999` (v3.0.0 dan; oldin id bo'yicha 10 xonali edi — migratsiya raqamni
saqlab qisqartirdi: `0000000027` -> `00027`). Kod tovar kartasida va Excel
faylida yoziladi; bo'sh qoldirilsa navbatdagi bo'sh kod beriladi. Kod
o'zgartirilsa — o'sha tovarning etiketkasini qayta chop etish kerak.

Kassada va tarozida **kodning o'zi** uriladi, boshidagi nollarsiz ham bo'ladi:
`27` = `00027`. 50 kg li bolg'ani yoki sement qopini kassagacha ko'tarib kelish
shart emas — yorliqdagi raqam uriladi va tovar ekranga chiqadi.

Tovar kassaga (sotuv va qarz ekraniga) to'rt yo'l bilan tushadi, hammasi bitta
joyga (`tovarTanla()`) boradi:

| Yo'l | Qachon | Nima bo'ladi |
|---|---|---|
| Ro'yxatdan bosish | avvalgidek | tovar tanlanadi, miqdorni kassir yozadi |
| O'ng paneldagi **Kod** maydoni | og'ir tovar kassaga kelmaydi | tovar tanlanadi, miqdorni kassir yozadi |
| **Skanerlash** | tovarga yopishtirilgan etiketka | **darrov chekka qo'shiladi** — «Qo'shish» bosilmaydi |
| **Tarozi etiketkasi** | kg bilan sotiladigani | darrov qo'shiladi, og'irligi bilan |

Skanerlangan tovarning miqdori:

1. kodning o'zi aytgani — tarozi etiketkasidagi og'irlik;
2. bo'lmasa — tovar tanlanmasdan oldin **«Miqdor»** ga yozilgan son: `20` yozib
   sement qopini skanerlasa 20 qop tushadi;
3. bo'lmasa — **1**.

**Bir xil tovar qayta skanerlansa yangi qator ochilmaydi** — mavjud qatorning
miqdori oshadi: uchta rozetka o'qilsa chekda «Rozetka 3 dona» turadi. Bu qoida
qo'lda qo'shilganda ham ishlaydi (`ombor/xizmat.py`, `hujjatga_qosh`).
Qo'shilgan qator ko'rinadigan joyga siljiydi va bir lahza yonib turadi, kursor
esa yana «Kod» ga qaytadi — keyingi tovarni darrov skanerlash mumkin.

**Zavod shtrixlari ishlatilmaydi** — kassa faqat do'konning o'z etiketkasini
taniydi. Skaner qadoqdagi zavod shtrixini o'qib qo'ysa chekka hech narsa
tushmaydi, «etiketkani skanerlang» degan xabar chiqadi.

Kod hamma joyda ko'rinadi: tovar kartalarida, **tovar tanlash oynasining
qidiruv ro'yxatida** (har qator oldida ustun bo'lib; raqam bilan izlanganda mos
kelgan raqamlar belgilanadi — nega topilgani ko'rinsin), chek qatorlarida va
sotuvlar ro'yxatida.

### Skaner nega sozlamasiz ishlaydi

USB skaner kompyuterga **klaviatura** bo'lib ulanadi: kodni juda tez yozadi va
oxirida Enter bosadi. Odam bunchalik tez yozolmaydi — `static/js/skaner.js`
shundan bilib oladi (belgilar orasi 40 ms dan tez bo'lsa — skaner). Drayver ham,
port sozlamasi ham kerak emas; skanerning o'zida «Enter suffiksi» yoqilgan bo'lsin.

Fokus qayerda turganining ahamiyati yo'q — belgilar hujjat darajasida ushlanadi.
Skaner biror maydonga yozib yuborgan bo'lsa maydon avvalgi holatiga qaytariladi,
ya'ni qidiruv maydoniga kod tushib qolmaydi.

**Kodlar faqat raqamli bo'lsin.** Kompyuterda ruscha yoki o'zbekcha klaviatura
yoqilgan bo'lsa harfli kodlar buzilib tushadi.

### Qidirish qoidalari bitta joyda

Hammasi `ombor/kod.py` da. JS ularni takrorlamaydi — kiritilganini `/ombor/kod/`
ga yuboradi va tayyor javob oladi. Xuddi qoldiq `ombor/xizmat.py` dan boshqa
joyda o'zgarmagani kabi, kod ham bitta joyda o'qiladi. Tartib:

| Kiritilgan | Deb tushuniladi |
|---|---|
| 13 raqam, `2` bilan boshlanadi, nazorat raqami to'g'ri | tarozi etiketkasi (og'irligi bilan) |
| 1–10 raqam | tovar kodi, son sifatida o'qiladi: `7`, `00007`, etiketkadagi `000007` va eski 10 xonali `0000000007` — hammasi bitta tovar |
| 12 raqam, `77` bilan boshlanadi, nazorat raqami to'g'ri | rang (kolerovka) cheki — baza bo'yoq chekdagi miqdori bilan (pastdagi «Rang» bo'limi) |
| Qolgani (zavod shtrixi va h.k.) | topilmaydi — «etiketkani skanerlang» |

### Etiketka: tovar qo'shilganda shtrix tayyor

Tovar yaratilganda unga kod beriladi — **shu kodning o'zi uning shtrixi**. U
etiketka printerida chop etilib tovarga yopishtiriladi:

```
    Rozetka
 ║▌║│▌║║│║▌│║▌║   <- skaner o'qisa kassaga «000009» tushadi, tovar darrov chekka
     00009        <- kassir shu raqamni (yoki shunchaki 9 ni) uradi
```

Shtrix turi — **Code 128** (`ombor/shtrix.py`), EAN-13 emas: EAN-13 ning oxirgi
raqami har doim nazorat raqami, ya'ni yozuvdagi oxirgi 4 raqam tovar kodiga to'g'ri
kelmasdi va kassir boshqa raqam urib qo'yardi. Code 128 ning nazorat belgisi
chiziqlar ichida, yozuvga chiqmaydi. Code 128-C raqamlarni juftlab yozadi, 5 xonali
kod esa toq — shuning uchun shtrixda oldiga bitta `0` qo'shiladi (`000009`, 3 belgi;
`Mahsulot.etiketka_kodi`), shtrix 40×30 mm etiketkaga bemalol sig'adi. Chizish ZXing bilan
tekshirilgan (jadvalning hamma belgilari), testlarda esa chiziqlardan qaytadan
o'qib ko'riladi.

Chop etish — **brauzerning o'z chop etish oynasi** (`/ombor/<id>/etiketka/`):

- printer Windows'da o'rnatilgan bo'lsa bas, modeli muhim emas;
- etiketka o'lchami tanlanadi (40×30, 58×40, 50×30, 30×20 mm) va shu kompyuterda
  eslab qolinadi; har bir etiketka alohida sahifa, sahifa o'lchami (`@page`) —
  etiketka o'lchami;
- shtrix moduli 0,25 / 0,375 mm — 203 dpi printerda aniq 2 / 3 nuqta, chiziqlar
  buzilmaydi. Chrome chiqargan PDF 203 va 300 dpi da rasmga aylantirilib, shtrix
  qaytadan o'qib tekshirilgan;
- chop etish oynasida: printer — etiketka printeri, qog'oz — etiketka o'lchami,
  chekkalar — «Нет», masshtab — 100%.

Etiketka sahifasiga uch yo'l bilan kelinadi:

| Qachon | Qayerdan | Nechta nusxa |
|---|---|---|
| Yangi tovar qo'shilganda | saqlangach o'zi ochiladi | kelgan soni (20 dona — 20 ta, 3 rulon — 3 ta) |
| Mol kelganda | kirim oynasidagi **«Qo'shish va etiketka»** | kirim miqdori |
| Istalgan payt | ombor ro'yxatidagi printer tugmasi | 1 (o'zgartirsa bo'ladi) |

Metr, kg, litr bilan o'lchanadigan tovarga (yoki juda ko'piga — 5000 g'isht) bitta
etiketka taklif qilinadi.

Nusxalar soni `Mahsulot.etiketka_soni()` da; bir yo'la ko'pi bilan 500 ta.

### Tarozi kodi

Tarozi o'z etiketkasini **EAN-13** da bosadi — ichida og'irlik ham bor
(`ichki_shtrix`). Tuzilishi:

```
2 | 000027 | 01250 | 4
^     ^        ^     ^
|     |        |     nazorat raqami
|     |        og'irlik grammda (01250 = 1,25 kg); 00000 — og'irliksiz
|     tovar kodining oxirgi 6 raqami (tarozidagi PLU)
do'kon ichki prefiksi
```

Prefiks `2` — GS1 da do'kon o'zi bosadigan kodlar uchun ajratilgan (20–29),
shuning uchun hech qanday zavod kodi bilan to'qnashmaydi. Nazorat raqami
to'g'ri kelmasa kod qabul qilinmaydi — skaner yarim o'qiganda noto'g'ri tovar
sotilib ketmasin.

**Tarozini shu formatga sozlash kerak:** prefiks `2`, PLU 6 raqam, og'irlik
5 raqam (grammda). Tarozidagi PLU — tovar kodi, oldiga bitta nol qo'shiladi
(`00027` -> `000027`). Tarozi narxni emas, **og'irlikni** kodga
joylasin: narx do'konda savdolashiladi, shuning uchun tizimda hisobga olinmaydi.

Tarozining o'z ichki ro'yxati bor — undagi PLU raqami va nomi bazadagi bilan
bir xil bo'lishi kerak. Kg bilan sotiladigan tovar 20–30 tadan oshmasa qo'lda
kiritib qo'yiladi.

### Ombor ro'yxati

Birinchi ustunda 5 xonali kod turadi. Qidiruv maydoni nom bilan ham, kod bilan
ham ishlaydi. Skanerlansa o'sha zahoti **kirim oynasi** ochiladi — mol
tushirayotganda qo'l band bo'ladi, ro'yxatdan izlab o'tirishga vaqt yo'q.

Ro'yxat 50 tadan sahifalanadi (Excel'dan 10 000 dan ortiq tovar keladi).
Filtrlar: valyuta, **«Kam qolganlar birinchi»** (omborda qolgan hajmiga teskari
tartib — eng kam qolgani tepada), «Faqat tugaganlar», «Yashirilganlar ham».
«Omborni Excel'ga yuklab olish» aynan shu filtr va tartibda yuklab beradi.

### Ombor: Excel orqali yangilash (v3.0.0)

Ombor → «Excel'dan yangilash». Hammasi `ombor/excel.py` da, sahifalari
`ombor/excel_views.py` da.

1. **Fayl yuklanadi — ombor hali o'zgarmaydi.** Fayldan **qoralama** tuziladi:
   har qator ombordagi bilan solishtiriladi — yangi tovar, o'zgargan, o'zgarmagan
   yoki xato.
2. **Ko'rib chiqiladi.** Eski qiymat ustidan chizilib, yangisi yonida turadi.
   Xato qatorni «Tuzatish» bilan to'g'rilash, istalgan qatorni «chiqarib
   tashlash» mumkin.
3. **«Qo'llash».** Qoldiq o'zgarsa tovar tarixiga «Tuzatish» bo'lib yoziladi,
   yangi tovarning qoldig'i — «Kirim (boshlang'ich qoldiq)». Qoralama tuzilgach
   sotuv bo'lgan bo'lsa ham yo'qolmaydi: faqat fayl o'zgartirgan maydonlar yoziladi.
4. **«Bekor qilish».** Ombor shu yangilanishdan oldingi holatiga qaytadi, qoldiq
   farqi tarixga teskari «Tuzatish» bo'lib yoziladi. Tovar keyin yana o'zgargan
   bo'lsa (sotuv, kirim, keyingi yangilanish) bekor qilinmaydi — qaysi
   yangilanish xalaqit berayotgani ko'rsatiladi, avval o'sha bekor qilinadi.

Fayl qoidalari:

- Sarlavhalar: `Kod`, `Tovar nomi`, `Birlik`, `Qoldiq`, `Narxi`, `Valyuta`
  (tartibi muhim emas). Bo'sh shablon va hozirgi ombor shu ko'rinishda yuklab olinadi.
- Tovar avval **kod** bo'yicha (kod — joy), kod bo'lmasa **nomi** bo'yicha
  (harfma-harf bir xil) topiladi; topilmasa — yangi tovar.
- **Faylda yo'q ustun o'zgarmaydi**: faqat `Kod` + `Qoldiq` fayli faqat qoldiqni yangilaydi.
- Do'kon dasturining «Products …xlsx» eksporti (`Товар`, `Остаток`,
  `Sotish narxi` = «180726 UZS») to'g'ridan-to'g'ri o'qiladi; boshqa narx
  ustunlari (ko'cha, diller, internet) hozircha olinmaydi.
- «Faylda yo'q tovarlarni yashirish» — tovar o'chmaydi (sotuv tarixi unga
  bog'langan), `faol=False` bo'ladi.
- Narx 4 xonali kasrgacha saqlanadi (`3,5432 $`).

10 169 qatorli haqiqiy fayl: tekshirish ~8 s, qo'llash ~6 s, yuklab olish ~6 s.

**Diqqat — kassa:** tovar tanlash oynasi (sotuv, qarz, rang ekranlari) hamma
faol tovarni birdaniga chizadi. 10 000 tovarda bu ekranlar ~10 s ochiladi va
7,6 MB bo'ladi — buni alohida hal qilish kerak.

## Rang (kolerovka) — Soruda mashinasi

Do'konda bo'yoqqa rang qo'shadigan mashina bor — **Soruda SO-T800**
(Jiangxi Suoruida, dasturi «Soruda tinting system», mashina kompyuteriga
o'rnatilgan). Uning dasturida rang **palitra kodi** bilan tanlanadi. Yon menyudagi
**Rang** bo'limi shu mashina yonida ishlaydi:

1. **Katalog varag'i** (`/rang/varaq/`) — mashina oldiga qo'yiladi. Har bir
   rangning namunasi, kodi, nomi va ostida **shtrix**. Shtrix — Soruda
   kodining **o'zi**: skaner uni Soruda'ning kod maydoniga xuddi odam
   yozgandek tushiradi, do'kon sahifasida esa rangni topadi.
2. Mijoz rangni ko'rsatadi, sotuvchi skanerlaydi — Soruda rangni tayyorlaydi.
3. **Stansiya** (`/rang/`, shu kompyuter brauzerida) — rang shtrixi,
   bankadagi do'kon etiketkasi (baza bo'yoq) skanerlanadi, kolerovka narxi
   yoziladi → **«Chek chiqarish»** (Enter). Maxsus chek chop etiladi.
4. Mijoz chekni kassaga olib boradi. Kassir skanerlaydi: baza bo'yoq
   chekdagi miqdori bilan **o'zi tushadi** (ombordan shu yerda ayriladi),
   kassirga «To'lanadi: 210 000 so'm» xabari chiqadi, chek qatorida rang kodi
   (`RAL 3020`) turadi. Summa boshqa joydagidek «Jami» ga qo'lda yoziladi.

```
   ULUG'BEK XOZMAG
 RANG (KOLEROVKA) CHEKI
 № 4       23.09.2026 22:20
 RAL 3020  Yo'l qizil
 Emulsiya baza oq 10 kg
 1 dona × 185 000   185 000 so'm
 Kolerovka           25 000 so'm
 TO'LANADI       210 000 so'm
  ║▌║│▌║║│║▌│║▌║│║▌║▌│   <- kassada skanerlanadi
   77 000000004 8
```

### Chek bir marta ishlaydi

Kassa chekni hujjatga bog'laydi (`rang/kassa.py`), stansiyaning o'ng
panelida holati ko'rinadi:

| Holat | Qachon |
|---|---|
| To'lanmagan | chek chiqdi, kassadan o'tmadi. Oldingi kunlardagisi qizil — bo'yoq pulsiz ketgan bo'lishi mumkin |
| Kassada | ochiq chekka qo'shildi |
| To'landi / Qarzga yozildi | sotuv yoki qarz hujjati yakunlandi |
| Bekor qilingan | mijoz fikridan qaytdi (chek sahifasidagi tugma; to'langanini bekor qilib bo'lmaydi) |

Ikkinchi marta skanerlansa qabul qilinmaydi («allaqachon chek #12 ga
qo'shilgan») — bo'yoq ombordan ikki marta ayrilmaydi. Kassada qator
o'chirilsa yoki sotuv bekor qilinsa chek yana bo'shaydi. Qarz ekranida ham
xuddi shunday ishlaydi.

Chek kodi — 12 raqam: `77` + chek raqami (9 raqam) + nazorat raqami
(`ombor/kod.py`). Tovar kodi (10) va tarozi (13) bilan uzunligi farq qiladi.
Stansiyada chek skanerlansa o'sha chek ochiladi (qayta chop etish).

### Ranglar katalogi

**Ranglar** sahifasi (`/rang/ranglar/`): qo'shish, tahrirlash, yashirish va
**yuklash** — Soruda'dan yoki Excel'dan ro'yxat bir yo'la qo'yiladi:

    RAL 3020;Yo'l qizil;#CC0605

Kod — Soruda dasturiga **qanday yozilsa aynan shunday** (bo'shlig'i bilan).
Faqat lotin harflari, raqamlar va belgilar: kirill harfni skaner Soruda'ga
to'g'ri yoza olmaydi. Qo'lda izlaganda katta-kichik harf va bo'shliq farq
qilmaydi, kodning oxiri ham yetadi (`3020` → `RAL 3020`). Raqamli rang kodi
tovarning 4 raqami bilan adashmaydi: stansiyada avval katalog qaraladi.

Shtrix — Code 128 (`rang/shtrix.py`): harfli qismi B to'plamida, raqamlari
C da (qisqaroq). Varaqda modul 0,254 mm — 600 dpi printerda aniq 6 nuqta.
Chrome'da A4 PDF qilib, 300 dpi rasmga aylantirib, 213 ta shtrixning
hammasi qaytadan o'qib tekshirilgan (4 va 5 ustunli, bo'sh katakli variant).

Namuna uchun **RAL Classic** (213 rang, `rang/namuna.py`) bir tugma bilan
yuklanadi. Haqiqiy Soruda palitrasi kelgach «To'plamni o'chirish» bilan
olib tashlanadi (chek chiqqan ranglar o'chmaydi, yashiriladi).

Printer rangni aniq bermaydi — varaqda **«Bo'sh katak»** tanlansa rang
o'rnida bo'sh joy qoladi, unga rang kartasidan haqiqiy namuna yopishtiriladi.

### Chop etish

Brauzerning o'z oynasi, printer Windows'da o'rnatilgan bo'lsa bas:

- **Chek** — 80 yoki 58 mm (tanlov shu kompyuterda eslab qolinadi). Sahifa
  balandligi chekning o'z uzunligicha (`static/js/rang_chek.js`), shtrix
  moduli 0,375 mm — 203 dpi termoprinterda aniq 3 nuqta. «Chek chiqarish»
  dan keyin chek o'zi chop etiladi va stansiyaga qaytadi.
- **Varaq** — A4, 3/4/5 ustun, har bir to'plam yangi sahifadan.

Mashina yonidagi kompyuterda brauzerni `--kiosk-printing` bilan ochsa
chop etish oynasi ham chiqmaydi — chek darrov printerga ketadi:

    msedge.exe --kiosk-printing http://<server>:8000/rang/

### Narx

**Kolerovka narxi** stansiyada qo'lda yoziladi (so'mda). Baza bo'yoq narxi
ombordagi tovar narxidan olinadi. Chekdagi «To'lanadi» = baza × miqdor +
kolerovka; dollarlik baza so'mga qo'shilmaydi («25 $ va 15 000 so'm»).
Kassada summa baribir kassir yozadi — savdolashuv qoidasi o'zgarmaydi.

### Ichki tarmoq (Wi-Fi) — chek bazaga tarmoq orqali boradi

Rang mashinasi o'z kompyuteriga ega (Windows, Soruda dasturi shunga
o'rnatilgan). Kassa esa boshqa kompyuterda. Ikkalasi do'kondagi **bitta
Wi-Fi routerga** ulanadi, Xozmag serveri shu ichki tarmoqda turadi —
**internet shart emas**:

```
 [Soruda kompyuteri] --Wi-Fi--> [router] <--Wi-Fi/kabel-- [server = kassa kompyuteri]
   stansiya (brauzer)                                        Xozmag + baza
   chek yaratiladi  ------------ tarmoq orqali ----------->  bazaga yoziladi
                                                             kassada skanerlanadi
```

- **Server** Wi-Fi'ga ochiq: o'rnatilgan dastur `0.0.0.0` da tinglaydi
  (`ishga_tushir.py`), `SERVERXOZMAG.bat` ham. Kichik oynada (va bat
  oynasida) boshqa kompyuterlar uchun manzil yoziladi:
  `http://192.168.1.5:8000/` va kompyuter nomi bilan. Stansiya
  sarlavhasida ham yashil «Wi-Fi: …/rang/» turadi. Manzillarni
  `config/tarmoq.py` topadi.
- Birinchi ochilganda Windows **«Разрешить доступ / Ruxsat berish»** so'raydi —
  ikkala belgini qo'yib ruxsat bering. Bekor qilinsa boshqa kompyuterlar
  ulana olmaydi (Brandmauer → «Разрешение взаимодействия с приложением» dan
  Xozmag'ga belgi qo'yiladi). Tarmoq turi **Частная (Private)** bo'lsin.
- IP o'zgarib qolmasligi uchun routerda server kompyuteriga doimiy IP
  (DHCP reservation) bering yoki kompyuter nomi bilan ulaning.
- Sayt baribir login va parol so'raydi — Wi-Fi'ga ulangan begona odam
  kira olmaydi. Wi-Fi'ning o'ziga ham parol qo'ying.

### Soruda kompyuteri uchun papka

`soruda_kompyuter/` — fleshkaga ko'chirilib, rang mashinasi kompyuterida
ochiladi (`OQING.txt`):

| Fayl | Nima qiladi |
|---|---|
| `1-STANSIYA-YORLIGI.bat` | ish stolida «Rang stansiyasi» yorlig'i: Edge alohida oynada (`--app`), chek so'ramasdan printerga (`--kiosk-printing`), alohida profil — login eslab qolinadi. Server manzilini so'raydi va ulanishni tekshiradi |
| `2-SORUDA-MALUMOTI.bat` | Soruda qayerga o'rnatilganini o'zi topadi (ochiq oyna, yorliqlar, papka nomlari) va uning ma'lumot fayllarini (rang kodlari, palitra, formulalar, yozuvlar), fayllar ro'yxatini, oxirgi soatlarda o'zgargan fayllarni, printerlar va tarmoqni zip qiladi. Soruda ma'lumotni SQL Server'da saqlasa jadvallar shu yerda CSV ga o'qiladi (faqat `SELECT`). Soruda fayllari **faqat o'qiladi**. Boshqa dasturlarning fayllari zipga tushmaydi — faqat ro'yxatda; brauzer oynalari (sarlavhasida «Soruda» bo'lsa ham) Soruda deb olinmaydi |

Soruda dasturining **o'z rang kodlari va palitrasi** bor — katalog RAL
namunasi o'rniga shu bilan to'ldiriladi. Zip kelgach: palitra katalogga
avtomatik yuklanadi, Soruda'da tayyorlangan bo'yoq yozuvi esa (qaysi faylga
tushishi ko'rilgach) Wi-Fi orqali bazaga **o'zi** yuboriladigan qilinadi —
stansiyada qayta skanerlash kerak bo'lmaydi.

### Hali aniq emas

- Soruda'ning palitra va yozuvlari qaysi faylda, qanday formatda —
  `2-SORUDA-MALUMOTI.bat` zipi kelsa aniqlanadi;
- mashina yonidagi chek printeri modeli (zipda printerlar ro'yxati bor);
- kolerovka narxi rangga/hajmga qarab o'zi hisoblansinmi (narx guruhlari).

## So'm va dollar — ikkita alohida hisob

Do'konga mol ikki xil keladi: bir qismi so'mda, bir qismi dollarda.
**Klientning asosiy sharti — ular hech qayerda qo'shilib ketmasligi.**

- **Tovar qo'shishda** «Qaysi pulda keladi» so'raladi (so'm yoki dollar).
  Dollarlik tovar ro'yxatlarda va kassada yashil **$** belgisi bilan turadi —
  kassir summani qaysi maydonga yozishni shundan biladi. Kartochkadagi narx
  ham o'sha valyutada ko'rinadi: «45 $» yoki «12 000 so'm».
- **Kassada ikkita «Jami» maydoni**: biri so'm, biri dollar. Bittasi to'lsa
  yetadi. Tizim ularni hech qachon qo'shmaydi, bir-biriga aylantirmaydi.
- **Kurs** o'sha yerda yoziladi (dollarlik summa bo'lsa majburiy). Standart
  qiymati **Markaziy bankdan** olinadi, kerak bo'lsa ustidan yoziladi. Kurs
  faqat yozib qo'yiladi — summalar baribir alohida qoladi.
- **Qarzdorning ikkita balansi** bor: so'm qarzi va dollar qarzi. To'lov ham
  valyutasi bilan yoziladi va faqat o'sha hisobni kamaytiradi.
- **Kunlik tushum** ham ikki qatorda: «250 000 so'm» va «40 $».

Maydonlar: `Sotuv.jami` / `Sotuv.jami_dollar` / `Sotuv.kurs`, xuddi shunday
`Qarz` da; `Mahsulot.valyuta`, `Tolov.valyuta`.

## Dollar kursi qayerdan olinadi

Kassadagi **Kurs** maydonining standart qiymati O'zbekiston Markaziy bankidan
olinadi (`ombor/markaziy_bank.py`, manba: `cbu.uz`). Bank tiyinigacha aytadi
(11 809,82) — do'konda butun so'mga yaxlitlanadi.

Do'kon internetsiz ham ishlashi kerak, shuning uchun:

- kurs **kuniga bir marta** so'raladi va bazaga yoziladi (`DollarKursi`);
- so'rov 3 soniyadan uzoq kutmaydi — sayt bankni kutib turmaydi;
- olib bo'lmasa oldingi kunning bank kursi, u ham bo'lmasa **oxirgi marta
  qo'lda yozilgan kurs** qoladi; hech qanday xatolik chiqmaydi;
- olib bo'lmagan bo'lsa bir soatdan keyin qayta urinadi.

Maydon ustiga sichqoncha borsa qiymat qayerdan kelgani yozilib turadi.
Kassir baribir ustidan o'zi yozishi mumkin — do'kon kursi bank kursidan
farq qilishi normal.

## Oldindan to'lov

Mijoz qarz yozdirayotganda bir qismini darrov to'lashi mumkin: 500 000 lik mol
oladi, 200 000 ini shu yerda beradi, daftarda 300 000 qoladi.

Qarz ekranining pastida **«Oldindan»** maydonlari turadi (so'mlik va dollarlik
alohida, boshqa joydagidek). Standart qiymati **0** — hech kim to'lamagan bo'lsa
hech narsa yozilmaydi. Hujjat summasidan ortiq to'lash mumkin emas: aks holda
balans manfiyga ketib «qarzi −100 000 so'm» degan ma'nosiz son chiqardi.

Oldindan to'lov alohida maydonda **saqlanmaydi** — oddiy `Tolov` bo'lib yoziladi
va `Tolov.qarz` orqali o'sha hujjatga bog'lanadi. Sabab: balans hisobi bitta
joyda (to'lovlar yig'indisida) qolishi kerak, aks holda ikkita manba paydo
bo'lib bir-biriga zid bo'lib qolardi. Qarzdor kartochkasida hujjat yonida
«Oldindan to'langan: 200 000 so'm» degan nishon turadi.

## Naqd sotuvda pul yetmasa (autosplit)

Mijoz 150 000 lik mol oldi, qo'lida 100 000 bor. Qolgan 50 000 qarzga yoziladi
— **sahifa almashmasdan**: kassir chekni tashlab ketolmaydi, mijoz qarshisida
turibdi.

**«Jami» — har doim chekning to'liq summasi** (kelishilgan narx). Kassir uni
yozadi, keyin «Jami» panelidagi **«Qarzga»** tugmasini bosadi. Oynachada
«Jami» o'zi ikkiga bo'linadi:

```
Jami        150 000 so'm      <- pastdagi «Jami» dan, o'zgarmaydi
To'ladi   [ 100 000 ] so'm    <- mijoz bergan pul
Qarzga    [  50 000 ] so'm    <- o'zi hisoblanadi: Jami − To'ladi
```

Bittasi yozilsa ikkinchisi o'zi to'ladi: «To'ladi» ga 100 000 yozilsa qarz
50 000, «Qarzga» ga 30 000 yozilsa to'langani 120 000. Oynacha ochilganda
hammasi qarzga turadi (To'ladi = 0). So'm va dollar **alohida** bo'linadi;
dollar qismi chekda dollar bo'lsagina ko'rinadi. To'langan pul jamidan ko'p
bo'lsa qizil ogohlantirish chiqadi va tasdiqlab bo'lmaydi. «Jami» yozilmagan
bo'lsa oynacha ochilmaydi — avval summa kerak.

Oynachaning qolgan qismi:

- o'ngda — qarzdorlar ro'yxati, familiya/ism/hudud bo'yicha qidiruv bilan;
- **«Yangi qarzdor»**: mijoz birinchi marta qarz olayotgan bo'lsa shu yerda
  yaratiladi (`/yangi/oyna/` ga so'rov ketadi, sahifa yangilanmaydi) va darrov
  tanlanadi;
- sensorli rejimda o'z raqamlar klaviaturasi.

Tasdiqlangach tugmada ikki qator turadi: «Qarzga · Aliyev Vali» va
«50 000 so'm». Formaning yashirin maydoniga **to'langan pul** tushadi, qarz
esa har doim Jami − To'ladi — kassir «Jami» ni keyin o'zgartirsa tugmadagi
qarz ham darrov o'zgaradi. Yakunlash baribir **bitta oddiy POST**, hisobni
server qayta tekshiradi (`sotuv/views.py`, `qarzni_oqi`). Fikridan qaytsa
oynachadagi «Olib tashlash».

Hisob qanday yuritiladi:

| Nima | Qayerga tushadi |
|---|---|
| Naqd olingan pul | `Sotuv.jami` — **kunlik tushum** shundan chiqadi |
| Qarzga qolgani | alohida `Qarz` hujjati, `Qarz.sotuv` orqali chekka bog'lanadi |
| Chekning to'liq summasi | saqlanmaydi, `Sotuv.umumiy_jami` = naqd + qarz |
| Tovarlar | chekda qoladi, qarz hujjatida **qator bo'lmaydi** |

Tovarlar ko'chirilmasligi muhim: aks holda ombordan ikki marta ayrilardi. Qarz
hujjati shu sababli faqat puldan iborat, izohida «Chek #12 dan qolgan qarz»
deb turadi. Qarzdor kartochkasida «Chek #12 dan» nishoni ostida chekning
tovarlari ko'rinadi va ularni shu yerdan qaytarish mumkin.

Sotuvlar ro'yxatida chek yonida to'liq summa, uning ostida «naqd: … · qarzga:
…» va kimga yozilgani turadi. Kun ko'rsatkichlari ham ikki xil: **Kunlik
tushum** (kassaga tushgan pul) va **Qarzga yozildi** (shu kunning cheklaridan
daftarga o'tgani).

Pulning **hammasi** qarzga ketsa (To'ladi = 0) kassaga hech narsa tushmaydi.
Hammasi to'langan bo'lsa qarz yozilmaydi — server «qarzga hech narsa
qolmadi» deb qaytaradi.

## Qaytarib berish (vozvrat)

Mijoz olgan tovarni qaytarib kelishi mumkin va **qaytarish to'liq bo'lmasligi
mumkin**: 20 qop sementning 15 tasi ishlatilib, 5 tasi qaytadi.

Naqd sotuvlar ro'yxatida va qarzdor kartasida har bir tovar qatorida
**«Qaytarish»** tugmasi turadi. U ochadigan sahifada:

| Maydon | Nima |
|---|---|
| Qancha qaytarildi | sotilganidan ko'p bo'lmaydi; bir necha marta qaytarsa qo'shilib boradi |
| Qaytarilgan pul (so'm) | hujjat summasidan ayriladi |
| Qaytarilgan pul ($) | dollarlik qismidan ayriladi, so'mga aralashmaydi |

Yozilgach: tovar **omborga qaytadi** (tarixda alohida «Qaytarish» turi bilan
ko'rinadi), qatorda «5 qop qaytarilgan» bo'lib qoladi, hujjat summasidan
qaytarilgan pul ayriladi. Qarzda bu qarzdorning balansini kamaytiradi — mijoz
olmagan mol uchun qarzdor bo'lib qolmaydi.

**Chekning bir qismi qarzga yozilgan bo'lsa** pul avval o'sha qarzdan ayriladi,
qolgani mijozning qo'liga qaytariladi (`qaytarishni_taqsimla`). 200 000 lik
chek: 50 000 naqd, 150 000 qarz; 60 000 lik mol qaytsa — qarz 90 000 ga
tushadi, kassadan pul chiqmaydi. Qarzdan ko'pi bilan qarzdorning **hozirgi**
qarzicha ayriladi: u qarzini to'lab bo'lgan bo'lsa pul qo'lga qaytadi, balans
manfiyga ketmaydi. Qaytarish sahifasida bu qoida oldindan yozib turadi.

Qaytarish faqat yakunlangan chekdan bo'ladi — ochiq chekdagi tovar qatorni
o'chirib qaytariladi.

Maydonlar: `SotuvQator.qaytarilgan` / `QarzQator.qaytarilgan` (miqdor),
`Sotuv.qaytarilgan_summa(_dollar)` / `Qarz.qaytarilgan_summa(_dollar)` (pul).
Hisoblar `sof_jami` orqali yuradi.

## Cheklar bazada qoladi

Yakunlangan chek ham, **bekor qilingan** chek ham bazada saqlanadi — keyin
«o'sha kuni nima bo'lgan edi?» degan savolga javob beradigan yozuv kerak.
Bekor qilingan chek ro'yxatda xira ko'rinadi, nishoni bor va kunlik tushumga
qo'shilmaydi; tovarlari o'sha zahoti omborga qaytadi. Faqat **bo'sh chek**
(bironta tovar qo'shilmagani) o'chiriladi — unda yozib qo'yadigan narsa yo'q.

**Yopilgan chekka tegilmaydi.** Brauzerning «Orqaga» tugmasi yakunlangan
chekning kassa ekranini qaytarib berardi — unga tovar qo'shish, qatorni
o'chirish yoki chekni bekor qilish mumkin edi. Endi bunday so'rov o'sha kunning
ro'yxatiga qaytariladi («Chek #11 yakunlangan — uni endi o'zgartirib
bo'lmaydi»). Yakunlash bitta shartli `UPDATE` bilan bo'ladi: «Yakunlash» ikki
marta bosilsa ham qarz ikki marta yozilmaydi. Qarz ekranida ham xuddi shunday
(`yopiq_hujjat`) — oldindan to'lov ikki marta tushmaydi.

`Sotuv.sana` — chek **yopilgan** payt. Kecha ochilib bugun yakunlangan chek
puli bugungi tushumga tushadi.

## Bildirishnomalar

Xabarlar sahifani surib yubormaydi: **o'ng yuqorida kichkina** qalqib chiqadi
va **5 soniyadan keyin o'zi o'chadi** (bosilsa darrov). Kassa ekranida joy
tor — katta xabar qatori butun joylashuvni pastga suradi va ish buziladi.
Kodi: `static/js/bildirishnoma.js`, uslubi `.xabarlar` / `.xabar`.

## Ish tartibi: sotuv

Bosh sahifadagi **Sotuv** — do'kondagi savdo cheki:

1. **Skanerlang** — tovar darrov chekka tushadi (1 dona; bir xili qayta
   skanerlansa miqdori oshadi). Tovar kassaga keltirilmasa (og'ir) yoki
   etiketkasi o'qilmasa: kursor **«Kod»** da turadi (sichqoncha rejimida),
   etiketkadagi yirik 4 raqam urib Enter → miqdor → Enter. Tovar
   qo'shilgach kursor yana «Kod» ga qaytadi, ya'ni butun chek klaviaturadan
   teriladi. «Yangi tovar» (F2) ham avvalgidek.
2. Tovar qo'shilishi bilan ombordan ayriladi; qatorni o'chirsa qaytadi.
3. Pastdagi **Jami** ga chekning kelishilgan summasi yoziladi (so'm va dollar
   alohida). Pul yetmasa — «Qarzga» (yuqoridagi bo'lim).
4. **Sotuvni yakunlash.** Jami yozilmagan yoki dollar bor-u kurs yo'q bo'lsa
   sahifa yuborilmaydi, darrov ogohlantirish chiqadi.

Chek sarlavhasida raqami, ochilgan vaqti va tovarlar soni turadi; yonidagi
**«Sotuvlar»** tugmasi kunlik ro'yxatni ochadi. Kunlik tushum va qarzga
yozilgani o'sha sahifada.

## Pul maydonlari: raqamlar o'zi bo'linadi

Summa yozilayotganda raqamlar **o'zi guruhlanadi** (autosplit): `200000`
yozilsa maydonda `200 000` bo'lib turadi — kassir nollarni sanab o'tirmaydi.
Kassadagi Jami / Kurs / Oldindan, qarzga oynachasi, qaytarish, to'lov qabul
qilish va tovar narxi — hammasida bir xil.

Kodi `static/js/forma.js` da: maydonga `pul-maydon` klassi beriladi, kasr
xonalari `data-kasr` bilan (so'mda 0 — tiyin yozilmaydi, dollar va kursda 2).
Kasr vergul bilan ko'rinadi (`12,5 $`), nuqta yozilsa ham vergulga aylanadi.
Kursor o'z raqamining yonida qoladi, numpad bilan yozganda ham ishlaydi.

Server hech narsani o'zgartirmaydi: `ombor/xizmat.py` dagi `tozala` bo'shliqlarni
(oddiy va uzilmas) olib tashlaydi, `VergulliDecimal` ham shuni ishlatadi.

Shu faylda formalar uchun yana ikki qoida bor:

| Atribut | Nima qiladi |
|---|---|
| `data-tasdiq="Savol?"` | yuborishdan oldin so'raydi. Avval `onsubmit="confirm('…')"` edi — «Qo'shilgan» dagi apostrof JS satrini buzib, chek **so'ramasdan** bekor bo'lib ketardi |
| `data-bir-marta` | forma bir marta yuboriladi: tugma ikki bosilsa ikkinchi so'rov ketmaydi |

## Bir birlikda olinib boshqasida sotiladigan tovarlar

Ba'zi tovar do'konga bir birlikda keladi, mijozga boshqa birlikda sotiladi —
masalan **polietilen lenta rulonda olinib metrda sotiladi**.

Qoida oddiy: **ombor qoldig'i har doim sotuv birligida yuritiladi.** Sotuv, qarz
va qoldiq — hammasi metrda. Faqat **kirim** paytida rulondan metrga o'tkaziladi.

Yangi tovar qo'shishda **«Birlik o'zgaradi»** degan richag bor. O'chiq bo'lsa
forma oddiy: birlik, narx va qoldiq. Yoqilsa forma qadoq bo'yicha savol beradi va
qoldiqni o'zi hisoblaydi — operator metrni ko'paytirib o'tirmaydi:

| Savol | Misol | Nima bo'ladi |
|---|---|---|
| Necha rulon keldi | `3` | boshlang'ich qoldiq shundan chiqadi |
| Kelgan birligi | `rulon` | do'konga shu ko'rinishda keladi |
| Sotiladigan birligi | `metr` | mijozga shunda sotiladi, qoldiq ham shunda |
| 1 rulonda nechta metr | `100` | o'tkazish koeffitsiyenti |
| Narxi | `3 500` | bitta **sotuv** birligi uchun |

Pastda jonli izoh turadi:
*«1 rulon = 100 metr · 3 rulon = 300 metr omborga tushadi ·
1 metr 3 500 so'm · 1 rulon 350 000 so'm»*.
Saqlangach tarixga ham `3 rulon = 300 metr` deb yoziladi.

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

- `qarz/` — Hudud, Qarzdor, Qarz, QarzQator, Tolov; `Tolov.qarz` — oldindan
  to'lov qaysi hujjatga tegishli, `Qarz.sotuv` — chekdan qolgan qarz
- `sotuv/` — Sotuv, SotuvQator (naqd savdo)
- `rang/` — Rang (katalog), Buyurtma (rang cheki); `rang/kassa.py` — chekni
  kassa hujjatiga bog'lash, `rang/shtrix.py` — harfli Code 128,
  `rang/yuklash.py` — ro'yxatni matndan yuklash; uslubi `static/css/rang.css`
- `config/tarmoq.py` — ichki tarmoq (Wi-Fi) manzillari: oynada, bat'da va
  stansiyada ko'rsatiladi
- `soruda_kompyuter/` — rang mashinasi kompyuteri uchun: stansiya yorlig'i va
  Soruda ma'lumotlarini yig'uvchi
- `ombor/` — Mahsulot, OmborHarakati; `ombor/xizmat.py` — qoldiqni
  o'zgartiruvchi yagona joy (qarz ham, sotuv ham shuni chaqiradi);
  `ombor/kod.py` — kod/shtrix/tarozi kodi bo'yicha tovar topadigan yagona joy;
  `ombor/shtrix.py` — etiketkadagi Code 128 shtrixni chizadi.
  Birlik o'tkazish: `Mahsulot.sotuvga_aylantir()` — boshqa hech qayerda ko'paytirilmaydi
- `templates/`, `static/css/uslub.css`, `static/js/` — interfeys
- `templates/ikonlar.html` — SVG ikonlar to'plami (`<use href="#i-...">`)
- `static/js/ombor.js` — ombor ekranlaridagi jonli hisob va kirim numpadi
- `static/js/skaner.js` — skanerni klaviaturadan ajratadi va `/ombor/kod/` ga so'raydi
- `templates/ombor/etiketka.html`, `static/js/etiketka.js` — etiketka chop etish
  (o'lcham, nusxalar soni, `@page`)
- `static/js/sotuv_qarz.js`, `templates/sotuv/qarz_oyna.html` — «Jami» ni
  to'langan va qarz qismga bo'lish (autosplit) va yangi qarzdor oynachasi
- `static/js/forma.js` — pul maydonlarida raqamlarni guruhlash, `data-tasdiq`,
  `data-bir-marta` (har bir sahifada yuklanadi)
- `versiya.py`, `versiya.txt`, `VERSIYALAR.md` — versiyalash
- `config/sinov.py` — testlar uchun asos (sayt login talab qilgani uchun
  har bir test kirib oladi)
- `qarz/management/commands/xodim.py` — xodim hisobi
- `qarz/templatetags/statik_versiya.py` — CSS/JS kesh yangilash (`{% statik '...' %}`)

## Keyin qilinadigan ishlar

- 13 ta hududning haqiqiy nomlarini qo'yish (`qarz/management/commands/boshlangich.py`)
- Foydalanuvchi (receptionist) hisobi va parol bilan kirish
- Chek chop etish, hisobotlar
- Etiketkani bir bosishda, oynasiz chop etish — printer modeli ma'lum bo'lgach
  TSPL yoki ZPL buyrug'i `win32print` orqali (hozir brauzerning chop etish oynasi)
- Tarozining PLU ro'yxatini bazadan eksport qilish
