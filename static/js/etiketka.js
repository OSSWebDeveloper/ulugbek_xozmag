/* Etiketka sahifasi: nechta nusxa va qaysi o'lchamda — chop etish brauzerning
   o'z oynasida. Har bir etiketka alohida sahifa, sahifa o'lchami (@page) —
   etiketka o'lchami: printer rulonni aynan shunday kesadi.
   O'lcham brauzerda eslab qolinadi — do'konda printer ham, rulon ham bitta. */
(function () {
  "use strict";

  var KALIT = "ux_etiketka_olcham";
  var OLCHAMLAR = { "40x30": [40, 30], "58x40": [58, 40], "50x30": [50, 30], "30x20": [30, 20] };

  var joy, namuna, soniEl, olchamEl, sahifaUslubi, engKop;

  function oqi() {
    try { return localStorage.getItem(KALIT); } catch (e) { return null; }
  }

  function yoz(qiymat) {
    try { localStorage.setItem(KALIT, qiymat); } catch (e) { /* yopiq bo'lsa ham ishlayversin */ }
  }

  function olchamQoy(nomi) {
    if (!OLCHAMLAR[nomi]) nomi = "40x30";
    var o = OLCHAMLAR[nomi];
    olchamEl.value = nomi;
    joy.dataset.olcham = nomi;          // etiketka ichidagi o'lchamlar CSS da (uslub.css)
    sahifaUslubi.textContent = "@page { size: " + o[0] + "mm " + o[1] + "mm; margin: 0; }";
  }

  function nusxala() {
    var soni = Math.min(Math.max(parseInt(soniEl.value, 10) || 1, 1), engKop);
    var bor = joy.children.length;
    for (var i = bor; i < soni; i++) joy.appendChild(namuna.content.cloneNode(true));
    for (var j = bor; j > soni; j--) joy.lastElementChild.remove();
  }

  document.addEventListener("DOMContentLoaded", function () {
    joy = document.getElementById("etiketkalar");
    namuna = document.getElementById("etiketka-namuna");
    if (!joy || !namuna) return;
    soniEl = document.getElementById("etiketka-soni");
    olchamEl = document.getElementById("etiketka-olcham");
    sahifaUslubi = document.getElementById("etiketka-sahifa-uslubi");
    engKop = parseInt(soniEl.max, 10) || 500;

    olchamQoy(oqi());
    nusxala();

    olchamEl.addEventListener("change", function () {
      olchamQoy(olchamEl.value);
      yoz(olchamEl.value);
    });
    soniEl.addEventListener("input", nusxala);
    document.getElementById("chop-et").addEventListener("click", function () {
      nusxala();
      window.print();
    });
  });
})();
