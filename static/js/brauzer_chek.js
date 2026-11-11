/* Chekni shu qurilmaning brauzeridan chiqarish: chek qog'ozi yashirin ramkada
   ochiladi, ramka ichidagi sahifa chop oynasini o'zi chaqiradi.
   window.brauzerChek(url) — sinov cheki uchun ham (qurilmalar.js). */
(function () {
  'use strict';
  window.brauzerChek = function (url) {
    var eski = document.getElementById('brauzer-chek');
    if (eski) eski.remove();
    var ramka = document.createElement('iframe');
    ramka.id = 'brauzer-chek';
    ramka.className = 'brauzer-chek';
    ramka.title = 'Chek chop etilmoqda';
    ramka.setAttribute('aria-hidden', 'true');
    ramka.src = url;
    document.body.appendChild(ramka);
  };
  var belgi = document.querySelector('[data-brauzer-chek]');
  if (belgi) window.brauzerChek(belgi.dataset.brauzerChek);
})();
