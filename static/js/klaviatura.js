/* Ekran klaviaturasi — sensorli rejimda matn maydonlari uchun.
   Windows klaviaturasi emas, saytning o'ziniki.
   Raqamli maydonlar bu yerga tegmaydi: ular uchun numpad bor (rejim.js). */
(function () {
  "use strict";

  var HARFLAR = [
    ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
    ["a", "s", "d", "f", "g", "h", "j", "k", "l", "'"],
    ["z", "x", "c", "v", "b", "n", "m"],
  ];

  var BELGILAR = [
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
    ["-", "/", ":", ";", "(", ")", "+", "&", "@", "\""],
    [".", ",", "?", "!", "%", "№", "="],
  ];

  var panel, joriyMaydon = null, shift = false, rejim = "harf";

  function sensorMi() {
    return document.body.classList.contains("rejim-sensor");
  }

  function matnMaydonmi(el) {
    if (!el || el.disabled || el.readOnly) return false;
    if (el.tagName === "TEXTAREA") return true;
    if (el.tagName !== "INPUT") return false;
    var tur = (el.getAttribute("type") || "text").toLowerCase();
    if (["text", "search", "email", "url"].indexOf(tur) === -1) return false;
    // Raqamli maydonlar numpad bilan to'ldiriladi
    return !el.classList.contains("raqam-maydon");
  }

  function tugma(belgi, klass, yorliq) {
    return '<button type="button" class="kb-tugma' + (klass ? " " + klass : "") +
      '" data-belgi="' + belgi.replace(/"/g, "&quot;") + '">' +
      (yorliq || belgi) + "</button>";
  }

  function chiz() {
    var qatorlar = rejim === "harf" ? HARFLAR : BELGILAR;
    var html = '<div class="kb-bosh">' +
      '<span class="kb-nomi">Yozing</span>' +
      '<button type="button" class="tugma tinch kichik" data-amal="yop">' +
      "Klaviaturani yopish</button></div>";

    html += '<div class="kb-qator">' + qatorlar[0].map(function (b) {
      return tugma(shift ? b.toUpperCase() : b);
    }).join("") + "</div>";

    html += '<div class="kb-qator">' + qatorlar[1].map(function (b) {
      return tugma(shift && rejim === "harf" ? b.toUpperCase() : b);
    }).join("") + "</div>";

    html += '<div class="kb-qator">' +
      '<button type="button" class="kb-tugma kb-amal' + (shift ? " yoqiq" : "") +
      '" data-amal="shift">&#8679;</button>' +
      qatorlar[2].map(function (b) {
        return tugma(shift && rejim === "harf" ? b.toUpperCase() : b);
      }).join("") +
      '<button type="button" class="kb-tugma kb-amal" data-amal="ochir">&#9003;</button></div>';

    html += '<div class="kb-qator">' +
      '<button type="button" class="kb-tugma kb-amal" data-amal="rejim">' +
      (rejim === "harf" ? "123" : "ABC") + "</button>" +
      tugma("'", "kb-apostrof", "&#39;") +
      '<button type="button" class="kb-tugma kb-bosh-joy" data-belgi=" ">bo\'sh joy</button>' +
      '<button type="button" class="kb-tugma kb-tayyor" data-amal="tayyor">Tayyor</button></div>';

    panel.innerHTML = html;
    var nomi = maydonNomi();
    panel.querySelector(".kb-nomi").textContent = nomi;
  }

  function maydonNomi() {
    if (!joriyMaydon) return "Yozing";
    var idish = joriyMaydon.closest(".maydon");
    var yorliq = idish ? idish.querySelector("label") : null;
    if (yorliq) return yorliq.textContent.trim();
    return joriyMaydon.getAttribute("placeholder") || "Yozing";
  }

  function yarat() {
    panel = document.createElement("div");
    panel.className = "kb-panel";
    panel.id = "ekran-klaviaturasi";
    document.body.appendChild(panel);

    // Tugma bosilganda maydon fokusni yo'qotmasligi kerak
    panel.addEventListener("mousedown", function (e) { e.preventDefault(); });
    panel.addEventListener("click", function (e) {
      // Panel qayta chizilgach e.target DOM dan chiqib ketishi mumkin,
      // shuning uchun hodisani shu yerda to'xtatamiz
      e.stopPropagation();
      var t = e.target.closest("button");
      if (!t) return;

      if (t.dataset.belgi !== undefined) {
        belgiQoy(t.dataset.belgi);
        if (shift && rejim === "harf") { shift = false; chiz(); }
        return;
      }
      var amal = t.dataset.amal;
      if (amal === "shift") { shift = !shift; chiz(); }
      else if (amal === "rejim") { rejim = rejim === "harf" ? "belgi" : "harf"; shift = false; chiz(); }
      else if (amal === "ochir") ochir();
      else if (amal === "tayyor" || amal === "yop") yop();
    });
    return panel;
  }

  function belgiQoy(belgi) {
    var el = joriyMaydon;
    if (!el) return;
    var bosh = el.selectionStart, oxir = el.selectionEnd;
    if (bosh === null || bosh === undefined) {
      el.value += belgi;
    } else {
      el.value = el.value.slice(0, bosh) + belgi + el.value.slice(oxir);
      el.selectionStart = el.selectionEnd = bosh + belgi.length;
    }
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function ochir() {
    var el = joriyMaydon;
    if (!el) return;
    var bosh = el.selectionStart, oxir = el.selectionEnd;
    if (bosh === null || bosh === undefined) {
      el.value = el.value.slice(0, -1);
    } else if (bosh !== oxir) {
      el.value = el.value.slice(0, bosh) + el.value.slice(oxir);
      el.selectionStart = el.selectionEnd = bosh;
    } else if (bosh > 0) {
      el.value = el.value.slice(0, bosh - 1) + el.value.slice(bosh);
      el.selectionStart = el.selectionEnd = bosh - 1;
    }
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function och(maydon) {
    if (!panel) yarat();
    joriyMaydon = maydon;
    shift = false;
    rejim = "harf";
    chiz();
    document.body.classList.add("kb-ochiq");
    panel.classList.add("ochiq");
    // Maydon klaviatura ostida qolib ketmasin
    setTimeout(function () {
      var r = maydon.getBoundingClientRect();
      if (r.bottom > window.innerHeight - panel.offsetHeight) {
        maydon.scrollIntoView({ block: "center", behavior: "smooth" });
      }
    }, 60);
  }

  function yop() {
    if (panel) panel.classList.remove("ochiq");
    document.body.classList.remove("kb-ochiq");
    joriyMaydon = null;
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.addEventListener("focusin", function (e) {
      if (!sensorMi()) return;
      if (e.target.closest && e.target.closest(".kb-panel")) return;
      if (matnMaydonmi(e.target)) och(e.target);
      else if (joriyMaydon && e.target !== joriyMaydon) yop();
    });

    // Bosish orqali ham ochamiz: ba'zi holatlarda (modal oyna ichida)
    // focusin hodisasi klaviaturani ochib ulgurmaydi
    document.addEventListener("click", function (e) {
      if (!sensorMi()) return;
      if (e.target.closest(".kb-panel")) return;

      // Bosilgan element yoki hozir fokusda turgan maydon — qaysi biri matn maydoni bo'lsa
      var maydon = matnMaydonmi(e.target) ? e.target
                 : (matnMaydonmi(document.activeElement) ? document.activeElement : null);
      if (maydon) {
        if (maydon !== joriyMaydon) och(maydon);
        return;
      }
      if (joriyMaydon) yop();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") yop();
    });

    // Sensor rejimi o'chirilsa klaviatura ham yopiladi
    document.addEventListener("rejim-ozgardi", function (e) {
      if (e.detail.rejim !== "sensor") yop();
    });
  });
})();
