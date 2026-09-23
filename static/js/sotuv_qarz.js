/* Naqd sotuvda pul yetmay qolganda — «qolgani qarzga» oynachasi.

   Kassir sahifani tashlab ketolmaydi: mijoz qarshisida turibdi, chek ochiq.
   Shuning uchun qarzdorni tanlash ham, yangisini yaratish ham shu oynachada
   bo'ladi.

   «Jami» o'zi ikkiga bo'linadi (autosplit): «To'ladi» ga mijoz bergan pul
   yozilsa «Qarzga» = Jami − To'ladi, «Qarzga» yozilsa aksincha. So'm va
   dollar alohida bo'linadi, bir-biriga aralashmaydi.

   Tasdiqlanganda **to'langan pul** pastdagi «Jami» formasining yashirin
   maydonlariga tushadi. Qarz saqlanmaydi — u har doim Jami − To'ladi, ya'ni
   kassir «Jami» ni keyin o'zgartirsa qarz ham o'zi o'zgaradi. Yakunlash
   baribir bitta oddiy POST bo'lib qoladi, hisobni server qayta tekshiradi.

   Sensorli rejimda oynachaning o'z raqamlar klaviaturasi bor — CSS uni
   sichqoncha rejimida yashiradi (.raqamlar qoidasi). */
