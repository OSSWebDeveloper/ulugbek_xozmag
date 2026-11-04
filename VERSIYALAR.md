# Versiyalar tarixi

## 3.9.19 — 2026-11-04

- BIZAROPOS_ORNATISH.ps1 ichidagi PowerShell 5.1 da parser xatosiga sabab bo'lgan tipografik apostrof olib tashlandi.
- Installerning UAC yo'li va desktop yorlig'i saqlandi; kod faqat moslik uchun tuzatildi.

## 3.9.18 — 2026-11-04

- BizaroPOS ish stoli yorlig'i ishga tushirilganda Windows standart UAC administrator ruxsatini avtomatik so'raydi (ShellExecute runas).
- UAC rad etilsa server ochilmaydi; rozilik berilganda oldingi tray va brauzer rejimi saqlanadi.
- Elevated Pythonw jarayonida yangilash funksiyasi Git yo'lini to'g'ri ishlatishi uchun launcher --git-path argumentini uzatadi.
- Yangilangan yorliqni olish uchun BIZAROPOS_ORNATISH.ps1 qayta bajariladi; mavjud eski yorliqlar avtomatik o'zgarmaydi.

## 3.9.17 — 2026-11-04

- LAN portining firewall qoidasi Wi-Fi Public profilida ham ishlashi uchun Profile Any qilib yangilandi, RemoteAddress esa LocalSubnet4 bilan cheklangan.
- Administrator huquqi dastur o'rnatuvchisining boshida tekshiriladi; shuning uchun o'rnatish yarmida firewall qoidasiga yetib kelib to'xtamaydi.
- Telefonning ERR_ADDRESS_UNREACHABLE xatosi subnetlar yoki Wi-Fi client isolation tufayli bo'lsa, router va telefon tarmog'ini alohida tekshirish talab etiladi; dastur kodi buni o'zi hal qila olmaydi.

## 3.9.16 — 2026-11-04

- Wi-Fi/LAN orqali kirishda mavjud tarmoq IP manzili ko‘rsatiladi; eskirgan 192.168.153.25 manziliga ko‘r-ko‘rona tayanilmaydi.
- Kassalar sahifasidagi Saqlash tugmasi faqat sozlamalarni faylga yozadi; PowerShell orqali IP qo‘shmaydi va server jarayonini ishga tushirmaydi.
- Installer firewall qoidasi 5555-portni Private LAN va LocalSubnet uchun ochadi; pythonw.exe va python.exe farqidan keladigan bloklanish bartaraf etiladi.
- IP saqlash va haqiqiy LAN manzilni ko‘rsatish uchun regressiya testlari qo‘shildi.
- Bosh versiya foydalanuvchi belgilagan 3.9.15 asosidan 3.9.16 ga ko‘tarildi. Avvalgi git versiyasi 3.9.9 edi.

### Hisoblar va login/parolni o'zgartirish — 2026-11-03
- Yangi o'rnatishda server/server va kassa/kassa boshlang'ich akkauntlari.
- Birinchi kirishda parolni majburiy almashtirish va keyinchalik login/parolni sozlash.
- O'rnatuvchi yoki qayta ishga tushirish mavjud akkaunt parollarini qayta yozmaydi.

## 3.9.9 — 2026-11-03

- Server kassasiga «Hisobot» bo'limi: kassir va sana bo'yicha yakunlangan sotuvlar, qaytarilgan summa ayrilgan tushum.
- Omborga mahsulot qo'shish va tahrirlashda do'kon sotib olish narxi hamda xarid valyutasi.
- Dasturdan foydalanish qo'llanmasi va tegishli testlar.

## 3.9.8 — 2026-11-01

