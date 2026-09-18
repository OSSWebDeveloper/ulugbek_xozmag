/* Ombor ekranlari: ikki birlikli tovarlar uchun jonli hisob.
   Hech narsa yubormaydi — faqat foydalanuvchi nima bo'lishini oldindan ko'rsin.
   Haqiqiy hisob har doim serverda (ombor/models.py, ombor/forms.py). */
(function () {
  "use strict";

  function son(matn) {
    var q = parseFloat(String(matn || "").replace(",", "."));
    return isNaN(q) ? 0 : q;
  }

  function chiroyli(q) {
    return q.toLocaleString("ru-RU", { maximumFractionDigits: 3 }).replace(/ /g, " ");
  }

  // Qoldiqni qadoq bilan aytadi: 5020 dona, 1 pachka = 1000 -> "5 pachka 20 dona".
  // Serverdagi Mahsulot.qadoq_matni bilan bir xil qoida.
  function qadoqMatni(qoldiq, nechta, olish, sotuv) {
    if (!nechta || nechta <= 0) return chiroyli(qoldiq) + " " + sotuv;
    var butun = Math.floor(qoldiq / nechta);
    var ortiq = qoldiq - butun * nechta;
    // suzuvchi nuqta xatosini yumshatamiz (0.30000000000000004 kabi)
    ortiq = Math.round(ortiq * 1000) / 1000;
    var bolaklar = [];
    if (butun) bolaklar.push(chiroyli(butun) + " " + olish);
    if (ortiq || !butun) bolaklar.push(chiroyli(ortiq) + " " + sotuv);
    return bolaklar.join(" ");
  }

  function matnQoy(sinf, matn) {
    document.querySelectorAll("." + sinf).forEach(function (el) { el.textContent = matn; });
  }

  // ---------- Tovar formasi ----------
  // «Birlik o'zgaradi» richagi yoqilsa forma qadoq bo'yicha savol beradi va
  // qoldiqni o'zi hisoblaydi. O'chiq bo'lsa oddiy tovar kartochkasi qoladi.
  function mahsulotFormasi() {
    var forma = document.getElementById("mahsulot-forma");
    if (!forma) return;

    var richag = document.getElementById("birlik-richag");
    var belgi = document.getElementById("birlik-ozgaradi");
    var birlik = document.getElementById("id_birlik");
    var olishBirligi = document.getElementById("id_olish_birligi");
    var olishMiqdori = document.getElementById("id_olish_miqdori");
    var narx = document.getElementById("id_narx");
    var qoldiq = document.getElementById("id_qoldiq");
    var qoldiqMaydon = document.getElementById("qoldiq-maydon");
    var qadoqSoni = document.getElementById("qadoq-soni");
    var birlikYorliq = document.getElementById("birlik-yorliq");
    var qoida = document.getElementById("birlik-qoida");
    if (!belgi || !birlik || !olishBirligi || !olishMiqdori) return;

    var yangiMi = forma.dataset.yangi === "1";

    function yangila() {
      var yoniq = belgi.checked;
      var sotuv = birlik.value;
      var olish = olishBirligi.value;

      richag.classList.toggle("yoniq", yoniq);
      forma.querySelectorAll("[data-ikki]").forEach(function (el) { el.hidden = !yoniq; });

      matnQoy("sotuv-birlik-nomi", sotuv);
      matnQoy("olish-birlik-nomi", olish || "qadoq");
      birlikYorliq.textContent = yoniq ? "Sotiladigan birligi" : "Sotuv birligi";

      // Yangi tovarda qoldiq qadoq sonidan chiqadi — qo'lda yozilmaydi.
      var qoldiqYashirin = yoniq && yangiMi;
      qoldiqMaydon.hidden = qoldiqYashirin;

      if (!yoniq) {
        qoida.hidden = true;
        return;
      }

      qoida.classList.remove("ogoh");
      var nechta = son(olishMiqdori.value);
      if (!olish) {
        qoida.hidden = false;
        qoida.classList.add("ogoh");
        qoida.textContent = "Tovar qaysi birlikda kelishini tanlang.";
        return;
      }
      if (olish === sotuv) {
        qoida.hidden = false;
        qoida.classList.add("ogoh");
        qoida.textContent = "Kelgan va sotiladigan birlik bir xil — birlik " +
                            "o'zgarmasa richagni o'chiring.";
        return;
      }
      if (nechta <= 0) {
        qoida.hidden = false;
        qoida.classList.add("ogoh");
        qoida.textContent = "1 " + olish + "da nechta " + sotuv + " borligini yozing.";
        return;
      }

      // Narx doim sotuv birligida; qadoq narxi shundan ko'rsatiladi.
      var dona = son(narx.value);
      var qadoqNarxi = dona * nechta;

      var qatorlar = ["1 " + olish + " = " + chiroyli(nechta) + " " + sotuv];

      if (qoldiqYashirin) {
        var qadoq = son(qadoqSoni && qadoqSoni.value);
        if (qadoq > 0) {
          qatorlar.push(chiroyli(qadoq) + " " + olish + " = " +
                        chiroyli(qadoq * nechta) + " " + sotuv + " omborga tushadi");
        } else {
          qatorlar.push("qadoq soni yozilmagan — qoldiq 0 bo'ladi");
        }
      } else if (son(qoldiq.value) > 0) {
        qatorlar.push("Qoldiq: " + chiroyli(son(qoldiq.value)) + " " + sotuv + " = " +
                      qadoqMatni(son(qoldiq.value), nechta, olish, sotuv));
      }

      if (dona > 0) {
        qatorlar.push("1 " + sotuv + " " + chiroyli(Math.round(dona)) + " so'm");
        qatorlar.push("1 " + olish + " " + chiroyli(Math.round(qadoqNarxi)) + " so'm");
      }

      qoida.hidden = false;
      qoida.classList.remove("ogoh");
      qoida.textContent = qatorlar.join("  ·  ");
    }

    [belgi, birlik, olishBirligi, olishMiqdori, narx, qoldiq, qadoqSoni]
      .forEach(function (el) {
        if (!el) return;
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
      var b = forma.querySelector('input[name="birlik"]:checked');
      return b ? b.value : sotuv;
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
      if (ikki) matn += " (" + qadoqMatni(yangi, nechta, olish, sotuv) + ")";

      natija.hidden = false;
      natija.textContent = matn;
    }

    // Sensorli rejimdagi raqamlar klaviaturasi — to'g'ridan-to'g'ri miqdor
    // maydoniga yozadi, shunda jonli izoh yozayotganda ham ko'rinib turadi.
    var raqamlar = document.getElementById("kirim-raqamlar");
    if (raqamlar) {
      raqamlar.addEventListener("click", function (e) {
        var t = e.target.closest("button");
        if (!t) return;
        if (t.dataset.raqam) {
          var b = t.dataset.raqam;
          var q = miqdor.value === "0" ? "" : miqdor.value;
          if (b === "." && q.indexOf(".") !== -1) return;
          if (b === "." && q === "") q = "0";
          miqdor.value = q + b;
        } else if (t.dataset.amal === "ochir") {
          miqdor.value = miqdor.value.slice(0, -1);
        }
        yangila();
      });
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

  // ---------- Ombor ro'yxati: satr bosilsa kirim ichki oyna bo'lib ochiladi ----------
  function omborRoyxati() {
    var jadval = document.getElementById("ombor-jadval");
    var oyna = document.getElementById("kirim-oyna");
    if (!jadval || !oyna) return;

    var tana = document.getElementById("kirim-oyna-tana");
    var nomi = document.getElementById("kirim-oyna-nom");

    function yop() {
      oyna.classList.remove("ochiq");
      tana.innerHTML = "";
    }

    function och(manzil, tovar) {
      nomi.textContent = "Kirim: " + tovar;
      tana.innerHTML = '<div class="bosh-holat">Yuklanmoqda…</div>';
      oyna.classList.add("ochiq");
      fetch(manzil, { credentials: "same-origin" })
        .then(function (javob) {
          if (!javob.ok) throw new Error(javob.status);
          return javob.text();
        })
        .then(function (html) {
          tana.innerHTML = html;
          kirimFormasi();          // yangi formaga hisob va numpadni ulaymiz
          var m = document.getElementById("kirim-miqdor");
          if (m && !document.body.classList.contains("rejim-sensor")) m.focus();
        })
        .catch(function () {
          tana.innerHTML = '<div class="xabar error"><span>Kirim formasini ' +
                           "yuklab bo'lmadi. Sahifani yangilang.</span></div>";
        });
    }

    jadval.addEventListener("click", function (e) {
      if (e.target.closest("[data-kirimsiz]")) return;   // qalam va tarix tugmalari
      var qator = e.target.closest("tr[data-kirim]");
      if (!qator) return;
      e.preventDefault();                                 // «Kirim» havolasi ham shu yerda
      och(qator.dataset.kirim, qator.dataset.nom);
    });

    oyna.addEventListener("click", function (e) {
      if (e.target === oyna || e.target.closest("[data-yop]")) yop();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && oyna.classList.contains("ochiq")) yop();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    mahsulotFormasi();
    kirimFormasi();
    omborRoyxati();
  });
})();
