# BizaroPOS asosiy kassa

`BIZAROPOS_ORNATISH.ps1` (administrator PowerShell) Python kutubxonalarini,
desktop yarligini va mahalliy tarmoq uchun 5555-port qoidasini o‘rnatadi.
Ish stolidagi BizaroPOS yorlig‘i ikki marta bosilganda Windows UAC orqali
Administrator ruxsatini so‘raydi. Faqat ruxsat berilganda server ishga tushadi;
rad etilganda ishga tushmaydi. Pythonw oynasiz ishlaydi, brauzer ochiladi.
Takror bosish yangi server ochmaydi. Eski SERVERXOZMAG.bat va kuzatuvchi bilan birga ishlatmang.

Asosiy kompyuter: http://127.0.0.55:5555/.
Boshqa Windows kassalari: http://WIN-HS2MGB9MV4U:5555/ (server kompyuter nomi).
Yangi USB yordamchi paketlari ham server nomiga ulanadi; eski IP yozilgan
paketni qayta yuklab o'rnatish kerak. Kompyuter nomi o'zgartirilmasin.
Ikkala kassa bir xil Wi-Fi yoki bir xil hotspotda bo'lishi kerak.
Tarmoq Windows kompyuter nomlarini aniqlashi va mijozlararo aloqani o'tkazishi
kerak. Mijozlarni ajratadigan hotspotda nom orqali ham ulanish bo'lmaydi.
127.x manzillar har qurilmaning o‘zini anglatadi. Wi-Fi manzili routerdan
o‘zgarishi mumkin; barqaror manzil uchun routerda DHCP reservation qo‘ying.
Guest Wi-Fi / client isolation boshqa qurilmalar ulanishini to‘sishi mumkin.

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

## Yordamchisiz kassa: brauzer orqali chop etish

Boshqa kompyuterga hech narsa o‘rnatish shart emas. Brauzerda serverning
manzilini (http://<server IP>:5555/) ochib, o‘z akkaunti bilan kirgan har
qanday kompyuter o‘ziga ulangan printerda chop etadi:

- savdo yakunlanganda chek shu brauzerning chop oynasiga chiqadi;
- Sotuvlar > «Chekni qayta chiqarish» va Qurilmalar > «Sinov cheki» ham shunday;
- yorliq: Ombor > Etiketka > Chop etish > «Brauzerdan chop etish».

Chek Windows’dagi standart (default) printerga chiqadi, shuning uchun har
kompyuterda chek printerini standart qiling. Chop oynasida bir marta:
qog‘oz o‘lchami 80 mm, hoshiyalar «Yo‘q», kolontitullar o‘chiq.

Chop oynasi har safar chiqmasligi uchun brauzerni shu bayroq bilan oching
(ish stolida yorliq yarating; Edge o‘rniga chrome.exe ham bo‘ladi):

    msedge.exe --kiosk-printing http://<server IP>:5555/

Shunda chek tasdiqsiz, to‘g‘ridan-to‘g‘ri standart printerga ketadi.
Server kompyuterining o‘zi avvalgidek USB printerga bevosita chiqaradi.
Yordamchi (keyingi bo‘lim) o‘rnatilgan va ishlab turgan kassada chek
yordamchi orqali chiqadi; yordamchi yopiq bo‘lsa — brauzer orqali.

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