- Ikki kassa uchun umumiy ombor, alohida savatlar va USB chek printeri yordamchisi.
- BizaroPOS lokal serveri, tray menyusi va GitHub orqali yangilanishni tekshirish.
- Rongta RLS1100C bilan Ethernet aloqasi va kg mahsulotlarini taroziga yuborish.
- Kelish narxlari, birliklar konvertatsiyasi, qoldiqni tuzatish va 4 xonali mahsulot kodlari.
- Miqdorni ko‘paytirish oynasi, avtomatik jami va savdo yakunida ombordan ayirish.
- Shtrix kodli xarid cheki, chekni qayta chiqarish va chek orqali qaytarish.
- Printer tanlanadigan mahsulot yorliqlari va 56×40 mm o‘lcham.

Tekshiruv: 334 ta test o‘tdi; yangi migratsiyalar model holatiga mos.

## 3.0.0 — 2026-10-01

Ombor: Excel orqali yangilash va bekor qilish, 5 xonali joy kodi, kam qolganlar birinchi

## 2.8.0 — 2026-09-23

Sotuv qayta ishlandi: autosplit va qidiruvda tovar kodi

- Pul maydonlarida raqamlar o'zi guruhlanadi (200000 -> 200 000).
- «Jami» — chekning to'liq summasi; «Qarzga» oynachasi uni to'langan va
  qarz qismga o'zi bo'ladi, biri yozilsa ikkinchisi hisoblanadi.
- Tovar tanlash oynasining qidiruv ro'yxatida tovar kodi.
- «Bekor qilish» endi tasdiq so'raydi; yopilgan chekka tegilmaydi va u ikki
  marta yakunlanmaydi; qaytarilgan pul avval qarzdan ayriladi.

## 2.7.0 — 2026-09-22

Oldindan to'lov, naqd sotuvda qisman qarz oynachasi, ko'rinish tozalandi

## 2.6.0 — 2026-09-22

Tovar kodi (0000000001), oxirgi 4 raqam bilan topish, shtrix skaner va tarozi etiketkasi

## 2.5.0 — 2026-09-22

Dollar kursi Markaziy bankdan olinadi

- Kassadagi «Kurs» maydonining standart qiymati cbu.uz dan keladi, butun
  so'mga yaxlitlanadi; kassir ustidan yozib qo'ya oladi.
- Kuniga bir marta so'raladi va bazaga yoziladi — internet yo'q bo'lsa
  oldingi kun kursi yoki oxirgi qo'lda yozilgani ishlatiladi, xatolik
  chiqmaydi.
- Qiymat qayerdan kelgani maydon ustiga borilganda ko'rinadi.

## 2.4.1 — 2026-09-22

Tovar formasi tartibga solindi

- Maydonlar juft bo'lib tekis turadi: valyuta bilan narx, birlik bilan qoldiq.
- Izohlar qisqardi, uzuni endi maydon ustiga olib borilganda chiqadi.
- Pastki qator ingichka chiziq bilan ajraldi: belgilash chapda, tugmalar o'ngda.
- Tahrirlashda ortiqcha nollar ko'rinmaydi: «45.00» emas, «45».

## 2.4.0 — 2026-09-22

Tovar kartochkasiga narx qaytdi

- Narx 1 sotuv birligi uchun, tovarning valyutasida — ombor ro'yxatida va
  kassadagi tovar kartasida ko'rinadi (keyinchalik elektron tarozi uchun).
- Hisob-kitobga aralashmaydi: chek va qarz summasi baribir qo'lda yoziladi.
- Ikki birlikli tovarda jonli izoh qadoq narxini ham aytadi.

## 2.3.0 — 2026-09-22

Qaytarib berish (vozvrat) va cheklar bazada saqlanishi

- Har bir tovar qatoridan **qaytarish**: qisman ham bo'ladi — 20 qopdan 5 tasi.
  Tovar omborga qaytadi, qaytarilgan pul hujjat summasidan ayriladi, qarzda
  qarzdorning balansi kamayadi.
- Ombor tarixida qaytarish alohida tur bo'lib ko'rinadi.
- Bekor qilingan chek endi o'chirilmaydi — bazada qoladi, ro'yxatda nishoni
  bilan xira turadi va kunlik tushumga qo'shilmaydi.

## 2.2.0 — 2026-09-22

So'm va dollar alohida hisoblanadi, summa qo'lda yoziladi