(function () {
  "use strict";

  var VALYUTALAR = [
    { kalit: "som", jami: "jami", yashirin: "qarz-tolandi", belgi: "so'm", kasr: 0 },
    { kalit: "dollar", jami: "jami-dollar", yashirin: "qarz-tolandi-dollar", belgi: "$", kasr: 2 },
  ];

  var oyna, tugma, yozuv, izoh, xulosa, tasdiq, setka, qidiruv, boshHolat, xatoEl;
  var yashirinQarzdor, tanlangan = null;
  var son, matn;

  function sensorMi() {
    return document.body.classList.contains("rejim-sensor");
  }

  function yaxlitla(q, kasr) {
    var k = Math.pow(10, kasr);
    return Math.round(q * k) / k;
  }

  /* Kiritish maydoniga son yozadi — guruhlab (200 000). */
  function maydongaYoz(el, q) {
    el.value = q ? String(q) : "0";
    window.Pul.tartibla(el);
  }

  // ---------- Bo'linish (autosplit) ----------
  function qism(v) {
    return oyna.querySelector('.bolinish[data-valyuta="' + v.kalit + '"]');
  }

  function jamisi(v) {
    return yaxlitla(son(document.getElementById(v.jami).value), v.kasr);
  }

  /* Bitta valyuta bo'yicha holat: {jami, tolandi, qarz, xato}. */
  function holati(v) {
    var blok = qism(v);
    var jami = jamisi(v);
    var tolandi = yaxlitla(son(blok.querySelector("[data-tolandi]").value), v.kasr);
    var qarz = yaxlitla(son(blok.querySelector("[data-qarz]").value), v.kasr);
    var xato = "";
    if (tolandi > jami) xato = "To'langan pul jamidan ko'p: " + matn(tolandi) + " > " + matn(jami) + " " + v.belgi;
    else if (qarz > jami) xato = "Qarz jamidan ko'p: " + matn(qarz) + " > " + matn(jami) + " " + v.belgi;
    return { jami: jami, tolandi: tolandi, qarz: blok.hidden ? 0 : qarz, xato: blok.hidden ? "" : xato };
  }

  /* Bittasi yozilsa ikkinchisi o'zi hisoblanadi. */
  function bol(kirish) {
    var blok = kirish.closest(".bolinish");
    var v = VALYUTALAR.filter(function (x) { return x.kalit === blok.dataset.valyuta; })[0];
    var jami = jamisi(v);
    var yozilgan = yaxlitla(son(kirish.value), v.kasr);
    var juft = blok.querySelector(kirish.hasAttribute("data-tolandi") ? "[data-qarz]" : "[data-tolandi]");
    maydongaYoz(juft, yaxlitla(Math.max(0, jami - yozilgan), v.kasr));
    holatYangila();
  }

  // ---------- Faol maydon (raqamlar klaviaturasi shunga yozadi) ----------
  function faolQoy(quti) {
    oyna.querySelectorAll("[data-qmaydon]").forEach(function (el) {
      el.classList.toggle("faol", el === quti);
    });
  }

  function joriyInput() {
    var quti = oyna.querySelector("[data-qmaydon].faol");
    return quti && quti.querySelector("input");
  }

  // ---------- Holat ----------
  function qarzMatni(holatlar) {
    var bolaklar = [];
    VALYUTALAR.forEach(function (v, i) {
      if (holatlar[i].qarz > 0) bolaklar.push(matn(holatlar[i].qarz) + " " + v.belgi);
    });
    return bolaklar.join(" + ");
  }

  function holatYangila() {
    var holatlar = VALYUTALAR.map(holati);
    var xato = holatlar.map(function (h) { return h.xato; }).filter(Boolean)[0] || "";
    var qarzBor = holatlar.some(function (h) { return h.qarz > 0; });

    xatoEl.textContent = xato;
    xatoEl.hidden = !xato;
    VALYUTALAR.forEach(function (v, i) {
      qism(v).classList.toggle("xato", !!holatlar[i].xato);
    });

    tasdiq.disabled = !(tanlangan && qarzBor && !xato);
    if (!tanlangan) {
      xulosa.textContent = "Qarzdor tanlanmagan";
    } else if (xato) {
      xulosa.textContent = tanlangan.dataset.nom + " — summani tekshiring";
    } else if (!qarzBor) {
      xulosa.textContent = tanlangan.dataset.nom + " — hammasi to'langan, qarz qolmadi";
    } else {
      xulosa.textContent = tanlangan.dataset.nom + " — qarzga " + qarzMatni(holatlar);
    }
  }

  function kartaTanla(karta) {
    tanlangan = karta;
    setka.querySelectorAll(".qarzdor-karta").forEach(function (el) {
      el.classList.toggle("tanlangan", el === karta);
    });
    holatYangila();
  }

  /* Pastdagi tugma tanlovni ko'rsatib turadi — kassir yakunlashdan oldin
     nima bo'layotganini ko'rib turishi kerak: tepada kichik «Qarzga ·
     Aliyev Vali», ostida summa. «Jami» o'zgarsa ham darrov yangilanadi:
     qarz = Jami − To'ladi. */
  function tugmaYangila() {
    var bor = !!yashirinQarzdor.value;
    tugma.classList.toggle("tanlangan", bor);
    tugma.classList.remove("xato-holat");
    izoh.hidden = !bor;
    if (!tugma.dataset.izoh) tugma.dataset.izoh = tugma.title;
    if (!bor) {
      yozuv.textContent = "Qarzga";
      tugma.title = tugma.dataset.izoh;
      return;
    }
    var qarzlar = VALYUTALAR.map(function (v) {
      return { qarz: yaxlitla(jamisi(v) - son(document.getElementById(v.yashirin).value), v.kasr) };
    });
    izoh.textContent = "Qarzga · " + (yashirinQarzdor.dataset.nom || "");
    if (qarzlar.some(function (h) { return h.qarz < 0; })) {
      // «Jami» to'langandan kam qilib qo'yilgan — server ham qabul qilmaydi
      tugma.classList.add("xato-holat");
      yozuv.textContent = "Summani tekshiring";
      return;
    }
    yozuv.textContent = qarzMatni(qarzlar) || "Qarz qolmadi";
    // Tor tugmada ism qisqarib qolishi mumkin — to'liq yozuv ustiga borganda
    tugma.title = izoh.textContent + ": " + yozuv.textContent + " (o'zgartirish uchun bosing)";
  }

  function tozala() {
    yashirinQarzdor.value = "";
    yashirinQarzdor.dataset.nom = "";
    VALYUTALAR.forEach(function (v) { document.getElementById(v.yashirin).value = ""; });
    tugmaYangila();
  }

  /* «Olib tashlash» faqat oldin biror narsa tanlangan bo'lsa ko'rinadi. */
  function olibTashlaYangila() {
    document.getElementById("qarz-olib-tashla").hidden = !yashirinQarzdor.value;
  }

  // ---------- Oynani ochish-yopish ----------
  function och() {
    var jamilar = VALYUTALAR.map(jamisi);
    if (!jamilar.some(function (q) { return q > 0; })) {
      // Bo'ladigan narsa yo'q: avval chekning to'liq summasi kerak
      window.xabarBer("Avval «Jami» ga chek summasini yozing — qarzga qoladigani " +
                      "shundan o'zi hisoblanadi.", "error");
      var jamiEl = document.getElementById("jami");
      if (!sensorMi()) jamiEl.focus();
      return;
    }

    var birinchi = null;
    VALYUTALAR.forEach(function (v, i) {
      var blok = qism(v);
      blok.hidden = jamilar[i] <= 0;
      blok.querySelector("[data-jami]").textContent = matn(jamilar[i]);
      // Oldin tasdiqlangan bo'lsa o'sha to'lov, bo'lmasa 0 — hammasi qarzga
      var tolandi = son(document.getElementById(v.yashirin).value);
      var tolandiEl = blok.querySelector("[data-tolandi]");
      tolandiEl.value = tolandi ? String(tolandi) : "";
      window.Pul.tartibla(tolandiEl);
      maydongaYoz(blok.querySelector("[data-qarz]"),
                  yaxlitla(Math.max(0, jamilar[i] - tolandi), v.kasr));
      if (!blok.hidden && !birinchi) birinchi = tolandiEl;
    });

    oyna.classList.add("ochiq");
    olibTashlaYangila();
    var bor = yashirinQarzdor.value;
    kartaTanla(bor ? setka.querySelector('.qarzdor-karta[data-id="' + bor + '"]') : null);
    faolQoy(birinchi.closest("[data-qmaydon]"));
    if (!sensorMi()) { birinchi.focus(); birinchi.select(); }
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

  function tasdiqla() {
    var holatlar = VALYUTALAR.map(holati);
    yashirinQarzdor.value = tanlangan.dataset.id;
    yashirinQarzdor.dataset.nom = tanlangan.dataset.nom;
    VALYUTALAR.forEach(function (v, i) {
      // Serverga oddiy son ketadi: «50000», «12.5»
      document.getElementById(v.yashirin).value = qism(v).hidden ? "" : String(holatlar[i].tolandi);
    });
    tugmaYangila();
    olibTashlaYangila();
    yop();
    window.xabarBer(tanlangan.dataset.nom + " ning daftariga " + qarzMatni(holatlar) +
                    " yoziladi. Endi sotuvni yakunlang.");
  }

  document.addEventListener("DOMContentLoaded", function () {
    oyna = document.getElementById("qarz-oyna");
    tugma = document.getElementById("qarzga-tugma");
    if (!oyna || !tugma) return;

    son = window.Pul.son;
    matn = window.Pul.matn;
    yozuv = document.getElementById("qarzga-yozuv");
    izoh = document.getElementById("qarzga-izoh");
    xulosa = document.getElementById("qarz-xulosa");
    tasdiq = document.getElementById("qarz-tasdiq");
    setka = document.getElementById("qarzdor-setka");
    qidiruv = document.getElementById("qarzdor-qidiruv");
    boshHolat = document.getElementById("qarzdor-bosh-holat");
    xatoEl = document.getElementById("bolinish-xato");
    yashirinQarzdor = document.getElementById("qarz-qarzdor");

    tugma.addEventListener("click", och);

    // «Jami» o'zgarsa tugmadagi qarz ham o'zgaradi — to'langan pul o'sha-o'sha
    VALYUTALAR.forEach(function (v) {
      document.getElementById(v.jami).addEventListener("input", tugmaYangila);
    });

    oyna.addEventListener("click", function (e) {
      if (e.target === oyna || e.target.closest("[data-yop]")) return yop();

      var karta = e.target.closest(".qarzdor-karta");
      if (karta) return kartaTanla(karta);

      var quti = e.target.closest("[data-qmaydon]");
      if (quti) {
        faolQoy(quti);
        if (!sensorMi()) quti.querySelector("input").focus();
      }
    });

    oyna.querySelectorAll(".bolinish input").forEach(function (el) {
      el.addEventListener("input", function () { bol(el); });
      el.addEventListener("focus", function () { faolQoy(el.closest("[data-qmaydon]")); });
    });

    // Oynachaning o'z raqamlar klaviaturasi (sensorli rejim)
    document.getElementById("qarz-raqamlar").addEventListener("click", function (e) {
      var t = e.target.closest("button");
      var el = joriyInput();
      if (!t || !el) return;
      if (t.dataset.raqam) {
        var q = el.value === "0" ? "" : el.value;
        if (t.dataset.raqam === "," && /[.,]/.test(q)) return;
        el.value = q + t.dataset.raqam;
      } else if (t.dataset.amal === "ochir") {
        el.value = el.value.replace(/\s+$/, "").slice(0, -1);
      }
      el.dispatchEvent(new Event("input", { bubbles: true }));
    });

    qidiruv.addEventListener("input", qidiruvYangila);

    var yangiForma = document.getElementById("yangi-qarzdor-forma");
    document.getElementById("yangi-qarzdor-tugma").addEventListener("click", function () {
      yangiForma.hidden = !yangiForma.hidden;
      if (!yangiForma.hidden && !sensorMi()) {
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

    tasdiq.addEventListener("click", tasdiqla);

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
