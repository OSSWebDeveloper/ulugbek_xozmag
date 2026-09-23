/* Formalar uchun umumiy yordamchilar — har bir sahifada yuklanadi.

   1. Pul maydonlarida raqamlar o'zi guruhlanadi (autosplit): 200000 yozilsa
      maydonda «200 000» bo'lib turadi. Server bo'shliqlarni o'zi tozalaydi
      (ombor/xizmat.py dagi tozala), shuning uchun yuborishdan oldin hech
      narsa qilinmaydi. Maydonga `pul-maydon` klassi beriladi; kasr xonalari
      soni `data-kasr` bilan (standart 2, so'mda 0 ham bo'ladi).
   2. `data-tasdiq="Savol?"` — forma yuborilishidan oldin so'raladi. Savol
      atributda turadi, JS satriga yopishtirilmaydi: o'zbekcha apostrof
      («qo'shilgan») satrni buzib, forma so'ramasdan yuborilib ketardi.
   3. `data-bir-marta` — forma bir marta yuboriladi. Tugma ikki marta
      bosilsa ikkinchi so'rov ketmaydi: chek ikki marta yakunlanmaydi,
      tovar ikki marta qo'shilmaydi.

   Boshqa skriptlar uchun `window.Pul`:
     Pul.son("200 000,5")  -> 200000.5
     Pul.matn(200000)      -> «200 000» (uzilmas bo'shliq bilan — tugma
                              ichida son ikki qatorga bo'linib qolmaydi) */
(function () {
  "use strict";

  var UZILMAS = " ";

  function son(qiymat) {
    var q = parseFloat(String(qiymat == null ? "" : qiymat)
      .replace(/\s/g, "").replace(",", "."));
    return isNaN(q) ? 0 : q;
  }

  function guruhla(butun, ajratuvchi) {
    return butun.replace(/\B(?=(\d{3})+(?!\d))/g, ajratuvchi);
  }

  /* Ekranda ko'rsatish uchun: 200000 -> «200 000», 12.5 -> «12,5». */
  function matn(q, kasr) {
    kasr = kasr == null ? 2 : kasr;
    var bolak = Math.abs(q).toFixed(kasr).split(".");
    var natija = guruhla(bolak[0], UZILMAS);
    var ortiq = (bolak[1] || "").replace(/0+$/, "");
    return (q < 0 ? "-" : "") + natija + (ortiq ? "," + ortiq : "");
  }

  /* Maydondagi yozuv: faqat raqamlar va bitta kasr belgisi (vergul). */
  function tartibla(qiymat, kasr) {
    var s = String(qiymat).replace(/[^\d.,]/g, "");
    var joy = s.search(/[.,]/);
    var butun = joy === -1 ? s : s.slice(0, joy);
    var ortiq = joy === -1 ? null : s.slice(joy + 1).replace(/[.,]/g, "");
    butun = butun.replace(/^0+(?=\d)/, "");
    if (ortiq !== null && !butun) butun = "0";
    var natija = guruhla(butun, " ");
    if (ortiq !== null && kasr > 0) natija += "," + ortiq.slice(0, kasr);
    return natija;
  }

  function maydonniTartibla(el) {
    var kasr = el.dataset.kasr ? parseInt(el.dataset.kasr, 10) : 2;
    var eski = el.value;
    var yangi = tartibla(eski, kasr);
    if (yangi === eski) return;

    // Kursor o'z raqamining yonida qolsin: undan oldingi raqamlar sanaladi
    var fokusda = document.activeElement === el;
    var oldin = eski.slice(0, fokusda ? el.selectionStart : eski.length)
      .replace(/[^\d.,]/g, "").length;
    el.value = yangi;
    if (!fokusda) return;
    var joy = 0, sanaldi = 0;
    while (joy < yangi.length && sanaldi < oldin) {
      if (/[\d,]/.test(yangi.charAt(joy))) sanaldi += 1;
      joy += 1;
    }
    try { el.setSelectionRange(joy, joy); } catch (e) { /* ba'zi turlarda kursor yo'q */ }
  }

  window.Pul = { son: son, matn: matn, tartibla: maydonniTartibla };

  // Capture: boshqa ishlovchilar qiymatni o'qishidan oldin tartibga keladi
  document.addEventListener("input", function (e) {
    var el = e.target;
    if (e.isComposing || !el.classList || !el.classList.contains("pul-maydon")) return;
    maydonniTartibla(el);
  }, true);

  // ---------- Tasdiq va bir marta yuborish ----------
  document.addEventListener("submit", function (e) {
    var forma = e.target;
    if (!(forma instanceof HTMLFormElement)) return;

    var savol = forma.getAttribute("data-tasdiq");
    if (savol && !window.confirm(savol)) {
      e.preventDefault();
      return;
    }
    if (e.defaultPrevented || !forma.hasAttribute("data-bir-marta")) return;

    if (forma.hasAttribute("data-yuborildi")) {
      e.preventDefault();
      return;
    }
    forma.setAttribute("data-yuborildi", "");
    // Tugma keyinroq o'chiriladi — aks holda uning qiymati so'rovga tushmay qolardi
    setTimeout(function () {
      forma.querySelectorAll("button:not([type=button])").forEach(function (t) {
        if (!t.disabled) { t.disabled = true; t.setAttribute("data-bir-marta-ochdi", ""); }
      });
    }, 0);
  });

  // «Orqaga» bilan keshdan qaytgan sahifada formalar yana ishlasin
  window.addEventListener("pageshow", function (e) {
    if (!e.persisted) return;
    document.querySelectorAll("form[data-yuborildi]").forEach(function (forma) {
      forma.removeAttribute("data-yuborildi");
      forma.querySelectorAll("[data-bir-marta-ochdi]").forEach(function (t) {
        t.disabled = false;
        t.removeAttribute("data-bir-marta-ochdi");
      });
    });
  });

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".pul-maydon").forEach(maydonniTartibla);
  });
})();
