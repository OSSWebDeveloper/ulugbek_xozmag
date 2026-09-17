/* Sensor / sichqoncha rejimi richagi + raqamli maydonlar uchun qalqib chiquvchi numpad. */
(function () {
  "use strict";

  var KALIT = "ux_rejim";

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
      richag.setAttribute("aria-pressed", rejim === "sensor" ? "true" : "false");
      var holat = richag.querySelector(".holat");
      if (holat) holat.textContent = rejim === "sensor" ? "Sensor" : "Sichqoncha";
    }
    try {
      localStorage.setItem(KALIT, rejim);
    } catch (e) { /* localStorage yopiq bo'lsa ham ishlayversin */ }
    document.dispatchEvent(new CustomEvent("rejim-ozgardi", { detail: { rejim: rejim } }));
  }

  function sensorMi() {
    return document.body.classList.contains("rejim-sensor");
  }

  // ---------- Qalqib chiquvchi numpad ----------
  var joriyMaydon = null;
  var qalqigich = null;

  function qalqigichYarat() {
    var fon = document.createElement("div");
    fon.className = "oyna-fon";
    fon.id = "numpad-oyna";
    fon.innerHTML =
      '<div class="oyna" style="max-width:420px">' +
      '  <div class="oyna-bosh"><span class="numpad-nomi">Raqam kiriting</span>' +
      '    <button type="button" class="tugma qizil kichik" data-yop>X</button></div>' +
      '  <div class="oyna-tana">' +
      '    <div class="kiritish-maydon faol"><span class="qiymat numpad-ekran">0</span></div>' +
      '    <div class="raqamlar">' +
      '      <button type="button" class="tugma" data-raqam="7">7</button>' +
      '      <button type="button" class="tugma" data-raqam="8">8</button>' +
      '      <button type="button" class="tugma" data-raqam="9">9</button>' +
      '      <button type="button" class="tugma" data-raqam="4">4</button>' +
      '      <button type="button" class="tugma" data-raqam="5">5</button>' +
      '      <button type="button" class="tugma" data-raqam="6">6</button>' +
      '      <button type="button" class="tugma" data-raqam="1">1</button>' +
      '      <button type="button" class="tugma" data-raqam="2">2</button>' +
      '      <button type="button" class="tugma" data-raqam="3">3</button>' +
      '      <button type="button" class="tugma" data-raqam="0">0</button>' +
      '      <button type="button" class="tugma amal" data-raqam=".">,</button>' +
      '      <button type="button" class="tugma amal" data-amal="ochir">&#9003;</button>' +
      '    </div>' +
      '    <div class="qator tor" style="gap:6px">' +
      '      <button type="button" class="tugma qizil" style="flex:1" data-amal="tozala">Tozalash</button>' +
      '      <button type="button" class="tugma yashil" style="flex:2" data-amal="tayyor">Tayyor</button>' +
      '    </div>' +
      '  </div>' +
      '</div>';
    document.body.appendChild(fon);

    fon.addEventListener("click", function (e) {
      if (e.target === fon || e.target.hasAttribute("data-yop")) return numpadYop();
      var t = e.target.closest("button");
      if (!t) return;
      var ekran = fon.querySelector(".numpad-ekran");
      if (t.dataset.raqam) {
        var q = ekran.textContent === "0" && t.dataset.raqam !== "." ? "" : ekran.textContent;
        if (t.dataset.raqam === "." && q.indexOf(".") !== -1) return;
        ekran.textContent = q + t.dataset.raqam;
      } else if (t.dataset.amal === "ochir") {
        ekran.textContent = ekran.textContent.slice(0, -1) || "0";
      } else if (t.dataset.amal === "tozala") {
        ekran.textContent = "0";
      } else if (t.dataset.amal === "tayyor") {
        if (joriyMaydon) {
          joriyMaydon.value = ekran.textContent;
          joriyMaydon.dispatchEvent(new Event("input", { bubbles: true }));
        }
        numpadYop();
      }
    });
    return fon;
  }

  function numpadOch(maydon) {
    if (!qalqigich) qalqigich = qalqigichYarat();
    joriyMaydon = maydon;
    var yorliq = maydon.closest(".maydon") ? maydon.closest(".maydon").querySelector("label") : null;
    qalqigich.querySelector(".numpad-nomi").textContent =
      yorliq ? yorliq.textContent.trim() : "Raqam kiriting";
    qalqigich.querySelector(".numpad-ekran").textContent = maydon.value || "0";
    qalqigich.classList.add("ochiq");
  }

  function numpadYop() {
    if (qalqigich) qalqigich.classList.remove("ochiq");
    joriyMaydon = null;
  }

  // ---------- Ishga tushirish ----------
  document.addEventListener("DOMContentLoaded", function () {
    rejimniQoy(rejimniOqi());

    var richag = document.getElementById("richag");
    if (richag) {
      richag.addEventListener("click", function () {
        rejimniQoy(sensorMi() ? "sichqoncha" : "sensor");
      });
    }

    // Sensor rejimida raqamli maydon bosilganda numpad chiqadi
    document.addEventListener("focusin", function (e) {
      var m = e.target;
      if (!sensorMi()) return;
      if (m.classList && m.classList.contains("raqam-maydon") && !m.dataset.numpadsiz) {
        m.blur();
        numpadOch(m);
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") numpadYop();
    });
  });
})();
