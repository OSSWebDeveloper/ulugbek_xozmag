/* Katalog varag'i: sozlama o'zgarsa sahifa shu zahoti qayta chiziladi
   (server o'zi tuzadi), «Chop etish» — brauzerning chop etish oynasi. */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var forma = document.getElementById("varaq-sozlama");
    if (!forma) return;
    forma.querySelectorAll("select").forEach(function (el) {
      el.addEventListener("change", function () { forma.submit(); });
    });
    var tugma = document.getElementById("chop-et");
    if (tugma) tugma.addEventListener("click", function () { window.print(); });
  });
})();
