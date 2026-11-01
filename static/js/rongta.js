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
    if (!response.ok) throw new Error(data.xato || 'Tarozi javob bermadi.');
    return data;
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
      count.textContent = `${data.tayyor} ta mahsulot yuborishga tayyor; ${data.otkazildi} ta o‘tkaziladi. ` +
        (data.oxirgi ? `Oxirgi yuklash: ${data.oxirgi.tekshirildi} ta mahsulot qayta o‘qib tekshirilgan (${new Date(data.oxirgi.vaqt).toLocaleString()}).` : 'Hali to‘liq yuklash tekshirilmagan.');
      if (data.sabablar) count.textContent += ' Sabablar: ' + Object.entries(data.sabablar).map(([k,v]) => `${k}: ${v}`).join('; ');
      send.disabled = false;
    } catch (e) {
      status.textContent = e.message;
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
  form.addEventListener('submit', async e => {
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
  check();
})();
