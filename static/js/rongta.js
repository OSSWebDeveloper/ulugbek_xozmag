(() => {
  'use strict';
  const panel = document.getElementById('rongta-panel');
  if (!panel) return;
  const status = document.getElementById('rongta-holat');
  const count = document.getElementById('rongta-hisob');
  const test = document.getElementById('rongta-test');
  const send = document.getElementById('rongta-yukla');
  const progress = document.getElementById('rongta-progress');
  let syncing = false;
  async function json(url, options = {}) {
    const response = await fetch(url, {cache: 'no-store', ...options});
    if (response.redirected) throw new Error('Hisobingizga qayta kiring.');
    const data = await response.json();
    if (!response.ok) {
      const error = new Error(data.xato || 'Tarozi javob bermadi.');
      error.data = data;
      throw error;
    }
    return data;
  }
  function counts(data) {
    let text = `${data.tayyor} ta mahsulot yuborishga tayyor; ${data.otkazildi} ta o‘tkaziladi.`;
    if (data.sabablar && Object.keys(data.sabablar).length)
      text += ' Sabablar: ' + Object.entries(data.sabablar).map(([k, v]) => `${k}: ${v}`).join('; ') + '.';
    return text;
  }
  function cell(row, text, cls) {
    const td = row.insertCell();
    td.textContent = text;
    if (cls) td.className = cls;
  }
  async function list() {
    try {
      const data = await json(panel.dataset.royxat);
      const ready = document.getElementById('rongta-tayyor');
      const skipped = document.getElementById('rongta-otkaz');
      ready.replaceChildren();
      skipped.replaceChildren();
      for (const r of data.tayyor) {
        const row = ready.insertRow();
        cell(row, r.kod);
        cell(row, r.nom);
        cell(row, r.narx.toLocaleString('ru-RU', {maximumFractionDigits: 2}), 'son');
        cell(row, r.shtrix);
      }
      for (const r of data.otkazildi) {
        const row = skipped.insertRow();
        cell(row, r.kod);
        cell(row, r.nom);
        cell(row, r.sabab);
      }
      document.getElementById('rongta-tayyor-soni').textContent = data.tayyor.length + ' ta';
      document.getElementById('rongta-otkaz-soni').textContent = data.otkazildi.length + ' ta';
      // Ombordagi oynada katta ko'rsatkichlar ham bor
      const big = document.getElementById('rongta-tayyor-katta');
      if (big) big.textContent = data.tayyor.length + ' ta kg tovar';
      const bigSkip = document.getElementById('rongta-otkaz-katta');
      if (bigSkip) bigSkip.textContent = data.otkazildi.length + ' ta';
    } catch (e) {
      document.getElementById('rongta-tayyor-soni').textContent = e.message;
    }
  }
  async function check() {
    if (syncing) return;
    test.disabled = true;
    send.disabled = true;
    status.textContent = 'Tarozi javobi kutilmoqda…';
    try {
      const data = await json(panel.dataset.status);
      if (data.band) { watch(data.id); return; }
      status.textContent = `Aloqa bor: ${data.address}. Tarozi protokoli javob berdi.`;
      count.textContent = counts(data) + ' ' +
        (data.oxirgi ? `Oxirgi yuklash: ${data.oxirgi.tekshirildi} ta mahsulot qayta o‘qib tekshirilgan (${new Date(data.oxirgi.vaqt).toLocaleString()}).` : 'Hali to‘liq yuklash tekshirilmagan.');
      send.disabled = false;
    } catch (e) {
      status.textContent = e.message;
      // Tarozi yoki drayver yo'q bo'lsa ham nechta tovar ketishini ko'rsatamiz.
      if (e.data && e.data.tayyor !== undefined) count.textContent = counts(e.data);
    } finally {
      if (!syncing) test.disabled = false;
    }
  }
  async function watch(id) {
    syncing = true;
    send.disabled = true;
    test.disabled = true;
    progress.hidden = false;
    try {
      const data = await json(panel.dataset.progress.replace('00000000-0000-0000-0000-000000000000', id));
      progress.max = data.jami || 1;
      progress.value = data.yuborildi || 0;
      if (data.holat === 'xato') throw new Error(data.xato + ' ' + (data.izoh || ''));
      if (data.holat === 'tayyor') {
        status.textContent = `Tayyor: ${data.tekshirildi} ta mahsulot taroziga yuborildi va qayta o‘qib tekshirildi. ${data.otkazildi} ta o‘tkazildi.`;
        syncing = false;
        test.disabled = false;
        send.disabled = false;
        list();
      } else {
        status.textContent = data.holat === 'tekshirilmoqda' ? 'Tarozidan qayta o‘qib tekshirilmoqda…' : `Tarozi katalogi yangilanmoqda: ${data.yuborildi || 0} / ${data.jami} amal. Tarozini o‘chirmang.`;
        setTimeout(() => watch(id), 2000);
      }
    } catch (e) {
      status.textContent = e.message + ' Aloqani qayta tekshiring.';
      syncing = false;
      test.disabled = false;
      // Qisman yozilgan bo'lishi mumkin; holat tekshirilgach yana yuborish mumkin.
    }
  }
  test.addEventListener('click', check);
  send.addEventListener('click', async () => {
    send.disabled = true;
    test.disabled = true;
    try {
      const data = await json(panel.dataset.sync, {method: 'POST', headers: {
        'X-CSRFToken': document.querySelector('#rongta-csrf input').value,
      }});
      watch(data.id);
    } catch (e) {
      status.textContent = e.message;
      test.disabled = false;
    }
  });
  const form = document.getElementById('skaner-test-form');
  const input = document.getElementById('skaner-test-kod');
  const result = document.getElementById('skaner-test-natija');
  if (form) form.addEventListener('submit', async e => {
    e.preventDefault();
    const code = input.value.trim();
    if (!code) return;
    result.textContent = 'Tekshirilmoqda…';
    try {
      const data = await json(form.dataset.url + '?k=' + encodeURIComponent(code));
      result.textContent = data.topildi ? `Kod ${data.kod}: ${data.nom}` +
        (data.miqdor ? ` · Miqdor: ${data.miqdor} ${data.birlik}` : '') : data.xato;
    } catch (err) { result.textContent = err.message; }
    input.select();
  });
  // Tarozi IP manzili: saqlangach aloqa yangi manzilda darhol tekshiriladi.
  const ipForm = document.getElementById('rongta-ip-form');
  if (ipForm) ipForm.addEventListener('submit', async e => {
    e.preventDefault();
    const note = document.getElementById('rongta-ip-natija');
    const field = document.getElementById('rongta-ip');
    const button = ipForm.querySelector('button');
    button.disabled = true;
    note.classList.remove('xato');
    note.textContent = 'Saqlanmoqda…';
    try {
      const data = await json(ipForm.dataset.url, {method: 'POST', body: new FormData(ipForm)});
      field.value = data.ip;
      note.textContent = `Saqlandi: ${data.ip}. Aloqa shu manzilda tekshirilmoqda.`;
      check();
    } catch (err) {
      note.classList.add('xato');
      note.textContent = err.message;
      field.focus();
    } finally {
      button.disabled = false;
    }
  });
  // Ombor sahifasida panel oyna ichida: tarozi faqat oyna ochilganda so'raladi,
  // har sahifa ochilishida emas (aloqa tekshiruvi 15 soniyagacha cho'ziladi).
  const modal = document.getElementById('tarozi-oyna');
  if (modal) {
    const open = () => {
      modal.classList.add('ochiq');
      check();
      list();
    };
    const close = () => modal.classList.remove('ochiq');
    document.querySelectorAll('[data-tarozi-och]').forEach(b => b.addEventListener('click', open));
    modal.addEventListener('click', e => {
      if (e.target === modal || e.target.closest('[data-yop]')) close();
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && modal.classList.contains('ochiq')) close();
    });
  }
  if (!('kechiktir' in panel.dataset)) {
    check();
    list();
  }
})();
