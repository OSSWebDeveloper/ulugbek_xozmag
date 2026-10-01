/* Ranglar katalogi: ro'yxatda qator bosilsa tahrirlash ochiladi, formada rang
   tanlagich #RRGGBB maydoni bilan birga yuradi, yuklash sahifasida tanlangan
   fayl matn maydoniga tushadi. */
(function () {
  "use strict";

  var HEX = /^#?[0-9a-f]{6}$/i;

  function royxat() {
    document.querySelectorAll("tr[data-href]").forEach(function (qator) {
      qator.addEventListener("click", function (e) {
        if (e.target.closest("a, button")) return;
        window.location.href = qator.dataset.href;
      });
    });
  }

  function rangTanlagich() {
    var tanlagich = document.getElementById("rang-tanlagich");
    var maydon = document.getElementById("id_hex");
    if (!tanlagich || !maydon) return;
    tanlagich.addEventListener("input", function () {
      maydon.value = tanlagich.value.toUpperCase();
    });
    maydon.addEventListener("input", function () {
      var q = maydon.value.trim();
      if (HEX.test(q)) tanlagich.value = (q.charAt(0) === "#" ? q : "#" + q).toLowerCase();
    });
  }

  /* Excel'dan saqlangan CSV ko'pincha Windows-1251 da bo'ladi — UTF-8 da
     o'qilganda kirill nomlar buzilsa qaytadan o'shanday o'qiladi. */
  function faylniOqi(fayl, qayerga) {
    var oquvchi = new FileReader();
    oquvchi.onload = function () {
      var matn = String(oquvchi.result || "");
      if (matn.indexOf("�") !== -1) {
        var ikkinchi = new FileReader();
        ikkinchi.onload = function () { qayerga.value = String(ikkinchi.result || ""); };
        ikkinchi.readAsText(fayl, "windows-1251");
        return;
      }
      qayerga.value = matn;
    };
    oquvchi.readAsText(fayl, "UTF-8");
  }

  function yuklash() {
    var fayl = document.getElementById("yuklash-fayl");
    var matn = document.getElementById("yuklash-matn");
    if (!fayl || !matn) return;
    fayl.addEventListener("change", function () {
      if (fayl.files && fayl.files[0]) faylniOqi(fayl.files[0], matn);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    royxat();
    rangTanlagich();
    yuklash();
  });
})();
