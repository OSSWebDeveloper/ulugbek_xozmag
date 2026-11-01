/* Etiketka sahifasi: nechta nusxa va qaysi o'lchamda — chop etish brauzerning
   o'z oynasida. Har bir etiketka alohida sahifa, sahifa o'lchami (@page) —
   etiketka o'lchami: printer rulonni aynan shunday kesadi.
   O'lcham brauzerda eslab qolinadi — do'konda printer ham, rulon ham bitta. */
(function () {
  "use strict";

  var KALIT = "ux_etiketka_olcham";
  var OLCHAMLAR = { "40x30": [40, 30], "58x40": [58, 40], "56x40": [56, 40], "50x30": [50, 30], "30x20": [30, 20] };

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
    var printerDialog = document.getElementById('etiketka-printer-dialog');
    var printerForma = document.getElementById('etiketka-printer-forma');
    var printerSelect = document.getElementById('etiketka-native-printer');
    var status = document.getElementById('etiketka-printer-izoh');
    var submit = document.getElementById('etiketka-native-submit');
    var busy = false;
    var jobId = null;
    function newId() {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var random = new Uint8Array(1);
        window.crypto.getRandomValues(random);
        var n = random[0] & 15;
        return (c === 'x' ? n : (n & 3) | 8).toString(16);
      });
    }
    async function readResponse(response) {
      if (response.redirected) throw new Error('Seans tugadi. Sahifani yangilang.');
      var data = await response.json();
      if (!response.ok) throw new Error(data.xato || 'Printer bilan aloqa xatosi.');
      return data;
    }
    document.getElementById('etiketka-printer-bekor').addEventListener('click', function () { printerDialog.close(); });
    printerForma.addEventListener('submit', async function(event) {
      event.preventDefault();
      if (busy || !printerSelect.value) return;
      busy = true; submit.disabled = true;
      status.textContent = 'Printerga yuborilmoqda…';
      if (!jobId) jobId = newId();
      try {
        var data = await readResponse(await fetch(printerForma.dataset.print, {
          method: 'POST', headers: {'Content-Type': 'application/json',
            'X-CSRFToken': printerForma.querySelector('[name=csrfmiddlewaretoken]').value},
          body: JSON.stringify({id: jobId, printer: printerSelect.value,
            olcham: olchamEl.value, soni: soniEl.value})
        }));
        for (var i = 0; i < 65; i++) {
          var result = await readResponse(await fetch(printerForma.dataset.status.replace('00000000-0000-0000-0000-000000000000', data.id), {cache: 'no-store'}));
          status.textContent = result.xabar;
          if (result.holat !== 'yuborilmoqda') { jobId = null; return; }
          await new Promise(function(resolve) { setTimeout(resolve, 1000); });
        }
        status.textContent = 'Chop holati noma’lum. Yana yuborishdan oldin printer navbatini va qog‘ozni tekshiring.';
      } catch (error) { status.textContent = error.message; }
      finally { busy = false; submit.disabled = false; }
    });
    document.getElementById('chop-et').addEventListener('click', async function () {
      nusxala();
      printerDialog.showModal();
      document.getElementById('etiketka-printer-summary').textContent = soniEl.value + ' nusxa · ' + olchamEl.options[olchamEl.selectedIndex].text;
      if (busy) return;
      submit.disabled = true;
      status.textContent = 'Printerlar olinmoqda…';
      try {
        var data = await readResponse(await fetch(printerForma.dataset.list, {cache: 'no-store'}));
        printerSelect.replaceChildren();
        data.printerlar.sort(function(a,b) { return Number(/xprinter xp-80/i.test(b.nom)) - Number(/xprinter xp-80/i.test(a.nom)); });
        data.printerlar.forEach(function(printer) {
          var option = document.createElement('option');
          option.value = printer.nom; option.textContent = printer.nom + ' · ' + printer.port;
          printerSelect.appendChild(option);
        });
        submit.disabled = !data.printerlar.length;
        status.textContent = data.printerlar.length ? 'Printerni tanlang va yuboring.' : 'Windows’da printer topilmadi.';
      } catch (error) { status.textContent = error.message; }
    });
  });
})();
