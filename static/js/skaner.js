/* Shtrix skaner — kassada ham, ombor ro'yxatida ham bir xil ishlaydi.

   USB skaner kompyuterga klaviatura bo'lib ulanadi: kodni juda tez yozadi va
   oxirida Enter bosadi. Odam bunchalik tez yozolmaydi — skaner shundan
   bilinadi. Shuning uchun na drayver, na port sozlamasi kerak: skanerni
   ulash kifoya (uning o'zida «Enter suffiksi» yoqilgan bo'lsin).

   Fokus qayerda turganining ahamiyati yo'q — belgilar hujjat darajasida
   ushlanadi. Skaner biror maydonga yozib yuborgan bo'lsa maydon avvalgi
   holatiga qaytariladi, ya'ni qidiruv maydoniga kod tushib qolmaydi.

   Kodni tovarga aylantirish bu yerda emas, serverda (`ombor/kod.py`) —
   qisqa kod, zavod shtrixi va tarozi etiketkasi qoidalari bitta joyda. */
(function () {
  "use strict";

  var TEZLIK = 40;      // ms: belgilar orasi shundan tez bo'lsa — skaner
  var ENG_QISQA = 4;    // skaner o'qigan kod shuncha belgidan qisqa bo'lmaydi
  var TUGASH = 3;       // Enter oxirgi belgidan TEZLIK*TUGASH ichida kelishi kerak

  /* Kodni serverga yuboradi va javobni sahifaga uzatadi. */
  function sorovchi(manzil, topilganda, topilmaganda) {
    return function (kod) {
      if (!kod) return;
      fetch(manzil + "?k=" + encodeURIComponent(kod), { credentials: "same-origin" })
        .then(function (javob) {
          if (!javob.ok) throw new Error(javob.status);
          return javob.json();
        })
        .then(function (javob) {
          if (javob.topildi) return topilganda(javob);
          if (topilmaganda) return topilmaganda(javob);
          window.xabarBer(javob.xato, "error");
        })
        .catch(function () {
          window.xabarBer("Tovarni izlab bo'lmadi. Sahifani yangilang.", "error");
        });
    };
  }

  /* Hujjat bo'ylab skanerni kutadi. */
  function skanerUlash(sora) {
    var bufer = "", oxirgi = 0, maydon = null, avvalgi = "";

    function maydonniTikla() {
      // Skaner yozgan belgilar maydonga tushib qolgan bo'lsa qaytarib olamiz.
      if (maydon && "value" in maydon && maydon.value !== avvalgi) {
        maydon.value = avvalgi;
      }
    }

    document.addEventListener("keydown", function (e) {
      if (e.ctrlKey || e.altKey || e.metaKey || e.isComposing) return;
      var hozir = Date.now();

      if (e.key === "Enter") {
        var kod = bufer, tez = hozir - oxirgi <= TEZLIK * TUGASH;
        if (kod.length < ENG_QISQA || !tez) {
          // Odam yozdi — sahifaning o'z Enter ishlovchisi bajarsin.
          bufer = "";
          return;
        }
        e.preventDefault();
        e.stopPropagation();
        maydonniTikla();
        bufer = "";
        maydon = null;
        sora(kod);
        return;
      }

      if (e.key.length !== 1) return;          // Shift, Tab, strelkalar va h.k.
      if (hozir - oxirgi > TEZLIK) {
        // Yangi kod boshlandi: fokus qayerda turganini eslab qolamiz.
        bufer = "";
        maydon = document.activeElement;
        avvalgi = maydon && "value" in maydon ? maydon.value : "";
      }
      oxirgi = hozir;
      bufer += e.key;
    }, true);                                   // capture: sahifadan oldin ushlaymiz
  }

  /* Sahifa shu funksiyani chaqiradi.
     sozlama: {manzil, topilganda(javob), topilmaganda(javob)}
     Qaytadigan `sora(kod)` ni sahifa o'zi ham chaqira oladi — kod maydoni
     uchun (skanersiz, qo'lda uriladigan yo'l). */
  window.Skaner = {
    ulash: function (sozlama) {
      var sora = sorovchi(sozlama.manzil, sozlama.topilganda, sozlama.topilmaganda);
      skanerUlash(sora);
      return sora;
    },
  };
})();
