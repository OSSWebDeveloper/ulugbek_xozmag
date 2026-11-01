# Rongta RLS1100C

Manzil: 192.168.1.110. Ethernet orqali server kompyuteriga ulangan.
Ombordan faqat `birlik=kg`, faol va musbat so'm narxli mahsulotlar olinadi.
Kelish birligi `pachka` bo'lishi mumkin; sotish birligi `kg` bo'lishi shart.
Qoldiq nol bo'lsa ham mahsulot taroziga yuboriladi. Qoldiq taroziga yuklanmaydi.

Kod = LFCode va Code. Sotish narxi *100 (tarozi 2 kasr xonasida), WeightUnit=4.
Barcode type 27 va department 2: 2 + PLU(6) + gramm(5) + EAN nazorat raqami.
Bu `ombor/kod.py` formatiga mos. Nom ASCII 32 belgigacha qisqartiriladi;
uzun nomning oxiridagi variant belgisi saqlanadi. Asl nom omborda o'zgarmaydi.
Narxsiz, lotin shriftiga mos kelmaydigan yoki 999999.99 dan katta narxlar o'tkaziladi.

Qurilmalar sahifasida aloqa sinovi, katalog yuborish va etiketkani tekshirish bor.
Sinovning 'aloqa bor' natijasi faqat SDK protokoli javobini anglatadi.
Etiketkaning bosilishi va skanerlash jismoniy tekshiruvni talab qiladi.
RLS1100C etiketka tarozisi sifatida ishlaydi; vazn kassaga etiketka ichidan keladi.

Har bir yuborishdan oldin to'liq PLU nusxasi `qurilmalar_data/*_backup.json` ga olinadi.
Yangi kg katalogiga kirmagan eski yozuvlar SDK `isDelete=1` bilan yashiriladi.
Kalibrlash, firmware, shrift, etiketka va boshqa parametrlar almashtirilmaydi.
Yuborish tugagach narx, nom, birlik, shtrix turi, kodlar va faol yozuvlar to'plami
tarozidan qayta o'qib solishtiriladi. Natija va o'tkazilganlar shu papkada saqlanadi.
Xatoda qisman yuborilgan bo'lishi mumkin; sababni tuzatib, qayta yuboring.
Jarayon uzilib qolib lock fayli qolgan bo'lsa, oldin boshqa yuklash ishlamayotganini
tekshirib, keyin `qurilmalar_data/rongta_sync.lock` ni olib tashlang.

Drayverning x86 DLL fayllari `qurilma_drivers/rongta` ichida mahalliy saqlanadi.
32 bit Windows PowerShell yordamchi jarayoni ishlatiladi. U faqat nomlangan
ulanish/PLU o'qish va yuborish funksiyalarini chaqiradi. DLL'larni system32 ga
ko'chirish va registratsiya qilish talab qilinmaydi. Drayver va mahalliy hisobotlar
git'ga kiritilmaydi. Ularni tarqatish huquqi Rongta ishlab chiqaruvchisiga tegishli.

Mahalliy SDK manbasi: Rongta RLS_setup_V2.0.19.37, DataBird One ishlab chiqaruvchi
utilitasi sifatida taqdim etgan nusxa:
https://databird.one/rls1s/files/RLS_setup_V2.0.19.37.exe
Qo'llanmalar:
https://databird.one/rls1s/files/RLS-Series-software-user-manual-RT-V2.0.pdf
https://file.globalso.com/file_manage/4365/20251121/label-scale-software-user-manual.pdf

Jismoniy sinov: PLU 98, shefir shurub, 32000 so'm/kg. Masalan 0.500 kg uchun
16000 so'm bo'lishi kerak. Etiketkani Qurilmalar sahifasida skanerlab tekshiring.
