/* Naqd sotuvda pul yetmay qolganda — «qolgani qarzga» oynachasi.

   Kassir sahifani tashlab ketolmaydi: mijoz qarshisida turibdi, chek ochiq.
   Shuning uchun qarzdorni tanlash ham, yangisini yaratish ham shu oynachada
   bo'ladi. Tanlov pastdagi «Jami» formasining yashirin maydonlariga tushadi,
   ya'ni yakunlash baribir bitta oddiy POST bo'lib qoladi.

   Sensorli rejimda oynachaning o'z raqamlar klaviaturasi bor — CSS uni
   sichqoncha rejimida yashiradi (.raqamlar qoidasi). */
(function () {
  "use strict";

  var oyna, tugma, yozuv, xulosa, tasdiq, setka, qidiruv, boshHolat;
  var yashirinQarzdor, yashirinJami, yashirinDollar;
  var somEl, dollarEl, tanlangan = null;

  function son(matn) {
    var q = parseFloat(String(matn || "").replace(",", ".").replace(/\s/g, ""));
    return isNaN(q) ? 0 : q;
  }

  function pulMatn(q) {
    return q.toLocaleString("ru-RU", { maximumFractionDigits: 2 }).replace(/ /g, " ");
  }

  // ---------- Faol maydon (raqamlar klaviaturasi shunga yozadi) ----------
  function faolQoy(quti) {
    document.querySelectorAll("[data-qmaydon]").forEach(function (el) {
      el.classList.toggle("faol", el === quti);
    });
  }

  function joriyInput() {
    var quti = document.querySelector("[data-qmaydon].faol");
    return (quti && quti.querySelector("input")) || somEl;
  }

  // ---------- Holat ----------
  function holatYangila() {
    var summa = son(somEl.value) + son(dollarEl.value);
    tasdiq.disabled = !(tanlangan && summa > 0);
    if (!tanlangan) {
      xulosa.textContent = "Qarzdor tanlanmagan";
      return;
    }
    var bolaklar = [];
    if (son(somEl.value) > 0) bolaklar.push(pulMatn(son(somEl.value)) + " so'm");
    if (son(dollarEl.value) > 0) bolaklar.push(pulMatn(son(dollarEl.value)) + " $");
    xulosa.textContent = tanlangan.dataset.nom +
      (bolaklar.length ? " — " + bolaklar.join(" va ") : " — summa yozilmadi");
  }

  function kartaTanla(karta) {
    tanlangan = karta;
    document.querySelectorAll(".qarzdor-karta").forEach(function (el) {
      el.classList.toggle("tanlangan", el === karta);
    });
    holatYangila();
  }

  /* Tugmadagi yozuv tanlovni ko'rsatib turadi — kassir yakunlashdan oldin
     nima bo'layotganini ko'rib turishi kerak. */
  function tugmaYangila() {
    var bor = !!yashirinQarzdor.value;
    tugma.classList.toggle("tanlangan", bor);
    if (!bor) {
      yozuv.textContent = "Qarzga";
      return;
    }
    var bolaklar = [];
    if (son(yashirinJami.value) > 0) bolaklar.push(pulMatn(son(yashirinJami.value)) + " so'm");
    if (son(yashirinDollar.value) > 0) bolaklar.push(pulMatn(son(yashirinDollar.value)) + " $");
    yozuv.textContent = "Qarzga: " + bolaklar.join(" + ");
  }

  function tozala() {
    yashirinQarzdor.value = "";
    yashirinJami.value = "";
    yashirinDollar.value = "";
    tugmaYangila();
  }

  /* «Olib tashlash» faqat oldin biror narsa tanlangan bo'lsa ko'rinadi. */
  function olibTashlaYangila() {
    var el = document.getElementById("qarz-olib-tashla");
    if (el) el.hidden = !yashirinQarzdor.value;
  }

  // ---------- Oynani ochish-yopish ----------
  function och() {
    oyna.classList.add("ochiq");
    olibTashlaYangila();
    somEl.value = yashirinJami.value;
    dollarEl.value = yashirinDollar.value;
    var bor = yashirinQarzdor.value;
    kartaTanla(bor ? setka.querySelector('.qarzdor-karta[data-id="' + bor + '"]') : null);
    faolQoy(somEl.closest("[data-qmaydon]"));
    if (!document.body.classList.contains("rejim-sensor")) somEl.focus();
  }

  function yop() {
    oyna.classList.remove("ochiq");
  }

  // ---------- Qidiruv ----------
  function qidiruvYangila() {
    var soz = qidiruv.value.toLowerCase().trim();
    var topildi = 0;
    setka.querySelectorAll(".qarzdor-karta").forEach(function (karta) {
      var mos = !soz ||
        karta.dataset.nom.toLowerCase().indexOf(soz) !== -1 ||
        karta.dataset.hudud.toLowerCase().indexOf(soz) !== -1;
      karta.hidden = !mos;
      if (mos) topildi += 1;
    });
    boshHolat.hidden = topildi > 0;
  }

  // ---------- Yangi qarzdor ----------
  function qarzdorYarat(forma) {
    var maydonlar = ["ism", "familiya", "telefon", "hudud"];
    var malumot = new FormData();
    malumot.append("csrfmiddlewaretoken",
                   forma.querySelector("[name=csrfmiddlewaretoken]").value);
    maydonlar.forEach(function (nomi) {
      malumot.append(nomi, (document.getElementById("id_" + nomi) || {}).value || "");
    });
    forma.querySelectorAll("[data-xato]").forEach(function (el) { el.hidden = true; });

    fetch(forma.dataset.manzil, { method: "POST", body: malumot, credentials: "same-origin" })
      .then(function (javob) { return javob.json(); })
      .then(function (javob) {
        if (!javob.ok) {
          Object.keys(javob.xatolar || {}).forEach(function (nomi) {
            var el = forma.querySelector('[data-xato="' + nomi + '"]');
            if (el) { el.textContent = javob.xatolar[nomi]; el.hidden = false; }
          });
          return;
        }
        // Yangi qarzdor ro'yxatga qo'shiladi va darrov tanlanadi
        var karta = document.createElement("button");
        karta.type = "button";
        karta.className = "qarzdor-karta";
        karta.dataset.id = javob.id;
        karta.dataset.nom = javob.nom;
        karta.dataset.hudud = javob.hudud;
        karta.innerHTML = '<span class="q-nom"></span><span class="q-hudud"></span>' +
                          '<span class="nishon yashil">Yangi</span>';
        karta.querySelector(".q-nom").textContent = javob.nom;
        karta.querySelector(".q-hudud").textContent = javob.hudud;
        setka.prepend(karta);

        forma.hidden = true;
        maydonlar.forEach(function (nomi) {
          var el = document.getElementById("id_" + nomi);
          if (el && nomi !== "hudud") el.value = "";
        });
        qidiruv.value = "";
        qidiruvYangila();
        kartaTanla(karta);
        window.xabarBer(javob.nom + " qo'shildi.");
      })
      .catch(function () {
        window.xabarBer("Qarzdorni qo'shib bo'lmadi. Sahifani yangilang.", "error");
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    oyna = document.getElementById("qarz-oyna");
    tugma = document.getElementById("qarzga-tugma");
    if (!oyna || !tugma) return;

    yozuv = document.getElementById("qarzga-yozuv");
    xulosa = document.getElementById("qarz-xulosa");
    tasdiq = document.getElementById("qarz-tasdiq");
    setka = document.getElementById("qarzdor-setka");
    qidiruv = document.getElementById("qarzdor-qidiruv");
    boshHolat = document.getElementById("qarzdor-bosh-holat");
    somEl = document.getElementById("qarz-jami");
    dollarEl = document.getElementById("qarz-jami-dollar");
    yashirinQarzdor = document.getElementById("qarz-qarzdor");
    yashirinJami = document.getElementById("qarz-jami-yashirin");
    yashirinDollar = document.getElementById("qarz-jami-dollar-yashirin");

    tugma.addEventListener("click", och);

    oyna.addEventListener("click", function (e) {
      if (e.target === oyna || e.target.closest("[data-yop]")) return yop();

      var karta = e.target.closest(".qarzdor-karta");
      if (karta) return kartaTanla(karta);

      var quti = e.target.closest("[data-qmaydon]");
      if (quti) {
        faolQoy(quti);
        if (!document.body.classList.contains("rejim-sensor")) quti.querySelector("input").focus();
      }
    });

    // Oynachaning o'z raqamlar klaviaturasi (sensorli rejim)
    document.getElementById("qarz-raqamlar").addEventListener("click", function (e) {
      var t = e.target.closest("button");
      if (!t) return;
      var el = joriyInput();
      if (t.dataset.raqam) {
        var q = el.value === "0" ? "" : el.value;
        if (t.dataset.raqam === "." && q.indexOf(".") !== -1) return;
        el.value = q + t.dataset.raqam;
      } else if (t.dataset.amal === "ochir") {
        el.value = el.value.slice(0, -1);
      }
      holatYangila();
    });

    [somEl, dollarEl].forEach(function (el) {
      el.addEventListener("input", holatYangila);
      el.addEventListener("focus", function () { faolQoy(el.closest("[data-qmaydon]")); });
    });

    qidiruv.addEventListener("input", qidiruvYangila);

    var yangiForma = document.getElementById("yangi-qarzdor-forma");
    document.getElementById("yangi-qarzdor-tugma").addEventListener("click", function () {
      yangiForma.hidden = !yangiForma.hidden;
      if (!yangiForma.hidden && !document.body.classList.contains("rejim-sensor")) {
        document.getElementById("id_ism").focus();
      }
    });
    document.getElementById("qarzdor-saqla").addEventListener("click", function () {
      qarzdorYarat(yangiForma);
    });

    document.getElementById("qarz-olib-tashla").addEventListener("click", function () {
      tozala();
      yop();
      window.xabarBer("Qarz olib tashlandi — chek to'liq naqd.");
    });

    tasdiq.addEventListener("click", function () {
      yashirinQarzdor.value = tanlangan.dataset.id;
      yashirinJami.value = somEl.value.replace(",", ".");
      yashirinDollar.value = dollarEl.value.replace(",", ".");
      tugmaYangila();
      olibTashlaYangila();
      yop();
      window.xabarBer(tanlangan.dataset.nom +
                      " ning qarziga yoziladi. Endi sotuvni yakunlang.");
    });

    // Oyna ochiq turganda Enter chekni yakunlab yubormasin (kassa.js dagi qoida)
    document.addEventListener("keydown", function (e) {
      if (!oyna.classList.contains("ochiq")) return;
      if (e.key === "Escape") { e.stopPropagation(); return yop(); }
      if (e.key !== "Enter") return;
      e.preventDefault();
      e.stopPropagation();
      // Yangi qarzdor formasida Enter — saqlash, boshqa joyda — tasdiqlash
      if (!yangiForma.hidden && e.target.closest(".yangi-qarzdor-forma")) {
        qarzdorYarat(yangiForma);
      } else if (!tasdiq.disabled) {
        tasdiq.click();
      }
    }, true);

    tugmaYangila();
  });

  // Chek bekor qilinsa yoki sahifa yangilansa tanlov qolmaydi — yashirin
  // maydonlar formaning o'zida, ya'ni sahifa bilan birga ketadi.
  window.addEventListener("pageshow", function () {
    if (yashirinQarzdor) tugmaYangila();
  });
})();
