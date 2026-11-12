/* Etiketka sahifasi: nechta nusxa va qaysi o'lchamda — chop etish brauzerning
   o'z oynasida. Har bir etiketka alohida sahifa. Sahifa o'lchami (@page size)
   berilmaydi: brauzer printerning o'z qog'ozini oladi va yorliqni uning yuqori
   chap burchagiga 1:1 qo'yadi. O'lcham berilsa, brauzer yorliq sahifasini
   printer qog'ozining o'rtasiga joylaydi, rulonli printerda 90° burib yuboradi
   va bo'sh chetiga sahifa raqamini («1/1») qo'shadi.
   O'lcham brauzerda eslab qolinadi — do'konda printer ham, rulon ham bitta. */
(function () {
  "use strict";

  var KALIT = "ux_etiketka_olcham";
  var PRINTER_KALIT = "ux_etiketka_printer";
  // Shtrix (etiketka) printeri birinchi, chek printeri oxirida — oxirgi tanlov esa eng tepada.
  var ETIKETKA_PRINTER = /label|barcode|shtrix|etiket|zebra|tsc|godex|xp-?(3\d\d|4\d\d|dt|tt)/i;
  var CHEK_PRINTER = /xp-?(58|80)|pos-?(58|80)|receipt|chek/i;
  var OLCHAMLAR = { "40x30": [40, 30], "58x40": [58, 40], "56x40": [56, 40], "50x30": [50, 30], "30x20": [30, 20] };

  var joy, namuna, soniEl, olchamEl, engKop;

  function oqi() {
    try { return localStorage.getItem(KALIT); } catch (e) { return null; }
  }

  function yoz(qiymat, kalit) {
    try { localStorage.setItem(kalit || KALIT, qiymat); } catch (e) { /* yopiq bo'lsa ham ishlayversin */ }
  }

  function printerOchko(nom, oxirgi) {
    if (nom === oxirgi) return 3;
    if (ETIKETKA_PRINTER.test(nom)) return 2;
    return CHEK_PRINTER.test(nom) ? 0 : 1;
  }

  function olchamQoy(nomi) {
    if (!OLCHAMLAR[nomi]) nomi = "40x30";
    olchamEl.value = nomi;
    joy.dataset.olcham = nomi;          // etiketka ichidagi o'lchamlar CSS da (uslub.css)
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
    engKop = parseInt(soniEl.max, 10) || 500;
    // Server qayta ishga tushmaguncha eski shablonda sahifa o'lchami yozilgan
    // bo'lishi mumkin — uni olib tashlaymiz (yuqoridagi izohga qarang).
    var sahifaUslubi = document.getElementById("etiketka-sahifa-uslubi");
    if (sahifaUslubi) sahifaUslubi.textContent = "@page { margin: 0; }";

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
    // Yordamchisiz qurilma: yorliqlar shu brauzerning chop oynasi orqali chiqadi.
    // Har yorliq alohida sahifa; qog'oz o'lchami — printerning o'ziniki.
    document.getElementById('etiketka-brauzer').addEventListener('click', function () {
      nusxala();
      printerDialog.close();
      window.print();
    });
    printerForma.addEventListener('submit', async function(event) {
      event.preventDefault();
      if (busy || !printerSelect.value) return;
      yoz(printerSelect.value, PRINTER_KALIT);
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
    // «Printer qo'shish»: shu kompyuterda o'rnatilgan drayverlardan yangi Windows
    // printeri yaratiladi — ro'yxatda yo'q (hali qo'shilmagan) printer uchun.
    var qoshTugma = document.getElementById('etiketka-printer-qosh');
    var drayverQuti = document.getElementById('etiketka-drayver-quti');
    var drayverSelect = document.getElementById('etiketka-drayver');
    var portSelect = document.getElementById('etiketka-port');
    var drayverTasdiq = document.getElementById('etiketka-drayver-tasdiq');
    function toldir(select, qiymatlar) {
      select.replaceChildren();
      qiymatlar.forEach(function (q) {
        var option = document.createElement('option');
        option.value = q; option.textContent = q;
        select.appendChild(option);
      });
    }
    qoshTugma.addEventListener('click', async function () {
      drayverQuti.hidden = false;
      drayverTasdiq.disabled = true;
      status.textContent = 'Drayverlar olinmoqda…';
      try {
        var data = await readResponse(await fetch(printerForma.dataset.drivers, {cache: 'no-store'}));
        toldir(drayverSelect, data.drayverlar);
        toldir(portSelect, data.portlar);
        status.textContent = data.drayverlar.length ? 'Drayver va portni tanlab, «Qo‘shish» ni bosing.'
          : 'Bu kompyuterda printer drayveri o‘rnatilmagan.';
      } catch (error) { status.textContent = error.message; }
    });
    drayverSelect.addEventListener('change', function () { drayverTasdiq.disabled = !drayverSelect.value; });
    document.getElementById('etiketka-drayver-bekor').addEventListener('click', function () { drayverQuti.hidden = true; });
    drayverTasdiq.addEventListener('click', async function () {
      if (!drayverSelect.value || !portSelect.value) return;
      drayverTasdiq.disabled = true;
      status.textContent = 'Printer qo‘shilmoqda…';
      try {
        var data = await readResponse(await fetch(printerForma.dataset.add, {
          method: 'POST', headers: {'Content-Type': 'application/json',
            'X-CSRFToken': printerForma.querySelector('[name=csrfmiddlewaretoken]').value},
          body: JSON.stringify({drayver: drayverSelect.value, port: portSelect.value})
        }));
        drayverQuti.hidden = true;
        yoz(data.nom, PRINTER_KALIT);            // yangi printer ro'yxatda birinchi turadi
        await printerlarniOl();
        status.textContent = '«' + data.nom + '» qo‘shildi. Printerga yuborishingiz mumkin.';
      } catch (error) { status.textContent = error.message; drayverTasdiq.disabled = false; }
    });
    document.getElementById('chop-et').addEventListener('click', function () {
      nusxala();
      printerDialog.showModal();
      drayverQuti.hidden = true;
      document.getElementById('etiketka-printer-summary').textContent = soniEl.value + ' nusxa · ' + olchamEl.options[olchamEl.selectedIndex].text;
      if (busy) return;
      printerlarniOl();
    });
    async function printerlarniOl() {
      submit.disabled = true;
      status.textContent = 'Printerlar olinmoqda…';
      try {
        var data = await readResponse(await fetch(printerForma.dataset.list, {cache: 'no-store'}));
        if (data.brauzer) {
          // Yordamchisiz qurilma server printerini ishlatmaydi: brauzerning chop
          // oynasi ochiladi — unda shu kompyuterning o'z printerlari turadi.
          printerDialog.close();
          window.print();
          return;
        }
        printerSelect.replaceChildren();
        var oxirgi = null;
        try { oxirgi = localStorage.getItem(PRINTER_KALIT); } catch (e) { /* yopiq */ }
        data.printerlar.sort(function(a,b) { return printerOchko(b.nom, oxirgi) - printerOchko(a.nom, oxirgi); });
        data.printerlar.forEach(function(printer) {
          var option = document.createElement('option');
          option.value = printer.nom; option.textContent = printer.nom + ' · ' + printer.port;
          printerSelect.appendChild(option);
        });
        submit.disabled = !data.printerlar.length;
        qoshTugma.hidden = !data.qoshish;      // faqat server kompyuterining o'zida
        status.textContent = data.printerlar.length ? 'Printerni tanlang va yuboring.' : 'Windows’da printer topilmadi.';
      } catch (error) { status.textContent = error.message; }
    }
  });
})();
