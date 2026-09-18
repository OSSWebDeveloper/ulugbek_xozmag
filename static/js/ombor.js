/* Ombor ekranlari: ikki birlikli tovarlar uchun jonli hisob.
   Hech narsa yubormaydi — faqat foydalanuvchi nima bo'lishini oldindan ko'rsin.
   Haqiqiy hisob har doim serverda (ombor/models.py: sotuvga_aylantir). */
(function () {
  "use strict";

  function son(matn) {
    var q = parseFloat(String(matn || "").replace(",", "."));
    return isNaN(q) ? 0 : q;
  }

  function chiroyli(q) {
    return q.toLocaleString("ru-RU", { maximumFractionDigits: 3 }).replace(/ /g, " ");
  }

  // ---------- Tovar formasi: birliklarning jonli izohi ----------
  function mahsulotFormasi() {
    var forma = document.getElementById("mahsulot-forma");
    if (!forma) return;

    var birlik = document.getElementById("id_birlik");
    var olishBirligi = document.getElementById("id_olish_birligi");
    var olishMiqdori = document.getElementById("id_olish_miqdori");
    var narx = document.getElementById("id_narx");
    var qoldiq = document.getElementById("id_qoldiq");
    var miqdorMaydon = document.getElementById("olish-miqdori-maydon");
    var qoida = document.getElementById("birlik-qoida");
    if (!birlik || !olishBirligi || !olishMiqdori) return;

    function yangila() {
      var sotuv = birlik.value;
      var olish = olishBirligi.value;
      var ikki = olish && olish !== sotuv;

      document.getElementById("narx-birlik").textContent = sotuv;
      document.getElementById("qoldiq-birlik").textContent = sotuv;
      document.getElementById("olish-birlik-nomi").textContent = olish || "olish birligi";
      document.getElementById("sotuv-birlik-nomi").textContent = sotuv;

      miqdorMaydon.hidden = !ikki;
      if (!ikki) {
        qoida.hidden = true;
        return;
      }

      var nechta = son(olishMiqdori.value);
      if (nechta <= 0) {
        qoida.hidden = false;
        qoida.className = "qoida-satri ogoh";
        qoida.textContent = "1 " + olish + " da nechta " + sotuv + " borligini yozing.";
        return;
      }

      var qatorlar = ["1 " + olish + " = " + chiroyli(nechta) + " " + sotuv];
      if (son(narx.value) > 0) {
        qatorlar.push("1 " + olish + " narxi ≈ " + chiroyli(son(narx.value) * nechta) + " so'm");
      }
      if (son(qoldiq.value) > 0) {
        qatorlar.push("Qoldiq: " + chiroyli(son(qoldiq.value)) + " " + sotuv +
                      " = " + chiroyli(son(qoldiq.value) / nechta) + " " + olish);
      }
      qoida.hidden = false;
      qoida.className = "qoida-satri";
      qoida.textContent = qatorlar.join("  ·  ");
    }

    [birlik, olishBirligi, olishMiqdori, narx, qoldiq].forEach(function (el) {
      el.addEventListener("change", yangila);
      el.addEventListener("input", yangila);
    });
    yangila();
  }

  // ---------- Kirim ekrani: "2 rulon = 200 metr qo'shiladi" ----------
  function kirimFormasi() {
    var forma = document.getElementById("kirim-forma");
    if (!forma) return;

    var miqdor = document.getElementById("kirim-miqdor");
    var natija = document.getElementById("kirim-natija");
    if (!miqdor || !natija) return;

    var sotuv = forma.dataset.birlik;
    var olish = forma.dataset.olishBirligi;
    var nechta = son(forma.dataset.olishMiqdori) || 1;
    var hozirgi = son(forma.dataset.qoldiq);
    var ikki = !!olish && olish !== sotuv;

    function tanlanganBirlik() {
      var belgi = forma.querySelector('input[name="birlik"]:checked');
      return belgi ? belgi.value : sotuv;
    }

    // Tanlangan tugmani belgilaydi (eski brauzerda CSS :has ishlamasligi mumkin).
    function tugmalarniBelgila() {
      forma.querySelectorAll(".birlik-tugma").forEach(function (el) {
        var kirish = el.querySelector("input");
        el.classList.toggle("tanlangan", !!kirish && kirish.checked);
      });
    }

    function yangila() {
      var kiritilgan = son(miqdor.value);
      if (kiritilgan <= 0) {
        natija.hidden = true;
        return;
      }
      var birlik = tanlanganBirlik();
      var qoshiladi = (ikki && birlik === olish) ? kiritilgan * nechta : kiritilgan;
      var yangi = hozirgi + qoshiladi;

      var matn = "";
      if (birlik !== sotuv) {
        matn += chiroyli(kiritilgan) + " " + birlik + " = " +
                chiroyli(qoshiladi) + " " + sotuv + " qo'shiladi";
      } else {
        matn += chiroyli(qoshiladi) + " " + sotuv + " qo'shiladi";
      }
      matn += "  ·  yangi qoldiq: " + chiroyli(yangi) + " " + sotuv;
      if (ikki) matn += " (" + chiroyli(yangi / nechta) + " " + olish + ")";

      natija.hidden = false;
      natija.textContent = matn;
    }

    miqdor.addEventListener("input", yangila);
    forma.querySelectorAll('input[name="birlik"]').forEach(function (el) {
      el.addEventListener("change", function () {
        tugmalarniBelgila();
        yangila();
        miqdor.focus();
      });
    });
    tugmalarniBelgila();
    yangila();
  }

  document.addEventListener("DOMContentLoaded", function () {
    mahsulotFormasi();
    kirimFormasi();
  });
})();
