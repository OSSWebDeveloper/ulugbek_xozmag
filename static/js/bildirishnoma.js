/* Bildirishnomalar: o'ng yuqorida kichkina qalqib chiqadi va 5 soniyadan keyin
   o'zi o'chadi. Sahifa joylashuvini surmaydi — ustida turadi.
   Bosilsa darrov yopiladi.

   Serverdan kelgan xabarlar base.html da chiziladi; sahifaning o'zi ham
   `xabarBer('matn', 'error')` bilan xabar chiqara oladi — skaner notanish
   kod o'qiganda shu ishlatiladi. */
(function () {
  "use strict";

  var KUTISH = 5000;   // necha millisekunddan keyin o'chadi
  var SONISH = 300;    // so'nish animatsiyasining davomiyligi

  function yop(xabar) {
    if (xabar.classList.contains("ketmoqda")) return;
    xabar.classList.add("ketmoqda");
    setTimeout(function () {
      var quti = xabar.parentNode;
      xabar.remove();
      if (quti && !quti.children.length) quti.remove();
    }, SONISH);
  }

  function ulash(xabar, kechikish) {
    xabar.addEventListener("click", function () { yop(xabar); });
    setTimeout(function () { yop(xabar); }, KUTISH + (kechikish || 0));
  }

  function qutiniOl() {
    var quti = document.getElementById("xabarlar");
    if (quti) return quti;
    // Serverdan xabar kelmagan bo'lsa quti ham yo'q — o'zimiz yasaymiz.
    quti = document.createElement("div");
    quti.className = "xabarlar";
    quti.id = "xabarlar";
    quti.setAttribute("role", "status");
    quti.setAttribute("aria-live", "polite");
    (document.querySelector(".ish") || document.body).prepend(quti);
    return quti;
  }

  /* Sahifaning o'zidan xabar chiqarish. `tur`: 'error', 'warning' yoki bo'sh. */
  window.xabarBer = function (matn, tur) {
    var xabar = document.createElement("div");
    xabar.className = "xabar " + (tur || "success");
    var ikon = tur === "error" || tur === "warning" ? "i-ogoh" : "i-belgi";
    xabar.innerHTML = '<svg class="ikon"><use href="#' + ikon + '"></use></svg><span></span>';
    xabar.querySelector("span").textContent = matn;
    qutiniOl().appendChild(xabar);
    ulash(xabar, 0);
    return xabar;
  };

  document.addEventListener("DOMContentLoaded", function () {
    var quti = document.getElementById("xabarlar");
    if (!quti) return;
    // Bir nechta xabar bo'lsa ketma-ket o'chadi, hammasi birdan yo'qolmaydi
    [].forEach.call(quti.children, function (xabar, tartib) {
      ulash(xabar, tartib * 500);
    });
  });
})();