- Narx qatorlarda yozilmaydi: kassada tovar va miqdor tanlanadi, chek/qarz
  summasi yakunlashda qo'lda kiritiladi — do'konda savdolashiladi.
- Ikkita alohida «Jami»: so'm va dollar hech qayerda qo'shilmaydi. Tovar
  qo'shishda qaysi pulda kelgani so'raladi, dollarlik tovar «$» bilan turadi.
- Dollar kursi kassada yoziladi (oldingi hujjatdagisi tayyor turadi).
- Qarzdorning ikkita balansi va valyutasi bilan yoziladigan to'lov.
- «Qaytim» olib tashlandi.
- Xabarlar o'ng yuqorida, 5 soniyadan keyin o'zi o'chadi — sahifani surmaydi.

## 2.1.0 — 2026-09-19

Tovarda narx saqlanmaydi — narx sotuv va qarz vaqtida yoziladi

## 2.0.1 — 2026-09-19

Bosh sahifaga zarrachali ko'k fon qo'yildi

## 2.0.0 — 2026-09-18

Saytga kirish login va parol bilan

## 1.9.5 — 2026-09-18

Hududlar ekranida tepadagi bo'shliq kattaroq

## 1.9.4 — 2026-09-18

Hududlar ekraniga tepadan bo'shliq

## 1.9.3 — 2026-09-18

Hududlar ekranidan sarlavha olib tashlandi

## 1.9.2 — 2026-09-18

Qidiruv maydoni olib tashlandi

## 1.9.1 — 2026-09-18

Tanlov ekranlarida tugmalar o'rtada

## 1.9.0 — 2026-09-18

Kirim ichki oynada, qarzdorlar hudud bo'yicha, buxta -> o'ram

## 1.8.0 — 2026-09-18

Qalqib chiquvchi numpad yo'q, klaviatura faqat harf

## 1.7.1 — 2026-09-18

Umumiy o'lcham 90%

## 1.7.0 — 2026-09-18

Butun sayt 80% o'lchamda — brauzer ro'yxatlari ham sig'adi

## 1.6.0 — 2026-09-18

Qoldiq butun qadoq va ortig'i bilan: «5 pachka 20 dona»

## 1.5.1 — 2026-09-18

Tovar nomlarida santimetr o'rniga metr

## 1.5.0 — 2026-09-18

To'liq ko'rik: to'lov chegarasi, scrollsiz joylashuv, o'nlab tuzatish

## 1.4.0 — 2026-09-18

Yangi tovar formasiga «Birlik o'zgaradi» richagi

## 1.3.0 — 2026-09-18

Ikkala mavzu ham my.gov.uz palitrasida

## 1.2.0 — 2026-09-18

Kechki mavzu to'liq my.gov.uz palitrasida (ko'k urg'u)

## 1.1.0 — 2026-09-18

Kechki mavzu my.gov.uz palitrasiga o'tkazildi (neytral kulrang fonlar)

## 1.0.1 — 2026-09-18

Nom to'g'irlandi: Xozmag (xo'jalik magazini)

## 1.0.0 — 2026-09-18

Birinchi ishchi versiya: qarz daftari, naqd sotuv, ombor organiseri.

- Qarz daftari: qarzdorlar, hududlar, kassa ko'rinishidagi qarz yozish ekrani,
  to'lov qabul qilish, qarzdor kartasi.
- Naqd sotuv: qarzga yozilmaydigan savdo, «mijoz berdi» va qaytim hisobi,
  kunlik tushum.
- Ombor: tovarlar, qoldiq, kirim/chiqim tarixi; qoldiq bitta joydan o'zgaradi
  (`ombor/xizmat.py`).
- Bir birlikda olinib boshqasida sotiladigan tovarlar: polietilen lenta rulonda
  olinib metrda sotiladi. Qoldiq har doim sotuv birligida, o'tkazish faqat kirim
  paytida.
- Sensorli rejim: o'zimizning ekran klaviaturasi va raqamlar klaviaturasi.
- Kechki va kunduzgi ko'rinish.
