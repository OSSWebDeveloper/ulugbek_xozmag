/* Qarz qo'shish ekrani: tovar tanlash, raqamlar klaviaturasi, summa hisobi. */
(function () {
  "use strict";

  var oyna, qidiruv, miqdorEl, narxEl, summaEl, mahsulotId, tanlanganEl, qoshTugma, forma;
  var faolMaydon = "miqdor";

  function son(matn) {
    var t = String(matn || "").replace(",", ".");
    var q = parseFloat(t);
    return isNaN(q) ? 0 : q;
  }

  function chiroyli(q) {
    return q.toLocaleString("ru-RU", { maximumFractionDigits: 2 });
  }

  function summaYangila() {
    var s = son(miqdorEl.value) * son(narxEl.value);
    summaEl.textContent = chiroyli(s);
    qoshTugma.disabled = !(mahsulotId.value && son(miqdorEl.value) > 0);
  }

  function faolQoy(nomi) {
    faolMaydon = nomi;
    document.querySelectorAll(".kiritish-maydon[data-maydon]").forEach(function (el) {
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

  function amalBajar(amal) {
    var el = joriyInput();
    if (amal === "ochir") el.value = el.value.slice(0, -1);
    else if (amal === "tozala") el.value = "";
    else if (amal === "hammasi") tozalaHammasi();
    summaYangila();
  }

  function tozalaHammasi() {
    mahsulotId.value = "";
    miqdorEl.value = "";
    narxEl.value = "";
    tanlanganEl.className = "tanlangan-tovar";
    tanlanganEl.innerHTML = '<span class="bosh-yozuv">Tovar tanlanmagan</span>';
    faolQoy("miqdor");
    summaYangila();
  }

  function tovarTanla(karta) {
    mahsulotId.value = karta.dataset.id;
    narxEl.value = karta.dataset.narx;
    miqdorEl.value = "";
    tanlanganEl.className = "tanlangan-tovar tanlangan";
    tanlanganEl.innerHTML =
      '<span class="nom">' + karta.dataset.nom + "</span>" +
      '<span class="qoldiq">Omborda: ' + karta.dataset.qoldiq + " " + karta.dataset.birlik +
      " &middot; narxi " + chiroyli(son(karta.dataset.narx)) + " so'm</span>";
    document.querySelector("#miqdor-birlik").textContent = karta.dataset.birlik;
    oynaYop();
    faolQoy("miqdor");
    summaYangila();
  }

  function oynaOch() {
    oyna.classList.add("ochiq");
    qidiruv.value = "";
    filtrla("");
    if (!document.body.classList.contains("rejim-sensor")) qidiruv.focus();
  }

  function oynaYop() {
    oyna.classList.remove("ochiq");
  }

  function filtrla(matn) {
    var q = matn.toLowerCase().trim();
    document.querySelectorAll(".tovar-karta").forEach(function (k) {
      k.style.display = !q || k.dataset.nom.toLowerCase().indexOf(q) !== -1 ? "" : "none";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
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
    oyna.addEventListener("click", function (e) {
      if (e.target === oyna || e.target.hasAttribute("data-yop")) return oynaYop();
      var karta = e.target.closest(".tovar-karta");
      if (karta && !karta.classList.contains("yoq")) tovarTanla(karta);
    });
    qidiruv.addEventListener("input", function () { filtrla(this.value); });

    document.querySelectorAll(".kiritish-maydon[data-maydon]").forEach(function (el) {
      el.addEventListener("click", function () { faolQoy(el.dataset.maydon); });
    });

    document.getElementById("tozala-tugma").addEventListener("click", tozalaHammasi);

    document.getElementById("raqamlar").addEventListener("click", function (e) {
      var t = e.target.closest("button");
      if (!t) return;
      if (t.dataset.raqam) raqamBos(t.dataset.raqam);
      else if (t.dataset.amal) amalBajar(t.dataset.amal);
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
