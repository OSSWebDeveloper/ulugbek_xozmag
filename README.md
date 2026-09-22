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

Har bir tovarga yaratilganda **kod** beriladi — `0000000001` dan boshlab, id
bo'yicha. Kod bir marta beriladi va hech qachon o'zgarmaydi: o'zgarsa bosilgan
yorliqlarning hammasi yaroqsiz bo'lib qolardi.

Kassada va tarozida **oxirgi 4 raqam** uriladi. 50 kg li bolg'ani yoki sement
qopini kassagacha ko'tarib kelish shart emas — yorliqdagi `0027` uriladi va
tovar ekranga chiqadi.

Tovar endi to'rt yo'l bilan tanlanadi, hammasi bitta joyga (`tovarTanla()`) boradi:

| Yo'l | Qachon | Nima bo'ladi |
|---|---|---|
| Ro'yxatdan bosish | avvalgidek | tovar tanlanadi |
| O'ng paneldagi **Kod** maydoni | og'ir tovar kassaga kelmaydi | tovar tanlanadi |
| **Skanerlash** | zavod shtrixi bor tovar | tovar tanlanadi (quti kodi bo'lsa miqdor ham) |
| **Tarozi etiketkasi** | kg bilan sotiladigani | tovar tanlanadi, og'irlik miqdorga tushadi |

Miqdor faqat kodning o'zi aytganda to'ladi (tarozi yoki quti). Qolgan hollarda
bo'sh qoladi — do'konda miqdor kamdan-kam 1 ta bo'ladi.

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
| 13 raqam, `2` bilan boshlanadi, nazorat raqami to'g'ri | do'kon etiketkasi yoki tarozi kodi |
| Bazadagi zavod shtrixi | o'sha tovar (va kodning o'z miqdori) |
| 1–10 raqam | tovar kodining oxiri: `7` ham, `0007` ham bitta tovar |

### Zavod shtrixlari

Tovar kartochkasidagi **Zavod shtrixlari** maydoniga skanerlanadi — skaner Enter
bosgani uchun har bir kod o'zi alohida qatorga tushadi. Qatorni o'chirsangiz kod
ham o'chadi. Quti kodi bo'lsa yoniga qutidagi sonini yozing:

```
4780123456789
4780000000017 1000
```

Ikkinchi qator skanerlansa chekka 1 dona emas, **1000 dona** tushadi.

Ombor ro'yxatida notanish shtrix skanerlansa dastur «shu kod bilan yangi tovar
qo'shilsinmi?» deb so'raydi va kartochkani kod to'ldirilgan holda ochadi. Katalog
shu bilan **mol tushirish paytida** o'zi to'lib boradi — hammasini bir kunda
o'tirib kiritish shart emas.

### Ichki etiketka va tarozi kodi

O'zimiz bosadigan shtrix bazada saqlanmaydi — tovar kodidan hisoblanadi
(`Mahsulot.etiketka_kodi`), ya'ni ikki joyda turib bir-biriga zid bo'lib
qolmaydi. Tuzilishi — 13 raqamli EAN-13:

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
5 raqam (grammda). Tarozidagi PLU — tovarning oxirgi 4 raqami, oldiga ikkita
nol qo'shiladi (`0027` -> `000027`). Tarozi narxni emas, **og'irlikni** kodga
joylasin: narx do'konda savdolashiladi, shuning uchun tizimda hisobga olinmaydi.

Tarozining o'z ichki ro'yxati bor — undagi PLU raqami va nomi bazadagi bilan
bir xil bo'lishi kerak. Kg bilan sotiladigan tovar 20–30 tadan oshmasa qo'lda
kiritib qo'yiladi.

### Ombor ro'yxati

Birinchi ustunda kod turadi: yirik 4 raqam (kassada uriladigani) va ostida to'liq
kod. Qidiruv maydoni nom bilan ham, kod bilan ham ishlaydi. Skanerlansa o'sha
zahoti **kirim oynasi** ochiladi — mol tushirayotganda qo'l band bo'ladi,
ro'yxatdan izlab o'tirishga vaqt yo'q.

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

## Naqd sotuvda pul yetmasa

Mijoz 150 000 lik mol oldi, qo'lida 100 000 bor. Qolgan 50 000 qarzga yoziladi
— **sahifa almashmasdan**: kassir chekni tashlab ketolmaydi, mijoz qarshisida
turibdi.

«Jami» panelidagi **«Qarzga qoldirish»** tugmasi oynacha ochadi. Oynachada:

