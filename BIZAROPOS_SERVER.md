# BizaroPOS asosiy kassa

`BIZAROPOS_ORNATISH.ps1` (administrator PowerShell) Python kutubxonalarini,
desktop yarligini va mahalliy tarmoq uchun 5555-port qoidasini o‘rnatadi.
Ish stolidagi BizaroPOS yorlig‘i ikki marta bosilganda Windows UAC orqali
Administrator ruxsatini so‘raydi. Faqat ruxsat berilganda server ishga tushadi;
rad etilganda ishga tushmaydi. Pythonw oynasiz ishlaydi, brauzer ochiladi.
Takror bosish yangi server ochmaydi. Eski SERVERXOZMAG.bat va kuzatuvchi bilan birga ishlatmang.

Asosiy kompyuter: http://127.0.0.55:5555/.
Boshqa kassalar va telefonlar: http://<server IP>:5555/ — manzil Kassalar
sahifasida va server ishga tushgandagi bildirishnomada yoziladi.
Ikkala kassa bir xil routerga (Wi-Fi yoki kabel) ulangan bo'lishi kerak.
127.x manzillar har qurilmaning o‘zini anglatadi.
Guest Wi-Fi / client isolation boshqa qurilmalar ulanishini to‘sishi mumkin.

## Doimiy manzil: DHCP reservation

Server manzili o'zgarmasligi uchun u **routerda band qilinadi**. Dastur
Windows'ning IP sozlamalariga tegmaydi: kassalarga qo'lda qo'shimcha IP
(eski 192.168.153.x) endi yozilmaydi, 2-kassa manzilni routerdan o'zi oladi.

1. Server kompyuterida Windows IP ni avtomatik (DHCP) oladigan bo'lsin.
2. BizaroPOS → Kassalar sahifasini oching. U yerda server kompyuterining
   MAC manzili, hozirgi IP si va router sozlamalari havolasi turadi.
3. Routerga kiring (TP-Link XX530v: http://192.168.1.1, parol router
   ostidagi yorliqda) → Advanced → Network → LAN Settings (yoki DHCP Server)
   → Address Reservation → Add. MAC va IP ni yozing, saqlang.
4. Kassalar sahifasida shu IP ni yozib «Saqlash» ni bosing. Sahifa yashil
   «Tayyor» ni ko'rsatishi kerak.
5. Shundan keyin 2-kassa dasturini yuklab oling: paket yuklangan paytdagi
   server manzilini eslab qoladi. Manzil keyin o'zgargan bo'lsa paketni
   qayta yuklab, ORNATISH.bat ni qayta bajaring.

Sahifadagi ogohlantirishlar:
- «Router … berdi, band qilingan manzil esa …» — band qilish routerda
  saqlanmagan yoki kompyuter tarmoqqa qayta ulanmagan (Wi-Fi ni uzib-ulang).
- «IP qo'lda yozilgan» — Windows'da statik IP turibdi; avtomatikka o'tkazing.

Eslatmalar:
- Reservation MAC manzilga bog'lanadi. Server Wi-Fi o'rniga kabel bilan
  ulansa MAC boshqa bo'ladi — o'sha karta uchun alohida yozuv kerak.
- Windows'dagi «Случайные аппаратные адреса» (tasodifiy MAC) o'chiq bo'lsin.
- Router almashtirilsa yoki zavod holatiga qaytarilsa band qilish qaytadan
  qo'yiladi.
- Rongta tarozisi qo'lda yozilgan 192.168.1.110 manzilida. U ham shu
  routerga ulansa, bu manzilni boshqa qurilmaga band qilmang.

Tray belgisi ustiga chap yoki o‘ng bosilganda: serverni o‘chirish, qayta
yuklash, GitHub’dan yangilash, versiya. O‘chirish kompyuterni o‘chirmaydi.
Server Waitress orqali barcha IPv4 interfeyslarda ishlaydi, DEBUG o‘chiq,
kirish paroli talab qilinadi. Firewall faqat mahalliy subnetga ruxsat beradi.

GitHub origin/main ishga tushishda va har soatda tekshiriladi. Internet yo‘q
bo‘lsa savdo ishlayveradi. Yangilash faqat menyudagi buyruq bilan amalga oshadi.
Yangi versiya bo‘lsa menyuda yozuv chiqadi. Yangilash faqat oldinga siljiydi;
mahalliy kod o‘zgarishlari yoki bazaga tegadigan GitHub o‘zgarishlari bo‘lsa
to‘xtaydi. db.sqlite3 Git’da kuzatiladi, lekin uning mahalliy o‘zgarishi kodni
tekshirishda hisoblanmaydi va GitHub bazasi uning ustiga yozilmaydi.

Yangilash oldidan server yangi so‘rovlarni qabul qilishni to‘xtatadi, joriy
so‘rovlarga 30 soniya beradi, bazani SQLite backup API orqali va kodni ZIP
ko‘rinishida qurilmalar_data/server/zaxira ichiga saqlaydi. Yangilashda baza
migratsiyalari bajariladi. Xatoda zaxira saqlanadi; avtomatik baza rollback
qilinmaydi. Yangi kutubxona talab etilgan relizda o‘rnatuvchini qayta bajaring.
Savdo tugmalarini bosayotgan paytda qayta yuklash/yangilashni boshlamang.

Jurnallar: qurilmalar_data/server/server.log va boshqaruv.log.
Rongta, printer, eski etiketka o‘lchamlari va mavjud ombor shu kompyuterda qoladi.

## Ikki kassa

Har kassir alohida akkaunt bilan kiradi; ochiq savatlar bir-biriga aralashmaydi.
Ombor va tarozi etiketkalari umumiy. Skanerlash, miqdorni ko‘paytirish,
qatorni o‘chirish va ochiq savdoni bekor qilish qoldiqqa tegmaydi. Yakunlash
qoldiqni qayta tekshiradi va barcha qatorlarni bir tranzaksiyada ayiradi.
Bir mahsulot yetmasa butun savdo ochiq qoladi va chek chiqarilmaydi.

Asosiy kassada eski USB printer avvalgidek ishlaydi. Ikkinchi kassada
Qurilmalar > USB kassa yordamchisini yuklab olish orqali shaxsiy paket olinadi.
Paketni shu kassada ochib ORNATISH.bat bajariladi. Python paket ichida;
Windows’da mahalliy chek printerini default qiling. Yordamchini har ish kuni
BizaroPOS Kassa yarligidan oching. Ikkinchi kassa alohida server ochmaydi.

USB yordamchi faqat o‘z akkauntining navbatini maxsus kalit orqali oladi.
Server lokal printerini masofadagi kassa uchun ishlatmaydi. Chekda yuborildi
holati Windows spooleriga topshirishni anglatadi; qog‘oz chiqqanini isbotlamaydi.
Tarmoq uzilganda noma’lum chop avtomatik takrorlanmaydi. Qog‘ozni tekshirib,
Chek sahifasidagi tasdiq bilan qo‘lda qayta chiqarish mumkin. Yordamchini
qayta yuklab olish oldingi paket kalitini bekor qiladi.
