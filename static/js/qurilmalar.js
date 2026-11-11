/* Qurilma nomlari Windows'dan keladi: faqat textContent bilan chiqariladi. */
(() => {
  'use strict';
  const root = document.getElementById('qurilmalar');
  if (!root) return;
  const list = document.getElementById('qurilma-royxat');
  const button = document.getElementById('qurilma-yangila');
  const error = document.getElementById('qurilma-xato');
  const message = document.getElementById('qurilma-xabar');
  const stamp = document.getElementById('qurilma-vaqt');
  let previous = null;
  const fresh = new Map();
  let busy = false;
  function node(tag, text, cls) {
    const el = document.createElement(tag);
    el.textContent = text;
    if (cls) el.className = cls;
    return el;
  }
  async function refresh() {
    if (busy) return;
    busy = true;
    button.disabled = true;
    list.setAttribute('aria-busy', 'true');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(root.dataset.url, {cache: 'no-store', signal: controller.signal});
      if (response.redirected) throw new Error('Seans tugadi. Sahifani qayta ochib, hisobingizga kiring.');
      const data = await response.json();
      if (!response.ok) throw new Error(data.xato || 'Ro‘yxatni olib bo‘lmadi.');
      const now = Date.now();
      const current = new Map(data.qurilmalar.map(d => [d.id, d.nom]));
      const added = previous ? data.qurilmalar.filter(d => !previous.has(d.id)) : [];
      const removed = previous ? [...previous].filter(([id]) => !current.has(id)) : [];
      added.forEach(d => fresh.set(d.id, now + 60000));
      for (const [id, until] of fresh) if (until < now || !current.has(id)) fresh.delete(id);
      if (added.length || removed.length) {
        message.textContent = [added.length ? `Yangi ulandi: ${added.map(d => d.nom).join(', ')}` : '',
          removed.length ? `Uzildi: ${removed.map(([, name]) => name).join(', ')}` : ''].filter(Boolean).join('. ');
      }
      const fragment = document.createDocumentFragment();
      data.qurilmalar.forEach(d => {
        const card = node('article', '', 'quti qurilma-karta');
        card.append(node('span', d.tur, 'sust'));
        if (fresh.has(d.id)) card.append(node('span', 'Yangi', 'nishon yashil qurilma-yangi'));
        card.append(node('h2', d.nom));
        card.append(node('p', d.holat, d.tayyor ? 'qurilma-tayyor' : 'qurilma-ogoh'));
        card.append(node('p', `Sinf: ${d.sinf}${d.port ? ' · Port: ' + d.port : ''}`, 'sust'));
        const detail = node('details', '');
        detail.append(node('summary', 'Qurilma identifikatori'), node('code', d.id));
        card.append(detail);
        fragment.append(card);
      });
      if (!data.qurilmalar.length) fragment.append(node('p', 'Klaviatura va sichqonchadan boshqa tashqi qurilma topilmadi.', 'quti'));
      list.replaceChildren(fragment);
      stamp.textContent = `${data.qurilmalar.length} ta qurilma · Tekshirildi: ${new Date(data.vaqt).toLocaleTimeString()}`;
      error.hidden = true;
      previous = current;
    } catch (e) {
      error.textContent = e.name === 'AbortError' ? 'Tekshirish vaqti tugadi. Qayta yangilang.' : e.message;
      error.hidden = false;
      stamp.textContent = previous ? 'Yangilanmadi. Quyida oxirgi olingan ro‘yxat.' : 'Qurilmalar aniqlanmadi.';
    } finally {
      clearTimeout(timeout);
      busy = false;
      button.disabled = false;
      list.setAttribute('aria-busy', 'false');
    }
  }
  button.addEventListener('click', refresh);
  setInterval(() => { if (!document.hidden) refresh(); }, 10000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
  refresh();
})();

/* Printer tests always use the logged-in cashier's USB helper. */
(() => {
  const form = document.getElementById('printer-sinov-form');
  if (!form) return;
  const button = form.querySelector('button');
  const message = document.getElementById('printer-sinov-xabar');
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (button.disabled) return;
    button.disabled = true;
    message.textContent = 'Sinov yuborilmoqda…';
    try {
      const response = await fetch(form.action, {method: 'POST', body: new FormData(form)});
      if (response.redirected) throw new Error('Seans tugadi. Hisobingizga qayta kiring.');
      const data = await response.json();
      if (!response.ok) throw new Error(data.xato || 'Sinov yuborilmadi.');
      message.textContent = data.xabar;
      if (data.bosma) window.brauzerChek(data.bosma);
      if (data.url) {
        for (let i = 0; i < 20; i++) {
          await new Promise(resolve => setTimeout(resolve, 1500));
          const result = await fetch(data.url, {cache: 'no-store'});
          if (result.redirected) throw new Error('Seans tugadi. Hisobingizga qayta kiring.');
          const state = await result.json();
          if (!result.ok) throw new Error(state.xato || 'Sinov holatini olib bo‘lmadi.');
          message.textContent = state.xabar;
          if (['tayyor','xato'].includes(state.holat)) return;
        }
        message.textContent = 'Sinov holati hali tasdiqlanmadi. Qog‘oz va USB yordamchisini tekshiring; qayta bosish navbatdagi sinovni takrorlamaydi.';
      }
    } catch (error) {
      message.textContent = error.message;
    } finally { button.disabled = false; }
  });
})();