- chapda — qarzga qoladigan summa (so'm va dollar alohida) va sensorli rejimda
  o'z raqamlar klaviaturasi;
- o'ngda — qarzdorlar ro'yxati, familiya/ism/hudud bo'yicha qidiruv bilan;
- pastda — **«Yangi qarzdor»**: mijoz birinchi marta qarz olayotgan bo'lsa shu
  yerda yaratiladi (`/yangi/oyna/` ga so'rov ketadi, sahifa yangilanmaydi) va
  darrov tanlanadi.

Tasdiqlangach oynacha yopiladi, tugmada «Qarzga: 50 000 so'm» deb turadi —
kassir yakunlashdan oldin nima bo'layotganini ko'rib turadi. Tanlov «Jami»
formasining yashirin maydonlariga tushadi, ya'ni yakunlash baribir **bitta
oddiy POST** bo'lib qoladi. Fikridan qaytsa oynachadagi «Olib tashlash».

Hisob qanday yuritiladi:

| Nima | Qayerga tushadi |
|---|---|
| Naqd olingan pul | `Sotuv.jami` — **kunlik tushum** shundan chiqadi |
| Qarzga qolgani | alohida `Qarz` hujjati, `Qarz.sotuv` orqali chekka bog'lanadi |
| Tovarlar | chekda qoladi, qarz hujjatida **qator bo'lmaydi** |

Tovarlar ko'chirilmasligi muhim: aks holda ombordan ikki marta ayrilardi. Qarz
hujjati shu sababli faqat puldan iborat, izohida «Chek #12 dan qolgan qarz»
deb turadi va qarzdor kartochkasida «Chek #12 dan» nishoni ko'rinadi.
Sotuvlar ro'yxatida ham chek yonida kimga yozilgani va qancha ekani turadi.

Pulning **hammasi** qarzga ketsa «Jami» bo'sh qolishi mumkin — kassaga hech
narsa tushmagan bo'ladi. Qarzdor tanlanmagan bo'lsa esa «Jami» avvalgidek
majburiy.

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

Maydonlar: `SotuvQator.qaytarilgan` / `QarzQator.qaytarilgan` (miqdor),
`Sotuv.qaytarilgan_summa(_dollar)` / `Qarz.qaytarilgan_summa(_dollar)` (pul).
Hisoblar `sof_jami` orqali yuradi.

## Cheklar bazada qoladi

Yakunlangan chek ham, **bekor qilingan** chek ham bazada saqlanadi — keyin
«o'sha kuni nima bo'lgan edi?» degan savolga javob beradigan yozuv kerak.
Bekor qilingan chek ro'yxatda xira ko'rinadi, nishoni bor va kunlik tushumga
qo'shilmaydi; tovarlari o'sha zahoti omborga qaytadi. Faqat **bo'sh chek**
(bironta tovar qo'shilmagani) o'chiriladi — unda yozib qo'yadigan narsa yo'q.

## Bildirishnomalar

Xabarlar sahifani surib yubormaydi: **o'ng yuqorida kichkina** qalqib chiqadi
va **5 soniyadan keyin o'zi o'chadi** (bosilsa darrov). Kassa ekranida joy
tor — katta xabar qatori butun joylashuvni pastga suradi va ish buziladi.
Kodi: `static/js/bildirishnoma.js`, uslubi `.xabarlar` / `.xabar`.

## Ish tartibi: naqd sotuv

Bosh sahifadagi **Sotuv** — qarzga yozilmaydigan savdo: tovarlar qo'shiladi,
pastdagi **Jami** ga kelishilgan summa yoziladi, yakunlangach tovarlar
ombordan ayriladi. Kunlik tushum **Sotuvlar** sahifasida ko'rinadi.

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
- `ombor/` — Mahsulot, ShtrixKod, OmborHarakati; `ombor/xizmat.py` — qoldiqni
  o'zgartiruvchi yagona joy (qarz ham, sotuv ham shuni chaqiradi);
  `ombor/kod.py` — kod/shtrix/tarozi kodi bo'yicha tovar topadigan yagona joy.
  Birlik o'tkazish: `Mahsulot.sotuvga_aylantir()` — boshqa hech qayerda ko'paytirilmaydi
- `templates/`, `static/css/uslub.css`, `static/js/` — interfeys
- `templates/ikonlar.html` — SVG ikonlar to'plami (`<use href="#i-...">`)
- `static/js/ombor.js` — ombor ekranlaridagi jonli hisob va kirim numpadi
- `static/js/skaner.js` — skanerni klaviaturadan ajratadi va `/ombor/kod/` ga so'raydi
- `static/js/sotuv_qarz.js`, `templates/sotuv/qarz_oyna.html` — chekning qarzga
  qoladigan qismi va yangi qarzdor oynachasi
- `versiya.py`, `versiya.txt`, `VERSIYALAR.md` — versiyalash
- `config/sinov.py` — testlar uchun asos (sayt login talab qilgani uchun
  har bir test kirib oladi)
- `qarz/management/commands/xodim.py` — xodim hisobi
- `qarz/templatetags/statik_versiya.py` — CSS/JS kesh yangilash (`{% statik '...' %}`)

## Keyin qilinadigan ishlar

- 13 ta hududning haqiqiy nomlarini qo'yish (`qarz/management/commands/boshlangich.py`)
- Foydalanuvchi (receptionist) hisobi va parol bilan kirish
- Chek chop etish, hisobotlar
- Etiketka chop etish (`Mahsulot.etiketka_kodi` tayyor — printer modeliga qarab
  TSPL yoki ZPL buyrug'i `win32print` orqali yuboriladi)
- Tarozining PLU ro'yxatini bazadan eksport qilish
