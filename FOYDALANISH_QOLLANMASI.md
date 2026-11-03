# Ulug'bek Xozmag — foydalanish qo'llanmasi

## 1. Dastur vazifasi
Ulug'bek Xozmag — Django asosidagi do'kon POS tizimi. Ombor mahsulotlari, sotuvlar, cheklar, qarzdorlar, kassalar, qurilmalar va tarozi bilan ishlaydi. Ushbu qo'llanma server va kassa operatorlariga mo'ljallangan.

## 2. Ishga tushirish va tizimga kirish
- Server kompyuterida o'rnatilgan dasturini ishga tushiring (loyihada `SERVERXOZMAG.bat` mavjud).
- Brauzerda server manzilini oching; lokal ishlab chiqishda: `http://127.0.0.1:8000/`.
- `Kirish` sahifasida foydalanuvchi login/parolini kiriting. Har bir kassirga alohida foydalanuvchi berish hisobotda kassalarni ajratish uchun muhim.
- Qo'shimcha kassalar server bilan bir tarmoqda bo'lishi kerak. Serverdagi `Kassalar` bo'limida tarmoq parametrlarini tekshiring. Serverning IP manzilini o'zgartirishda tarmoq sozlamalari va administrator huquqlariga e'tibor bering.
- Dasturdan chiqishda yon menyudagi `Chiqish` tugmasidan foydalaning.

## 3. Omborga yangi tovar qo'shish
1. `Ombor` → `Yangi tovar` sahifasiga o'ting.
2. `Kod` (0001–9999) kiriting yoki avtomatik berilishi uchun bo'sh qoldiring.
3. `Shtrix kod` (ixtiyoriy, 8/12/13/14 xonali), `Nomi`, `Sotuv birligi` va `Valyuta`ni tanlang.
4. `Narxi` — mijozga sotishning ma'lumot narxi; `Do'kon sotib olish narxi` — mahsulotni yetkazib beruvchidan olishning **bitta sotuv birligiga to'g'ri keladigan** narxi. Xarid narxi valyutasini alohida tanlang. Ikkala narxni aralashtirmang. Xarid narxini bo'sh qoldirish mumkin.
5. Oddiy mahsulot uchun `Qoldiq`ni kiriting.
6. Masalan, 1 rulon = 100 metr bo'lsa `Birlik o'zgaradi`ni yoqing: kelgan birligi — rulon, sotuv birligi — metr, `Bittasida` — 100, `Necha qadoq keldi` — masalan, 3. Omborda 300 metr saqlanadi.
7. `Saqlash`ni bosing. So'ng etiketka sahifasida shtrix-kodlarni chop etish mumkin.

**Eslatma:** Valyutalar alohida yuritiladi. Dollarni so'mga avtomatik qo'shib yubormang. Xarid narxi kiritilgan bo'lsa ham, hisobotdagi tushum sotuvning amalda kassaga kelgan summasi asosida hisoblanadi; u foyda hisoboti emas.

## 4. Mavjud tovarga kirim qilish
1. `Ombor` ro'yxatidan tovarni toping (nom, ichki kod yoki shtrix orqali).
2. `Kirim`ni ochib, yangi kelgan miqdorni kiriting.
3. Ikki birlikli tovar bo'lsa kirim birligini (rulon/metr kabi) tanlang.
4. Kerak bo'lsa `Izoh` yozing; `Omborga qo'shish` yoki `Qo'shish va etiketka`ni bosing.
5. Yangi xarid partiyasining narxi o'zgargan bo'lsa tovar kartochkasini `Tahrirlash` orqali `Do'kon sotib olish narxi`ni yangilang. Hozirgi modelda mahsulotning bitta xarid narxi saqlanadi, alohida partiyalar tannarxi tarixi yuritilmaydi.

