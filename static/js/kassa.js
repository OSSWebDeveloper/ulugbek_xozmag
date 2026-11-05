/* Kassa ekrani: tovar tanlash va miqdor kiritish.
   «Jami» serverda qatorlarning sotish narxi × miqdori bo'yicha to'ldiriladi.
   Savdolashilgan yakuniy summani pastdagi maydonda o'zgartirish mumkin.
   Raqamlar klaviaturasi faqat sensorli rejimda ko'rinadi (CSS hal qiladi),
   lekin sichqoncha rejimida maydonlarga klaviaturadan yozish har doim ishlaydi.

   Tovar uch yo'l bilan tanlanadi va uchalasi ham tovarTanla() ga boradi:
   ro'yxatdan bosib, «Kod» maydoniga oxirgi 4 raqamni urib, yoki skanerlab.
   Skanerlangani tanlanibgina qolmaydi — darrov chekka qo'shiladi.
   Kodni tovarga aylantirish serverda (ombor/kod.py) — bu yerda takrorlanmaydi. */
(function () {
  "use strict";

  var oyna, qidiruv, miqdorEl, mahsulotId, tanlanganEl, qoshTugma, forma;
  var kodEl, kodiEl, kodSora;
  var faolMaydon = "miqdor";

  // Pul maydonlarida son guruhlangan turadi («200 000») — js/forma.js o'qiydi
  function son(matn) {
    return window.Pul.son(matn);
  }

  function sensorMi() {
    return document.body.classList.contains("rejim-sensor");
  }

  // ---------- Qator qo'shish ----------
  function holatYangila() {
    // Tovar tanlanib miqdor yozilmaguncha qator qo'shilmaydi.
    qoshTugma.disabled = !(mahsulotId.value && son(miqdorEl.value) > 0);
  }

  function faolQoy(nomi) {
    faolMaydon = nomi;
    document.querySelectorAll("[data-maydon]").forEach(function (el) {
      el.classList.toggle("faol", el.dataset.maydon === nomi);
    });
  }

  function joriyInput() {
    // Raqamlar klaviaturasi faol maydonga yozadi: miqdor yoki pastdagi «Jami».
    var quti = document.querySelector("[data-maydon].faol");
    var kirish = quti && quti.querySelector("input");
    return kirish || miqdorEl;
  }

  /* Numpad maydonga yozgach `input` hodisasini chiqaradi — pul maydoni
     o'zi guruhlanadi, «Qarzga» tugmasi ham yangi «Jami» ni ko'radi. */
  function yozildi(el) {
    el.dispatchEvent(new Event("input", { bubbles: true }));
    holatYangila();
  }

  function raqamBos(belgi) {
    var el = joriyInput();
    var q = el.value === "0" ? "" : el.value;
    var kasrli = belgi === "." || belgi === ",";
    if (kasrli && /[.,]/.test(q)) return;
    if (kasrli && q === "") q = "0";
    el.value = q + belgi;
    yozildi(el);
  }

  function tozalaHammasi() {
    mahsulotId.value = "";
    miqdorEl.value = "";
    qidiruvTozala();
    if (kodEl) kodEl.value = "";
    if (kodiEl) kodiEl.textContent = "";
    tanlanganEl.className = "tanlangan-tovar";
    tanlanganEl.querySelector(".nom").textContent = "Tovar tanlanmagan";
    tanlanganEl.querySelector(".nom").classList.add("bosh-yozuv");
    document.getElementById("tovar-qoldiq").innerHTML = "&mdash;";
    document.getElementById("miqdor-birlik").innerHTML = "&mdash;";
    faolQoy("miqdor");
    holatYangila();
  }

  /* `miqdor` faqat kodning o'zi miqdorni aytganda beriladi: tarozi
     etiketkasidagi og'irlik. Qolgan hollarda bo'sh qoladi — kassir o'zi
     yozadi. */
  function tovarTanla(karta, miqdor) {
    mahsulotId.value = karta.dataset.id;
    // Rang cheki faqat o'zi skanerlanganda bog'lanadi (rangChekQoy) — ro'yxatdan
    // tanlangan tovarga oldingi chek yopishib qolmasin
    miqdorEl.value = miqdor || "";
    if (kodEl) kodEl.value = "";
    if (kodiEl) kodiEl.textContent = karta.dataset.qisqa || "";

    tanlanganEl.className = "tanlangan-tovar tanlangan";
    var nom = tanlanganEl.querySelector(".nom");
    nom.textContent = karta.dataset.nom;
    nom.classList.remove("bosh-yozuv");
    nom.title = karta.dataset.nom;
    // Ikki birlikli tovarda ikkinchi birlik ham ko'rinadi (200 metr = 2 rulon).
    document.getElementById("tovar-qoldiq").textContent =
      "Omborda: " + karta.dataset.qoldiq + " " + karta.dataset.birlik +
      (karta.dataset.ikkinchi ? " · " + karta.dataset.ikkinchi : "") +
      // Dollarda kelgan tovar — summasi pastdagi dollar maydoniga yoziladi
      (karta.dataset.valyuta === "$" ? " · dollarda" : "");
    document.getElementById("miqdor-birlik").textContent = karta.dataset.birlik;

    oynaYop();
    qidiruvTozala();
    faolQoy("miqdor");
    holatYangila();
    if (!sensorMi()) miqdorEl.focus();
  }

  // ---------- Tovar tanlash oynasi ----------
  function oynaOch() {
    oyna.classList.add("ochiq");
    qidiruvTozala();
  }

  function oynaYop() {
    oyna.classList.remove("ochiq");
    dropdownYop();
  }

  // ---------- Qidiruv dropdowni ----------
  // Pastdagi kartalar hech qachon yashirilmaydi; natijalar maydon ostida chiqadi.
  var dropdown, nishonda = -1;

  function himoya(matn) {
    return matn.replace(/[&<>"]/g, function (b) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[b];
    });
  }

  function belgila(nom, soz) {
    var joy = nom.toLowerCase().indexOf(soz);
    if (joy === -1) return himoya(nom);
    return himoya(nom.slice(0, joy)) + "<mark>" + himoya(nom.slice(joy, joy + soz.length)) +
           "</mark>" + himoya(nom.slice(joy + soz.length));
  }

  function dropdownYop() {
    dropdown.classList.remove("ochiq");
    dropdown.innerHTML = "";
    qidiruv.setAttribute("aria-expanded", "false");
    nishonda = -1;
  }

  // Yo'lda qolgan so'rov ham bekor bo'ladi — ro'yxat keyin o'zi ochilib qolmasin
  function qidiruvTozala() {
    qidiruv.value = "";
    window.TovarOyna.izla("", dropdownYop);
  }

  // Ro'yxat panelga sig'maydi va panel ortiqchasini kesadi, shuning uchun
  // `position: fixed` — maydon ostida, panelning o'ng chetiga tekislanadi.
  function dropdownJoyla() {
    var r = qidiruv.getBoundingClientRect();
    dropdown.style.top = (r.bottom + 5) + "px";
    dropdown.style.right = (document.documentElement.clientWidth - r.right) + "px";
  }

  /* Qidiruv butun ombordan — serverda (static/js/tovar_oyna.js): oynaga faqat
     eng ko'p sotiladigan tovarlar chizilgan. Raqam yozilsa kod bo'yicha ham. */
  function dropdownYangila() {
    var soz = qidiruv.value.toLowerCase().trim();
    window.TovarOyna.izla(soz, function (tovarlar, yana) {
      if (!tovarlar || !qidiruv.value.trim()) return dropdownYop();
      if (!tovarlar.length) {
        dropdown.innerHTML = '<div class="dropdown-bosh">Bunday tovar topilmadi</div>';
      } else {
        dropdown.innerHTML = tovarlar.map(function (d) {
          // Kod chapda, ustun bo'lib turadi — raqam bilan izlanganda nega
          // topilgani ham ko'rinadi (mos kelgan raqamlar belgilanadi).
          return '<button type="button" class="dropdown-qator' + (d.yoq ? " yoq" : "") +
            '" role="option" data-id="' + d.id + '">' +
            '<span class="d-kod">' + belgila(d.qisqa || "", soz) + "</span>" +
            '<span class="d-nom">' + belgila(d.nom, soz) + "</span>" +
            '<span class="d-qoldiq">' +
            (d.yoq ? "tugagan" : himoya(d.qoldiq + " " + d.birlik +
              (d.ikkinchi ? " · " + d.ikkinchi : ""))) + "</span></button>";
        }).join("") + (yana ? '<div class="dropdown-bosh">Yana bor — aniqroq yozing</div>' : "");
      }
      dropdownJoyla();
      dropdown.classList.add("ochiq");
      qidiruv.setAttribute("aria-expanded", "true");
      nishonda = -1;
    });
  }

  function qatorlar() {
    return dropdown.querySelectorAll(".dropdown-qator:not(.yoq)");
  }

  function nishonQoy(yangi) {
    var r = qatorlar();
    if (!r.length) return;
    r.forEach(function (el) { el.classList.remove("nishonda"); });
    nishonda = (yangi + r.length) % r.length;
    r[nishonda].classList.add("nishonda");
    r[nishonda].scrollIntoView({ block: "nearest" });
  }

  function dropdowndanTanla(id) {
    var karta = window.TovarOyna.karta(id);
    if (karta && !karta.classList.contains("yoq")) {
      dropdownYop();
      tovarTanla(karta);
    }
  }

  // ---------- Yakunlashdan oldin ----------
  /* Server ham tekshiradi, lekin kassir xato uchun sahifa yangilanishini
     kutmasin — yozgan narsalari (qarz tanlovi ham) o'chib ketmasin.
     Bo'sh hujjat tekshirilmaydi: uni server o'zi o'chiradi. */
  function yakunTekshir(e) {
    if (!document.querySelector(".chek-royxat tbody tr")) return;
    var som = son(document.getElementById("jami").value);
    var dollar = son(document.getElementById("jami-dollar").value);
    var xato = "", maydon = "";
    if (som <= 0 && dollar <= 0) {
      xato = "Jami summasini yozing — so'mda yoki dollarda.";
      maydon = "jami";
    } else if (dollar > 0 && son(document.getElementById("kurs").value) <= 0) {
      xato = "Dollar summasi yozildi — o'sha kungi kursni ham yozing.";
      maydon = "kurs";
    }
    if (!xato) return;
    e.preventDefault();
    window.xabarBer(xato, "error");
    faolQoy(maydon);
    if (!sensorMi()) document.getElementById(maydon).focus();
  }

  // ---------- Kod, shtrix va tarozi etiketkasi ----------
  /* Server tovarni topib berdi — kartasini olib tanlaymiz (oynada chizilmagan
     bo'lsa server javobidan yasaladi). Yashirilgan (faol emas) tovar
     tanlanmaydi.

     Skanerlangan tovar darrov chekka tushadi (skanerdanQosh). «Kod»
     maydoniga qo'lda urilgani esa faqat tanlanadi — miqdorni kassir yozadi. */
  function kodTopildi(javob, skanerdan) {
    if (!javob.faol) {
      return window.xabarBer(javob.nom + " ombordan yashirilgan — avval faollashtiring.",
                             "error");
    }
    var karta = window.TovarOyna.koddanKarta(javob);
    if (karta.classList.contains("yoq")) {
      return window.xabarBer(javob.nom + " omborda tugagan.", "error");
    }
    if (skanerdan) return skanerdanQosh(karta, javob);

    tovarTanla(karta, javob.miqdor);
    if (javob.miqdor) {
      // Miqdorni kod o'zi aytdi (tarozi yoki quti) — kassir ko'rib tursin.
      window.xabarBer(javob.nom + ": " + javob.miqdor_matni + " " + javob.birlik);
    }
  }

  /* Skanerlangan tovar Qo'shish bosilmasdan chekka qo'shiladi. Miqdor:
       1) kodning o'zi aytgani — tarozi etiketkasidagi og'irlik;
       2) tovar tanlanmasdan oldin «Miqdor» ga yozilgan son — 20 yozib sement
          qopini skanerlasa 20 qop tushadi;
       3) bo'lmasa 1.
     Bir xil tovar qayta skanerlansa server yangi qator ochmaydi, mavjudining
     miqdorini oshiradi (ombor/xizmat.py, hujjatga_qosh). */
  function skanerdanQosh(karta, javob) {
    if (forma.hasAttribute("data-yuborildi")) {
      // Oldingi tovar hali yozilyapti (sahifa yangilanmoqda) — bu skaner yo'qolmasin
      return window.xabarBer("Oldingi tovar qo'shilyapti — " + javob.nom +
                             " ni qayta skanerlang.", "warning");
    }
    var oldindan = !mahsulotId.value && son(miqdorEl.value) > 0 ? miqdorEl.value : "";
    tovarTanla(karta, javob.miqdor || oldindan || "1");
    forma.requestSubmit(qoshTugma);
  }

  /* Rang (kolerovka) cheki: baza bo'yoq chekdagi miqdori bilan keladi, chek
     raqami forma bilan ketadi — server uni shu hujjatga bog'laydi va ikkinchi
     marta qabul qilmaydi (rang/kassa.py). */

  function kodniUlash() {
    var panel = document.querySelector(".ong-panel");
    kodEl = document.getElementById("kod-kirish");
    kodiEl = document.getElementById("tovar-kodi");
    if (!panel || !kodEl || !window.Skaner) return;

    kodSora = window.Skaner.ulash({
      manzil: panel.dataset.kodManzil,
      topilganda: kodTopildi,
    });

    function izla() {
      var kod = kodEl.value.trim();
      if (kod) kodSora(kod);
    }

    document.getElementById("kod-topish").addEventListener("click", izla);
    kodEl.addEventListener("focus", function () { faolQoy("kod"); });
    kodEl.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      // Enter bu yerda qator qo'shmaydi, tovar izlaydi.
      e.preventDefault();
      e.stopPropagation();
      izla();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    forma = document.getElementById("qator-forma");
    if (!forma) return;

    oyna = document.getElementById("tovar-oyna");
    qidiruv = document.getElementById("tovar-qidiruv");
    miqdorEl = document.getElementById("miqdor");
    mahsulotId = document.getElementById("mahsulot-id");
    tanlanganEl = document.getElementById("tanlangan");
    qoshTugma = document.getElementById("qosh-tugma");

    document.getElementById("yangi-tovar").addEventListener("click", oynaOch);
    document.getElementById("tozala-tugma").addEventListener("click", tozalaHammasi);

    dropdown = document.getElementById("tovar-dropdown");
    kodniUlash();

    oyna.addEventListener("click", function (e) {
      if (e.target === oyna || e.target.closest("[data-yop]")) return oynaYop();

      var karta = e.target.closest(".tovar-karta");
      if (karta && !karta.classList.contains("yoq")) tovarTanla(karta);
    });

    dropdown.addEventListener("click", function (e) {
      var qator = e.target.closest(".dropdown-qator");
      if (qator && !qator.classList.contains("yoq")) dropdowndanTanla(qator.dataset.id);
    });
    // Ro'yxatdan tashqariga bosilsa yopiladi; numpad qidiruvga yozayotgan bo'lishi mumkin
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".qidiruv-quti, #raqamlar")) dropdownYop();
    });
    window.addEventListener("resize", dropdownYop);

    qidiruv.addEventListener("focus", function () { faolQoy("qidiruv"); });
    qidiruv.addEventListener("input", dropdownYangila);
    qidiruv.addEventListener("keydown", function (e) {
      if (!dropdown.classList.contains("ochiq")) return;
      if (e.key === "ArrowDown") { e.preventDefault(); nishonQoy(nishonda + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); nishonQoy(nishonda - 1); }
      else if (e.key === "Enter") {
        e.preventDefault();
        var r = qatorlar();
        var tanlov = nishonda >= 0 ? r[nishonda] : r[0];
        if (tanlov) dropdowndanTanla(tanlov.dataset.id);
      } else if (e.key === "Escape") {
        e.stopPropagation();
        dropdownYop();
      }
    });

    // Maydonni bosish uni faol qiladi (numpad shunga yozadi)
    document.querySelectorAll("[data-maydon]").forEach(function (el) {
      el.addEventListener("click", function () {
        faolQoy(el.dataset.maydon);
        if (!sensorMi()) {
          var kirish = el.querySelector("input");
          if (kirish) kirish.focus();
        }
      });
    });

    document.getElementById("raqamlar").addEventListener("click", function (e) {
      var t = e.target.closest("button");
      if (!t) return;
      if (t.dataset.raqam) raqamBos(t.dataset.raqam);
      else if (t.dataset.amal === "ochir") {
        var el = joriyInput();
        el.value = el.value.replace(/\s+$/, "").slice(0, -1);
        yozildi(el);
      }
    });

    miqdorEl.addEventListener("input", holatYangila);
    miqdorEl.addEventListener("focus", function () { faolQoy("miqdor"); });

    // Pastdagi summa maydonlari ham numpadga ulanadi (sensorli rejim uchun)
    document.querySelectorAll(".tolov-panel [data-maydon] input").forEach(function (el) {
      var quti = el.closest("[data-maydon]");
      el.addEventListener("focus", function () { faolQoy(quti.dataset.maydon); });
    });

    // Klaviatura yorliqlari (sichqoncha rejimi uchun)
    document.addEventListener("keydown", function (e) {
      if (document.querySelector('#miqdor-dialog[open]')) return;
      if (e.key === "Escape") return oynaYop();
      if (e.key === "F2") { e.preventDefault(); return oynaOch(); }
      if (oyna.classList.contains("ochiq")) return;
      if (e.key === "Enter" && document.activeElement.tagName !== "BUTTON") {
        // «Jami» maydonida Enter o'sha formani yuboradi — aralashmaymiz.
        if (document.activeElement.closest("form") !== forma) return;
        e.preventDefault();
        // requestSubmit — `submit` hodisasi chiqadi, ya'ni forma.js dagi
        // «bir marta» qoidasi ishlaydi: Enter ikki bosilsa tovar ikki marta tushmaydi
        if (!qoshTugma.disabled) forma.requestSubmit(qoshTugma);
      }
    });

    var jamiForma = document.getElementById("jami-forma");
    if (jamiForma) jamiForma.addEventListener("submit", yakunTekshir);

    tozalaHammasi();
    // Hozirgina qo'shilgan qator ko'rinsin — uzun chekda u pastda qolib ketadi
    var yangi = document.querySelector(".chek-royxat tr.yangi");
    if (yangi) yangi.scrollIntoView({ block: "nearest" });
    // Sichqoncha rejimida kursor darrov «Kod» da turadi: keyingi tovarning
    // raqami urilib, Enter bilan qo'shilaveradi (sahifa har qo'shishda yangilanadi)
    if (!sensorMi() && kodEl) kodEl.focus();
  });
})();
