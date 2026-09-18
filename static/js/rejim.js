/* Sensor / sichqoncha rejimi va kechki / kunduzgi mavzu richaglari.
   Raqamli maydonlar uchun qalqib chiquvchi numpad yo'q — raqamlar
   klaviaturasi maydon yonida, sahifaning o'zida turadi (kassa va kirim). */
(function () {
  "use strict";

  var KALIT = "ux_rejim";
  var MAVZU_KALIT = "ux_mavzu";

  function rejimniOqi() {
    try {
      return localStorage.getItem(KALIT) === "sensor" ? "sensor" : "sichqoncha";
    } catch (e) {
      return "sichqoncha";
    }
  }

  function rejimniQoy(rejim) {
    document.body.classList.toggle("rejim-sensor", rejim === "sensor");
    var richag = document.getElementById("richag");
    if (richag) {
      // Yozuv o'zgarmaydi ("Sensor"), faqat yoqiq/o'chiq holati ko'rinadi
      richag.setAttribute("aria-pressed", rejim === "sensor" ? "true" : "false");
    }
    try {
      localStorage.setItem(KALIT, rejim);
    } catch (e) { /* localStorage yopiq bo'lsa ham ishlayversin */ }
    document.dispatchEvent(new CustomEvent("rejim-ozgardi", { detail: { rejim: rejim } }));
  }

  function sensorMi() {
    return document.body.classList.contains("rejim-sensor");
  }

  // ---------- Kechki / kunduzgi ko'rinish ----------
  function mavzuniOqi() {
    try {
      return localStorage.getItem(MAVZU_KALIT) === "kunduzgi" ? "kunduzgi" : "kechki";
    } catch (e) {
      return "kechki";
    }
  }

  function mavzuniQoy(mavzu) {
    document.body.classList.toggle("kunduzgi", mavzu === "kunduzgi");
    var richag = document.getElementById("mavzu-richag");
    if (richag) richag.setAttribute("aria-pressed", mavzu === "kechki" ? "true" : "false");
    try {
      localStorage.setItem(MAVZU_KALIT, mavzu);
    } catch (e) { /* localStorage yopiq bo'lsa ham ishlayversin */ }
  }

  function kechkimi() {
    return !document.body.classList.contains("kunduzgi");
  }

  // ---------- Brauzerning o'z ogohlantirishlari ----------
  // Ular brauzer tilida chiqadi (masalan ruscha) — sayt o'zbekcha bo'lgani
  // uchun matnni o'zimiz beramiz.
  var TEKSHIRUV = [
    ["valueMissing", "Bu maydonni to'ldiring."],
    ["badInput", "Faqat son yozing."],
    ["typeMismatch", "Qiymat noto'g'ri."],
    ["rangeUnderflow", "Son juda kichik."],
    ["rangeOverflow", "Son juda katta."],
    ["stepMismatch", "Bunday son bo'lmaydi."],
    ["tooLong", "Juda uzun yozuv."],
    ["patternMismatch", "Ko'rinishi mos emas."]
  ];

  function tekshiruvniUla() {
    document.addEventListener("invalid", function (e) {
      var el = e.target;
      if (!el.validity) return;
      for (var i = 0; i < TEKSHIRUV.length; i++) {
        if (el.validity[TEKSHIRUV[i][0]]) { el.setCustomValidity(TEKSHIRUV[i][1]); return; }
      }
      el.setCustomValidity("");
    }, true);
    // Yozila boshlanishi bilan xabar tozalanadi, aks holda maydon xato bo'lib qoladi
    document.addEventListener("input", function (e) {
      if (e.target && e.target.setCustomValidity) e.target.setCustomValidity("");
    }, true);
    document.addEventListener("change", function (e) {
      if (e.target && e.target.setCustomValidity) e.target.setCustomValidity("");
    }, true);
  }

  // ---------- Ishga tushirish ----------
  document.addEventListener("DOMContentLoaded", function () {
    tekshiruvniUla();
    rejimniQoy(rejimniOqi());
    mavzuniQoy(mavzuniOqi());

    var mavzuRichag = document.getElementById("mavzu-richag");
    if (mavzuRichag) {
      mavzuRichag.addEventListener("click", function () {
        mavzuniQoy(kechkimi() ? "kunduzgi" : "kechki");
      });
    }

    var richag = document.getElementById("richag");
    if (richag) {
      richag.addEventListener("click", function () {
        rejimniQoy(sensorMi() ? "sichqoncha" : "sensor");
      });
    }
  });
})();
