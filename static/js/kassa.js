/* Kassa ekrani: tovar tanlash, miqdor/narx kiritish, summa va qaytim hisobi.
   Raqamlar klaviaturasi faqat sensorli rejimda ko'rinadi (CSS hal qiladi),
   lekin sichqoncha rejimida maydonlarga klaviaturadan yozish har doim ishlaydi. */
(function () {
  "use strict";

  var oyna, qidiruv, miqdorEl, narxEl, summaEl, mahsulotId, tanlanganEl, qoshTugma, forma;
  var faolMaydon = "miqdor";

  function son(matn) {
    var q = parseFloat(String(matn || "").replace(",", "."));
    return isNaN(q) ? 0 : q;
  }

  function chiroyli(q) {
    return q.toLocaleString("ru-RU", { maximumFractionDigits: 2 }).replace(/ /g, " ");
  }

  function sensorMi() {
    return document.body.classList.contains("rejim-sensor");
  }

  // ---------- Qator qo'shish ----------
  function summaYangila() {
    summaEl.textContent = chiroyli(son(miqdorEl.value) * son(narxEl.value));
    qoshTugma.disabled = !(mahsulotId.value && son(miqdorEl.value) > 0);
  }

  function faolQoy(nomi) {
    faolMaydon = nomi;
    document.querySelectorAll("[data-maydon]").forEach(function (el) {
      el.classList.toggle("faol", el.dataset.maydon === nomi);
    });
  }

  function joriyInput() {
    return faolMaydon === "narx" ? narxEl : miqdorEl;
  }

  function raqamBos(belgi) {
    var el = joriyInput();
    var q = el.value === "0" ? "" : el.value;
    if (belgi === "." && q.indexOf(".") !== -1) return;
    if (belgi === "." && q === "") q = "0";
    el.value = q + belgi;
    summaYangila();
  }

  function tozalaHammasi() {
    mahsulotId.value = "";
    miqdorEl.value = "";
    narxEl.value = "";
    tanlanganEl.className = "tanlangan-tovar";
    tanlanganEl.querySelector(".nom").textContent = "Tovar tanlanmagan";
    tanlanganEl.querySelector(".nom").classList.add("bosh-yozuv");
    document.getElementById("tovar-qoldiq").innerHTML = "&mdash;";
    document.getElementById("miqdor-birlik").innerHTML = "&mdash;";
    faolQoy("miqdor");
    summaYangila();
  }

  function tovarTanla(karta) {
    mahsulotId.value = karta.dataset.id;
    narxEl.value = karta.dataset.narx;
    miqdorEl.value = "";

    tanlanganEl.className = "tanlangan-tovar tanlangan";
    var nom = tanlanganEl.querySelector(".nom");
    nom.textContent = karta.dataset.nom;
    nom.classList.remove("bosh-yozuv");
    nom.title = karta.dataset.nom;
    document.getElementById("tovar-qoldiq").textContent =
      "Omborda: " + karta.dataset.qoldiq + " " + karta.dataset.birlik;
    document.getElementById("miqdor-birlik").textContent = karta.dataset.birlik;

    oynaYop();
    faolQoy("miqdor");
    summaYangila();
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

    var topilgan = [].slice.call(document.querySelectorAll(".tovar-karta"))
      .filter(function (k) { return k.dataset.nom.toLowerCase().indexOf(soz) !== -1; });

    if (!topilgan.length) {
      dropdown.innerHTML = '<div class="dropdown-bosh">Bunday tovar topilmadi</div>';
    } else {
      dropdown.innerHTML = topilgan.map(function (k) {
        var yoq = k.classList.contains("yoq");
        return '<button type="button" class="dropdown-qator' + (yoq ? " yoq" : "") +
          '" role="option" data-id="' + k.dataset.id + '">' +
          '<span class="d-nom">' + belgila(k.dataset.nom, soz) + "</span>" +
          '<span class="d-narx">' + chiroyli(son(k.dataset.narx)) + "</span>" +
          '<span class="d-qoldiq">' +
          (yoq ? "tugagan" : k.dataset.qoldiq + " " + k.dataset.birlik) + "</span></button>";
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

  // ---------- Naqd sotuv: mijoz bergan pul -> qaytim ----------
  function qaytimniUla() {
    var tolandi = document.getElementById("tolandi");
    var qaytim = document.getElementById("qaytim");
    var jamiEl = document.getElementById("jami-summa");
    if (!tolandi || !qaytim || !jamiEl) return;

    var jami = son(jamiEl.dataset.jami);
    function hisobla() {
      var farq = son(tolandi.value) - jami;
      qaytim.textContent = farq > 0 ? chiroyli(farq) : "0";
    }
    tolandi.addEventListener("input", hisobla);
    hisobla();
  }

  document.addEventListener("DOMContentLoaded", function () {
    qaytimniUla();

    forma = document.getElementById("qator-forma");
    if (!forma) return;

    oyna = document.getElementById("tovar-oyna");
    qidiruv = document.getElementById("tovar-qidiruv");
    miqdorEl = document.getElementById("miqdor");
    narxEl = document.getElementById("narx");
    summaEl = document.getElementById("summa");
    mahsulotId = document.getElementById("mahsulot-id");
    tanlanganEl = document.getElementById("tanlangan");
    qoshTugma = document.getElementById("qosh-tugma");

    document.getElementById("yangi-tovar").addEventListener("click", oynaOch);
    document.getElementById("tozala-tugma").addEventListener("click", tozalaHammasi);

    dropdown = document.getElementById("tovar-dropdown");

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
        summaYangila();
      }
    });

    [miqdorEl, narxEl].forEach(function (el) {
      el.addEventListener("input", summaYangila);
      el.addEventListener("focus", function () {
        faolQoy(el === narxEl ? "narx" : "miqdor");
      });
    });

    // Klaviatura yorliqlari (sichqoncha rejimi uchun)
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") return oynaYop();
      if (e.key === "F2") { e.preventDefault(); return oynaOch(); }
      if (oyna.classList.contains("ochiq")) return;
      if (e.key === "Enter" && document.activeElement.tagName !== "BUTTON") {
        if (!qoshTugma.disabled) { e.preventDefault(); forma.submit(); }
      }
    });

    tozalaHammasi();
  });
})();
