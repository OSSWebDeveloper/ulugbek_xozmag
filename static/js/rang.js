/* Rang mashinasi stansiyasi: rang + baza bo'yoq + narx -> maxsus chek.

   Skaner fokusga qaramaydi (js/skaner.js). Kod serverga (/rang/kod/) boradi,
   server o'zi aytadi: katalogdagi rangmi, bankadagi do'kon etiketkasimi
   (baza bo'yoq) yoki oldin chiqqan chekmi. Qoidalar bu yerda takrorlanmaydi.

   Rang va baza tanlangach miqdor va kolerovka narxi yoziladi, «Chek
   chiqarish» yoki Enter. Summa faqat ko'rsatish uchun hisoblanadi: chekka
   server yozadi, kassada esa kassir baribir o'zi yozadi. So'm va dollar
   qo'shilmaydi — dollarlik baza alohida turadi. */
(function () {
  "use strict";

  var forma, rangId, bazaId, rangTanlov, namuna, kodiEl, nomiEl, kodEl;
  var bazaEl, bazaNomi, bazaQoldiq, bazaKodi, miqdorEl, birlikEl, narxEl;
  var hisobEl, jamiEl, tugma, oyna, qidiruv, dropdown, sora;
  var baza = null;
  var faolMaydon = "miqdor";

  function son(matn) { return window.Pul.son(matn); }
  function pul(q, kasr) { return window.Pul.matn(q, kasr); }
  function sensorMi() { return document.body.classList.contains("rejim-sensor"); }

  // ---------- Hisob va tugma ----------
  function holatYangila() {
    var miqdor = son(miqdorEl.value);
    var narx = son(narxEl.value);
    var dollar = !!baza && baza.valyuta === "$";
    var bazaNarx = baza ? son(baza.narx) : 0;
    var bazaSumma = bazaNarx * miqdor;
    var som = narx + (dollar ? 0 : bazaSumma);

    var bolaklar = [];
    if (baza) {
      bolaklar.push("Baza " + (bazaNarx
        ? pul(bazaSumma, dollar ? 2 : 0) + (dollar ? " $" : " so'm")
        : "— narxi yozilmagan"));
    }
    bolaklar.push("kolerovka " + pul(narx, 0) + " so'm");
    hisobEl.textContent = bolaklar.join(" + ");

    jamiEl.innerHTML = (dollar && bazaSumma ? pul(bazaSumma, 2) + "<small>$</small> + " : "") +
      pul(som, 0) + "<small>so'm</small>";
    tugma.disabled = !(rangId.value && bazaId.value && miqdor > 0);
  }

  function fokusQoy() {
    // Keyingi qadam qaysi bo'lsa o'sha maydon faol: sichqoncha rejimida kursor
    // ham o'sha yerda, sensorli rejimda raqamlar klaviaturasi o'shanga yozadi
    if (rangId.value && bazaId.value) {
      faolQoy("narx");
      if (!sensorMi()) {
        narxEl.focus();
        narxEl.select();
      }
    } else if (!rangId.value && !sensorMi()) {
      kodEl.focus();
    }
  }

  // ---------- Rang ----------
  function rangQoy(r) {
    rangId.value = r.id;
    rangTanlov.classList.add("tanlangan");
    namuna.innerHTML = "";
    namuna.classList.toggle("bosh", !r.hex);
    namuna.style.setProperty("--rang", r.hex || "transparent");
    kodiEl.textContent = r.kod;
    kodiEl.title = r.kod;
    nomiEl.textContent = [r.nom, r.toplam].filter(Boolean).join(" · ") || "Nomi yozilmagan";
    kodEl.value = "";
    holatYangila();
  }

  function rangTozala() {
    rangId.value = "";
    rangTanlov.classList.remove("tanlangan");
    namuna.classList.remove("bosh");
    namuna.style.removeProperty("--rang");
    namuna.innerHTML = '<svg class="ikon"><use href="#i-shtrix"></use></svg>';
    kodiEl.textContent = "Rang tanlanmagan";
    nomiEl.textContent = "Katalogdagi shtrixni skanerlang yoki kodini yozing";
    holatYangila();
  }

  // ---------- Baza bo'yoq ----------
  function bazaQoy(b) {
    baza = b;
    bazaId.value = b.id;
    bazaEl.classList.add("tanlangan");
    bazaNomi.textContent = b.nom;
    bazaNomi.title = b.nom;
    bazaNomi.classList.remove("bosh-yozuv");
    bazaQoldiq.textContent = "Omborda: " + b.qoldiq_matni + " " + b.birlik +
      (b.narx_matni ? " · " + b.narx_matni : "");
    bazaKodi.textContent = b.qisqa || "";
    birlikEl.textContent = b.birlik;
    holatYangila();
  }

  // ---------- Server javobi ----------
  function kodTopildi(javob) {
    if (javob.tur === "chek") {
      window.location.href = javob.manzil;
      return;
    }
    if (javob.tur === "rang") {
      rangQoy(javob);
    } else if (javob.tur === "baza") {
      if (son(javob.qoldiq) <= 0) {
        // Kassa baribir ayira olmaydi — mijoz kassada qolib ketmasin
        return window.xabarBer(javob.nom + " omborda tugagan — avval kirim qiling.", "error");
      }
      bazaQoy(javob);
      oynaYop();
    }
    fokusQoy();
  }

  // ---------- Raqamlar klaviaturasi (sensorli rejim) ----------
  function faolQoy(nomi) {
    faolMaydon = nomi;
    document.querySelectorAll("[data-maydon]").forEach(function (el) {
      el.classList.toggle("faol", el.dataset.maydon === nomi);
    });
  }

  /* Raqamlar klaviaturasi faol maydonga yozadi. «Kod» ham shunga kiradi:
     saytning ekran klaviaturasi faqat harfli, «RAL 3020» ning raqamlari shu yerdan. */
  function joriyInput() {
    if (faolMaydon === "kod") return kodEl;
    return faolMaydon === "narx" ? narxEl : miqdorEl;
  }

  function raqamBos(belgi) {
    var el = joriyInput();
    var q = el.value === "0" ? "" : el.value;
    el.value = q + belgi;
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }

  // ---------- Baza tanlash oynasi (kassadagi bilan bir xil ko'rinish) ----------
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

  function dropdownYop() {
    dropdown.classList.remove("ochiq");
    dropdown.innerHTML = "";
  }

  function himoya(matn) {
    return String(matn).replace(/[&<>"]/g, function (b) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[b];
    });
  }

  function dropdownYangila() {
    var soz = qidiruv.value.toLowerCase().trim();
    if (!soz) return dropdownYop();
    var raqammi = /^\d+$/.test(soz);
    var topilgan = [].slice.call(oyna.querySelectorAll(".tovar-karta")).filter(function (k) {
      if (k.dataset.nom.toLowerCase().indexOf(soz) !== -1) return true;
      return raqammi && (k.dataset.kod || "").indexOf(soz) !== -1;
    });
    dropdown.innerHTML = topilgan.length ? topilgan.map(function (k) {
      var yoq = k.classList.contains("yoq");
      return '<button type="button" class="dropdown-qator' + (yoq ? " yoq" : "") +
        '" data-kod="' + himoya(k.dataset.kod) + '">' +
        '<span class="d-kod">' + himoya(k.dataset.qisqa || "") + "</span>" +
        '<span class="d-nom">' + himoya(k.dataset.nom) + "</span>" +
        '<span class="d-qoldiq">' + (yoq ? "tugagan" : himoya(k.dataset.qoldiq + " " + k.dataset.birlik)) +
        "</span></button>";
    }).join("") : '<div class="dropdown-bosh">Bunday tovar topilmadi</div>';
    dropdown.classList.add("ochiq");
  }

  function kartadanTanla(kod) {
    // Tanlov ham skaner yo'lidan o'tadi — narx va qoldiq serverdan keladi
    if (kod) sora(kod);
  }

  // ---------- Xato bilan qaytgan sahifa: tanlov o'chib ketmasin ----------
  function avvalgiTanlov() {
    var r = rangTanlov.dataset;
    if (r.id) {
      rangQoy({ id: r.id, kod: r.kod, nom: r.nom, hex: r.hex, toplam: r.toplam });
    }
    var b = bazaEl.dataset;
    if (b.id) {
      bazaQoy({ id: b.id, nom: b.nom, qisqa: b.qisqa, birlik: b.birlik, qoldiq_matni: b.qoldiq,
                narx: b.narx, narx_matni: "", valyuta: b.valyuta });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var stansiya = document.getElementById("rang-stansiya");
    if (!stansiya || !window.Skaner) return;

    forma = document.getElementById("rang-forma");
    rangId = document.getElementById("rang-id");
    bazaId = document.getElementById("baza-id");
    rangTanlov = document.getElementById("rang-tanlov");
    namuna = document.getElementById("rang-namuna");
    kodiEl = document.getElementById("rang-kodi");
    nomiEl = document.getElementById("rang-nomi");
    kodEl = document.getElementById("kod-kirish");
    bazaEl = document.getElementById("baza-tanlangan");
    bazaNomi = document.getElementById("baza-nomi");
    bazaQoldiq = document.getElementById("baza-qoldiq");
    bazaKodi = document.getElementById("baza-kodi");
    miqdorEl = document.getElementById("miqdor");
    birlikEl = document.getElementById("miqdor-birlik");
    narxEl = document.getElementById("rang-narxi");
    hisobEl = document.getElementById("rang-hisob");
    jamiEl = document.getElementById("rang-jami");
    tugma = document.getElementById("chek-tugma");
    oyna = document.getElementById("tovar-oyna");
    qidiruv = document.getElementById("tovar-qidiruv");
    dropdown = document.getElementById("tovar-dropdown");

    sora = window.Skaner.ulash({ manzil: stansiya.dataset.kodManzil, topilganda: kodTopildi });

    function izla() {
      var kod = kodEl.value.trim();
      if (kod) sora(kod);
    }
    document.getElementById("kod-topish").addEventListener("click", izla);
    kodEl.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      e.preventDefault();
      e.stopPropagation();
      izla();
    });
    kodEl.addEventListener("focus", function () { faolQoy("kod"); });

    [miqdorEl, narxEl].forEach(function (el) {
      el.addEventListener("input", holatYangila);
    });
    miqdorEl.addEventListener("focus", function () { faolQoy("miqdor"); });
    narxEl.addEventListener("focus", function () { faolQoy("narx"); });
    document.querySelectorAll("[data-maydon]").forEach(function (el) {
      el.addEventListener("click", function () {
        faolQoy(el.dataset.maydon);
        var kirish = el.querySelector("input");
        if (kirish && !sensorMi()) kirish.focus();
      });
    });

    document.getElementById("raqamlar").addEventListener("click", function (e) {
      var t = e.target.closest("button");
      if (!t) return;
      if (t.dataset.raqam) raqamBos(t.dataset.raqam);
      else if (t.dataset.amal === "ochir") {
        var el = joriyInput();
        el.value = el.value.replace(/\s+$/, "").slice(0, -1);
        el.dispatchEvent(new Event("input", { bubbles: true }));
      }
    });

    // Baza tanlash oynasi
    document.getElementById("baza-tanla").addEventListener("click", oynaOch);
    qidiruv.addEventListener("input", dropdownYangila);
    qidiruv.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      e.preventDefault();
      var birinchi = dropdown.querySelector(".dropdown-qator:not(.yoq)");
      if (birinchi) kartadanTanla(birinchi.dataset.kod);
    });
    oyna.addEventListener("click", function (e) {
      if (e.target === oyna || e.target.closest("[data-yop]")) return oynaYop();
      var qator = e.target.closest(".dropdown-qator");
      if (qator) {
        if (!qator.classList.contains("yoq")) kartadanTanla(qator.dataset.kod);
        return;
      }
      if (!e.target.closest(".qidiruv-quti")) dropdownYop();
      var karta = e.target.closest(".tovar-karta");
      if (karta && !karta.classList.contains("yoq")) kartadanTanla(karta.dataset.kod);
    });

    // Klaviatura: Enter — chek, F2 — baza ro'yxati, Esc — oynani yopish
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") return oynaYop();
      if (e.key === "F2") { e.preventDefault(); return oynaOch(); }
      if (oyna.classList.contains("ochiq")) return;
      if (e.key === "Enter" && document.activeElement !== kodEl &&
          document.activeElement.tagName !== "BUTTON" && document.activeElement.tagName !== "A") {
        e.preventDefault();
        if (!tugma.disabled) forma.requestSubmit(tugma);
      }
    });

    faolQoy("miqdor");
    avvalgiTanlov();
    holatYangila();
    fokusQoy();
  });
})();
