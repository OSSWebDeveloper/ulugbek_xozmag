/* Rang cheki sahifasi: qog'oz eni, nusxalar va chop etish.

   Chop etish brauzerning o'z oynasi orqali — printer Windows'da o'rnatilgan
   bo'lsa bas. Sahifa o'lchami (@page) chekning o'z uzunligicha: termoprinter
   rulonni keraksiz uzun chiqarmaydi. Qog'oz eni shu kompyuterda eslab qolinadi.

   Stansiyadan yangi chiqqan chek (`data-chop`) o'zi chop etiladi va chop
   etish oynasi yopilgach stansiyaga qaytadi — sotuvchi keyingi mijozga
   darrov o'tadi. Brauzer `--kiosk-printing` bilan ochilgan bo'lsa oyna ham
   chiqmaydi, chek to'g'ridan-to'g'ri printerga ketadi. */
(function () {
  "use strict";

  var KALIT = "ux_rang_chek_eni";
  var joy, namuna, eniEl, nusxaEl, uslub;

  function oqi() {
    try { return localStorage.getItem(KALIT); } catch (e) { return null; }
  }

  function yoz(qiymat) {
    try { localStorage.setItem(KALIT, qiymat); } catch (e) { /* yopiq bo'lsa ham ishlayversin */ }
  }

  function nusxala() {
    var soni = Math.min(Math.max(parseInt(nusxaEl.value, 10) || 1, 1), 3);
    var bor = joy.children.length;
    for (var i = bor; i < soni; i++) joy.appendChild(namuna.content.cloneNode(true));
    for (var j = bor; j > soni; j--) joy.lastElementChild.remove();
  }

  /* Chek balandligi mm da. Ekranda kattalashtirilgan (zoom) bo'lsa ham
     to'g'ri chiqadi: o'lchagich xuddi shu joyda turadi, nisbat saqlanadi. */
  function balandlikMm() {
    var chek = joy.querySelector(".rang-chek");
    var olchagich = document.createElement("div");
    olchagich.style.cssText = "position:absolute;visibility:hidden;height:100mm;width:1px";
    joy.appendChild(olchagich);
    var mm = chek.offsetHeight / (olchagich.offsetHeight / 100);
    olchagich.remove();
    return Math.ceil(mm) + 2;
  }

  function sahifaniMosla() {
    var eni = joy.dataset.eni === "58" ? 58 : 80;
    uslub.textContent = "@page { size: " + eni + "mm " + balandlikMm() + "mm; margin: 0; }";
  }

  function eniQoy(eni) {
    if (eni !== "58") eni = "80";
    eniEl.value = eni;
    joy.dataset.eni = eni;
    sahifaniMosla();
  }

  function chopEt() {
    nusxala();
    sahifaniMosla();
    window.print();
  }

  document.addEventListener("DOMContentLoaded", function () {
    var sahifa = document.getElementById("rang-chek-sahifa");
    joy = document.getElementById("rang-cheklar-joy");
    namuna = document.getElementById("rang-chek-namuna");
    if (!sahifa || !joy || !namuna) return;
    eniEl = document.getElementById("chek-eni");
    nusxaEl = document.getElementById("chek-nusxa");
    uslub = document.getElementById("rang-chek-sahifa-uslubi");

    nusxala();
    eniQoy(oqi());

    eniEl.addEventListener("change", function () {
      eniQoy(eniEl.value);
      yoz(eniEl.value);
    });
    nusxaEl.addEventListener("input", nusxala);
    document.getElementById("chop-et").addEventListener("click", chopEt);

    if (sahifa.hasAttribute("data-chop")) {
      window.addEventListener("afterprint", function () {
        window.location.replace(sahifa.dataset.qaytish);
      });
      // Shriftlar yuklanib, o'lcham aniq bo'lgach
      (document.fonts ? document.fonts.ready : Promise.resolve()).then(function () {
        setTimeout(chopEt, 150);
      });
    }
  });
})();
