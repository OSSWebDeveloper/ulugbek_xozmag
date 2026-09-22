/* Kassa ekrani: tovar tanlash va miqdor kiritish.
   Narx hech qayerda hisoblanmaydi — do'konda savdolashiladi, shuning uchun
   chek/qarz summasi pastdagi «Jami» maydoniga qo'lda yoziladi.
   Raqamlar klaviaturasi faqat sensorli rejimda ko'rinadi (CSS hal qiladi),
   lekin sichqoncha rejimida maydonlarga klaviaturadan yozish har doim ishlaydi.

   Tovar uch yo'l bilan tanlanadi va uchalasi ham tovarTanla() ga boradi:
   ro'yxatdan bosib, «Kod» maydoniga oxirgi 4 raqamni urib, yoki skanerlab.
   Kodni tovarga aylantirish serverda (ombor/kod.py) — bu yerda takrorlanmaydi. */
(function () {
  "use strict";

  var oyna, qidiruv, miqdorEl, mahsulotId, tanlanganEl, qoshTugma, forma;
  var kodEl, kodiEl, kodSora;
  var faolMaydon = "miqdor";

  function son(matn) {
    var q = parseFloat(String(matn || "").replace(",", "."));
    return isNaN(q) ? 0 : q;
  }

  function sensorMi() {
    return document.body.classList.contains("rejim-sensor");
  }

  // ---------- Qator qo'shish ----------
  function holatYangila() {
    // Tovar tanlanib miqdor yozilmaguncha qator qo'shilmaydi.
    qoshTugma.disabled = !(mahsulotId.value && son(miqdorEl.value) > 0);
  }

  function faolQoy(nomi) {
    faolMaydon = nomi;
    document.querySelectorAll("[data-maydon]").forEach(function (el) {
      el.classList.toggle("faol", el.dataset.maydon === nomi);
    });
  }

  function joriyInput() {
    // Raqamlar klaviaturasi faol maydonga yozadi: miqdor yoki pastdagi «Jami».
    var quti = document.querySelector("[data-maydon].faol");
    var kirish = quti && quti.querySelector("input");
    return kirish || miqdorEl;
  }

  function raqamBos(belgi) {
    var el = joriyInput();
    var q = el.value === "0" ? "" : el.value;
    if (belgi === "." && q.indexOf(".") !== -1) return;
    if (belgi === "." && q === "") q = "0";
    el.value = q + belgi;
    holatYangila();
  }

  function tozalaHammasi() {
    mahsulotId.value = "";
    miqdorEl.value = "";
    if (kodEl) kodEl.value = "";
    if (kodiEl) kodiEl.textContent = "";
    tanlanganEl.className = "tanlangan-tovar";
    tanlanganEl.querySelector(".nom").textContent = "Tovar tanlanmagan";
    tanlanganEl.querySelector(".nom").classList.add("bosh-yozuv");
    document.getElementById("tovar-qoldiq").innerHTML = "&mdash;";
    document.getElementById("miqdor-birlik").innerHTML = "&mdash;";
    faolQoy("miqdor");
    holatYangila();
  }

  /* `miqdor` faqat kodning o'zi miqdorni aytganda beriladi: tarozi
     etiketkasidagi og'irlik yoki quti shtrixidagi soni. Qolgan hollarda
     bo'sh qoladi — kassir o'zi yozadi. */
  function tovarTanla(karta, miqdor) {
    mahsulotId.value = karta.dataset.id;
    miqdorEl.value = miqdor || "";
    if (kodEl) kodEl.value = "";
    if (kodiEl) kodiEl.textContent = karta.dataset.qisqa || "";

    tanlanganEl.className = "tanlangan-tovar tanlangan";
    var nom = tanlanganEl.querySelector(".nom");
    nom.textContent = karta.dataset.nom;
    nom.classList.remove("bosh-yozuv");
    nom.title = karta.dataset.nom;
    // Ikki birlikli tovarda ikkinchi birlik ham ko'rinadi (200 metr = 2 rulon).
    document.getElementById("tovar-qoldiq").textContent =
      "Omborda: " + karta.dataset.qoldiq + " " + karta.dataset.birlik +
      (karta.dataset.ikkinchi ? " · " + karta.dataset.ikkinchi : "") +
      // Dollarda kelgan tovar — summasi pastdagi dollar maydoniga yoziladi
      (karta.dataset.valyuta === "$" ? " · dollarda" : "");
    document.getElementById("miqdor-birlik").textContent = karta.dataset.birlik;

    oynaYop();
    faolQoy("miqdor");
    holatYangila();
    if (!sensorMi()) miqdorEl.focus();
  }

  // ---------- Tovar tanlash oynasi ----------
  function oynaOch() {
    oyna.classList.add("ochiq");
    qidiruv.value = "";
    dropdownYop();
    if (!sensorMi()) qidiruv.focus();
  }

  function oynaYop() {
    oyna.classList.remove("ochiq");
    dropdownYop();
  }

  // ---------- Qidiruv dropdowni ----------
  // Pastdagi kartalar hech qachon yashirilmaydi; natijalar maydon ostida chiqadi.
  var dropdown, nishonda = -1;

  function himoya(matn) {
    return matn.replace(/[&<>"]/g, function (b) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[b];
    });
  }

  function belgila(nom, soz) {
    var joy = nom.toLowerCase().indexOf(soz);
    if (joy === -1) return himoya(nom);
    return himoya(nom.slice(0, joy)) + "<mark>" + himoya(nom.slice(joy, joy + soz.length)) +
           "</mark>" + himoya(nom.slice(joy + soz.length));
  }

  function dropdownYop() {
    dropdown.classList.remove("ochiq");
    dropdown.innerHTML = "";
    qidiruv.setAttribute("aria-expanded", "false");
    nishonda = -1;
  }

  function dropdownYangila() {
    var soz = qidiruv.value.toLowerCase().trim();
    if (!soz) return dropdownYop();

    // Raqam yozilsa kod bo'yicha ham izlanadi: yorliqdagi 0027 ham topadi.
    var raqammi = /^\d+$/.test(soz);
    var topilgan = [].slice.call(document.querySelectorAll(".tovar-karta"))
      .filter(function (k) {
        if (k.dataset.nom.toLowerCase().indexOf(soz) !== -1) return true;
        return raqammi && (k.dataset.kod || "").indexOf(soz) !== -1;
      });

    if (!topilgan.length) {
      dropdown.innerHTML = '<div class="dropdown-bosh">Bunday tovar topilmadi</div>';
    } else {
      dropdown.innerHTML = topilgan.map(function (k) {
        var yoq = k.classList.contains("yoq");
        return '<button type="button" class="dropdown-qator' + (yoq ? " yoq" : "") +
          '" role="option" data-id="' + k.dataset.id + '">' +
          '<span class="d-nom">' + belgila(k.dataset.nom, soz) + "</span>" +
          '<span class="d-qoldiq">' +
          (yoq ? "tugagan" : k.dataset.qoldiq + " " + k.dataset.birlik +
            (k.dataset.ikkinchi ? " · " + k.dataset.ikkinchi : "")) + "</span></button>";
      }).join("");
    }
    dropdown.classList.add("ochiq");
    qidiruv.setAttribute("aria-expanded", "true");
    nishonda = -1;
  }

  function qatorlar() {
    return dropdown.querySelectorAll(".dropdown-qator:not(.yoq)");
  }

  function nishonQoy(yangi) {
    var r = qatorlar();
    if (!r.length) return;
    r.forEach(function (el) { el.classList.remove("nishonda"); });
    nishonda = (yangi + r.length) % r.length;
    r[nishonda].classList.add("nishonda");
    r[nishonda].scrollIntoView({ block: "nearest" });
  }

  function dropdowndanTanla(id) {
    var karta = document.querySelector('.tovar-karta[data-id="' + id + '"]');
    if (karta && !karta.classList.contains("yoq")) {
      dropdownYop();
      tovarTanla(karta);
    }
  }

  // ---------- Kod, shtrix va tarozi etiketkasi ----------
  /* Server tovarni topib berdi — kartasini ro'yxatdan olib tanlaymiz.
     Karta topilmasligi mumkin: tovar yashirilgan (faol emas) bo'lsa
     ro'yxatga umuman chiqmaydi. */
  function kodTopildi(javob) {
    var karta = document.querySelector('.tovar-karta[data-id="' + javob.id + '"]');
    if (!karta) {
      return window.xabarBer(javob.nom + " ro'yxatda yo'q — ombordan faollashtiring.",
                             "error");
    }
    if (karta.classList.contains("yoq")) {
      return window.xabarBer(javob.nom + " omborda tugagan.", "error");
    }
    tovarTanla(karta, javob.miqdor);
    if (javob.miqdor) {
      // Miqdorni kod o'zi aytdi (tarozi yoki quti) — kassir ko'rib tursin.
      window.xabarBer(javob.nom + ": " + javob.miqdor_matni + " " + javob.birlik);
    }
  }

  function kodniUlash() {
    var panel = document.querySelector(".ong-panel");
    kodEl = document.getElementById("kod-kirish");
    kodiEl = document.getElementById("tovar-kodi");
    if (!panel || !kodEl || !window.Skaner) return;

    kodSora = window.Skaner.ulash({
      manzil: panel.dataset.kodManzil,
      topilganda: kodTopildi,
    });

    function izla() {
      var kod = kodEl.value.trim();
      if (kod) kodSora(kod);
    }

    document.getElementById("kod-topish").addEventListener("click", izla);
    kodEl.addEventListener("focus", function () { faolQoy("kod"); });
    kodEl.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      // Enter bu yerda qator qo'shmaydi, tovar izlaydi.
      e.preventDefault();
      e.stopPropagation();
      izla();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    forma = document.getElementById("qator-forma");
    if (!forma) return;

    oyna = document.getElementById("tovar-oyna");
    qidiruv = document.getElementById("tovar-qidiruv");
    miqdorEl = document.getElementById("miqdor");
    mahsulotId = document.getElementById("mahsulot-id");
    tanlanganEl = document.getElementById("tanlangan");
    qoshTugma = document.getElementById("qosh-tugma");

    document.getElementById("yangi-tovar").addEventListener("click", oynaOch);
    document.getElementById("tozala-tugma").addEventListener("click", tozalaHammasi);

    dropdown = document.getElementById("tovar-dropdown");
    kodniUlash();

    oyna.addEventListener("click", function (e) {
      if (e.target === oyna || e.target.closest("[data-yop]")) return oynaYop();

      var qator = e.target.closest(".dropdown-qator");
      if (qator) {
        if (!qator.classList.contains("yoq")) dropdowndanTanla(qator.dataset.id);
        return;
      }
      // Ro'yxatdan tashqariga bosilsa ro'yxat yopiladi
      if (!e.target.closest(".qidiruv-quti")) dropdownYop();

      var karta = e.target.closest(".tovar-karta");
      if (karta && !karta.classList.contains("yoq")) tovarTanla(karta);
    });

    qidiruv.addEventListener("input", dropdownYangila);
    qidiruv.addEventListener("keydown", function (e) {
      if (!dropdown.classList.contains("ochiq")) return;
      if (e.key === "ArrowDown") { e.preventDefault(); nishonQoy(nishonda + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); nishonQoy(nishonda - 1); }
      else if (e.key === "Enter") {
        e.preventDefault();
        var r = qatorlar();
        var tanlov = nishonda >= 0 ? r[nishonda] : r[0];
        if (tanlov) dropdowndanTanla(tanlov.dataset.id);
      } else if (e.key === "Escape") {
        e.stopPropagation();
        dropdownYop();
      }
    });

    // Maydonni bosish uni faol qiladi (numpad shunga yozadi)
    document.querySelectorAll("[data-maydon]").forEach(function (el) {
      el.addEventListener("click", function () {
        faolQoy(el.dataset.maydon);
        if (!sensorMi()) {
          var kirish = el.querySelector("input");
          if (kirish) kirish.focus();
        }
      });
    });

    document.getElementById("raqamlar").addEventListener("click", function (e) {
      var t = e.target.closest("button");
      if (!t) return;
      if (t.dataset.raqam) raqamBos(t.dataset.raqam);
      else if (t.dataset.amal === "ochir") {
        var el = joriyInput();
        el.value = el.value.slice(0, -1);
        holatYangila();
      }
    });

    miqdorEl.addEventListener("input", holatYangila);
    miqdorEl.addEventListener("focus", function () { faolQoy("miqdor"); });

    // Pastdagi summa maydonlari ham numpadga ulanadi (sensorli rejim uchun)
    document.querySelectorAll(".tolov-panel [data-maydon] input").forEach(function (el) {
      var quti = el.closest("[data-maydon]");
      el.addEventListener("focus", function () { faolQoy(quti.dataset.maydon); });
    });

    // Klaviatura yorliqlari (sichqoncha rejimi uchun)
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") return oynaYop();
      if (e.key === "F2") { e.preventDefault(); return oynaOch(); }
      if (oyna.classList.contains("ochiq")) return;
      if (e.key === "Enter" && document.activeElement.tagName !== "BUTTON") {
        // «Jami» maydonida Enter o'sha formani yuboradi — aralashmaymiz.
        if (document.activeElement.closest("form") !== forma) return;
        if (!qoshTugma.disabled) { e.preventDefault(); forma.submit(); }
      }
    });

    tozalaHammasi();
  });
})();