## 5. Sotuv qilish va chek chiqarish
1. `Sotuv`ga o'ting; tugallanmagan chek bo'lsa ochiladi, bo'lmasa yangisi yaratiladi.
2. Kod/skaner yoki mahsulot tanlash oynasi orqali tovar qo'shing.
3. Miqdorni, kerak bo'lsa sotish narxini tekshiring. Tizim qatorlar bo'yicha jami hisoblaydi; kelishilgan yakuniy summa ham kiritilishi mumkin.
4. To'lov so'm va dollarda alohida saqlanadi. Qisman to'lovda qolgan summa qarz hujjatiga yozilishi mumkin.
5. Savdoni yakunlang: ombor qoldig'i kamayadi, chek saqlanadi. Printer ishlamasa, `Sotuv` ro'yxatidan chekni qayta chop etish imkoniyati mavjud.
6. Qaytarish kerak bo'lsa tegishli chekning `Qaytarish` amaliyotidan foydalaning; miqdor omborga qaytadi va qaytarilgan pul tushumdan ayriladi.

## 6. Serverda «Hisobot» bo'limi
**Faqat server kompyuterida ochiladi.** Yon menyudagi `Hisobot`ni tanlang (yoki `/sotuv/hisobot/` manzilini oching).
- Sana oralig'i: `Boshlanish sanasi` va `Tugash sanasi`.
- `Kassir`: bitta kassir yoki `Barcha kassalar`.
- Natija: yakunlangan va bekor qilinmagan cheklar soni, qaytarishdan keyingi naqd so'm, naqd dollar, kassirlar bo'yicha jamlanma va so'nggi 500 ta chek.
- `Chek` raqamini bosib uning tafsilotlarini ko'rish mumkin.
- Hisobotga ombor kirimlari, bekor qilingan yoki tugallanmagan cheklar, qarzning keyinchalik qaytarilishi kiritilmaydi.
- Qisman qarzga sotilgan chekda faqat ayni savdoda kassaga tushgan summa kassa tushumiga qo'shiladi.
- Hisobot **tushum hisoboti**; u xarid narxi yoki sof foyda hisoboti emas.

## 7. Qarzdorlar
`Qarzdor` bo'limida qarzdor mijozlar va qarz hujjatlarini ko'rish, kerakli qarz bo'yicha amallarni bajarish mumkin. Qarzning keyinchalik to'lanishi yangi kassa savdosi sifatida qayta hisoblanmaydi.

## 8. Excel orqali omborni yangilash
`Ombor` bo'limidagi Excel eksport/import orqali ko'p tovarlarni boshqarish mumkin. Fayl yuklanganda o'zgarishlar qoralama bo'ladi: avval tekshiring, keyin `Qo'llash`ni bajaring. Qoralama xatolarini tekshirmay qo'llamang. Excel importining ustunlari qo'lda kiritish formasidan mustaqil ishlaydi: xarid narxi maydonini Excel importida yuritish alohida sozlanadi.

## 9. Qurilmalar va printer
`Qurilmalar` sahifasi printer va tarozi ulanishlarini boshqaradi. Etiketka/printer sozlamalarini sinov bosmasi bilan tekshiring. USB chek chiqarish hamda tarozi agenti server yoki mahalliy kassa konfiguratsiyasiga bog'liq; ulanish ishlamasa, kabel, IP, printer nomi va yordamchi agentni tekshiring.

## 10. Ma'lumot xavfsizligi va zaxira
- Har bir kassir uchun alohida login ishlating.
- `db.sqlite3` ma'lumotlar bazasi zaxirasini dasturga hech kim yozmayotgan paytda xavfsiz usulda oling. Zaxirani ommaviy GitHub'ga yuklamang.
- Yangilashdan oldin bazani zaxiralang; yangi branch o'zgarishlarini sinov muhitida tekshiring.
- Dastur ochiq tarmoqqa chiqarilsa HTTPS, aniq `ALLOWED_HOSTS`, autentifikatsiya va foydalanuvchi huquqlarini tekshirish zarur.

## 11. Texnik ishga tushirish (dasturchi uchun)
Virtual muhit va loyiha kutubxonalarini o'rnating. So'ng:
```bash
python manage.py check
python manage.py migrate
python manage.py test sotuv ombor
python manage.py runserver
```
`Hisobot` bo'limi faqat server kompyuterining mahalliy IP manzilidan ishlashi uchun cheklangan. Yangilanishlar dastlab alohida branch'ga kiritiladi; sinovdan keyin main'ga qo'shing.
