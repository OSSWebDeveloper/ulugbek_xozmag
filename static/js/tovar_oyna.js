/* Tovar tanlash oynasining qidiruvi — kassa (sotuv, qarz) va rang stansiyasi uchun.

   Oynaga faqat eng ko'p sotiladigan 60 ta tovar chiziladi: omborda 10 000 dan
   ortiq tovar bor va hammasi chizilsa sahifa 10 soniyada ochilardi. Qolgani
   shu yerdan serverga so'raladi (`/ombor/tovar-qidir/`).

   Kartaning `data-*` qiymatlari serverdagi `ombor.xizmat.karta_malumoti` bilan
   bir xil — ro'yxatda chizilmagan tovar uchun ham shunday karta yasaladi va
   kassa uni oddiy kartadek tanlaydi.
*/
(function () {
  "use strict";

  var KECHIKISH = 180;   // ms — har harfda so'ramaslik uchun
  var taymer = null;
  var oxirgiSorov = 0;
  var tanish = {};       // id -> serverdan kelgan ma'lumot

  function kartaYasa(d) {
    var k = document.createElement("button");
    k.type = "button";
    k.className = "tovar-karta" + (d.yoq ? " yoq" : "");
    k.dataset.id = d.id;
    k.dataset.nom = d.nom;
    k.dataset.kod = d.kod || "";
    k.dataset.qisqa = d.qisqa || d.kod || "";
    k.dataset.qoldiq = d.qoldiq;
    k.dataset.birlik = d.birlik;
    k.dataset.ikkinchi = d.ikkinchi || "";
    k.dataset.valyuta = d.valyuta || "";
    k.dataset.narx = d.narx || "";
    return k;
  }

  /* Tovarning kartasi: oynada chizilgani bo'lsa o'sha, bo'lmasa serverdan
     kelgan ma'lumotdan yasaladi. Topilmasa null. */
  function karta(id) {
    var bor = document.querySelector('#tovar-oyna .tovar-karta[data-id="' + id + '"]');
    if (bor) return bor;
    return tanish[id] ? kartaYasa(tanish[id]) : null;
  }

  /* `/ombor/kod/` javobidan karta (skaner yoki «Kod» maydoni). */
  function koddanKarta(javob) {
    var bor = document.querySelector('#tovar-oyna .tovar-karta[data-id="' + javob.id + '"]');
    if (bor) return bor;
    return kartaYasa({
      id: javob.id, nom: javob.nom, kod: javob.kod, qisqa: javob.qisqa,
      qoldiq: javob.qoldiq, birlik: javob.birlik, ikkinchi: javob.qadoq,
      valyuta: javob.valyuta, yoq: !javob.bormi,
    });
  }

  /* Qidiruv: natija `chiz(tovarlar, yana)` ga keladi. Bo'sh so'z — darrov
     bo'sh ro'yxat. Eskirgan javoblar (yangi harf yozilgandan keyin kelgan)
     tashlab yuboriladi. */
  function izla(soz, chiz) {
    clearTimeout(taymer);
    soz = (soz || "").trim();
    var raqam = ++oxirgiSorov;
    if (!soz) return chiz(null);
    var oyna = document.getElementById("tovar-oyna");
    var manzil = oyna && oyna.dataset.qidirManzil;
    if (!manzil) return chiz([]);
    taymer = setTimeout(function () {
      fetch(manzil + "?q=" + encodeURIComponent(soz), { credentials: "same-origin" })
        .then(function (j) { return j.json(); })
        .then(function (javob) {
          if (raqam !== oxirgiSorov) return;
          javob.tovarlar.forEach(function (d) { tanish[d.id] = d; });
          chiz(javob.tovarlar, javob.yana);
        })
        .catch(function () {
          if (raqam === oxirgiSorov && window.xabarBer) {
            window.xabarBer("Qidiruv ishlamadi — server bilan aloqa yo'q.", "error");
          }
        });
    }, KECHIKISH);
  }

  window.TovarOyna = { izla: izla, karta: karta, koddanKarta: koddanKarta };
})();
