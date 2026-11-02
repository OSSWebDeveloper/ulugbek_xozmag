(() => {
  'use strict';
  document.querySelectorAll('.shtrix-maydon').forEach(cell => {
    const open = cell.querySelector('.shtrix-och');
    const form = cell.querySelector('form');
    const input = form.elements.shtrix_kod;
    const error = form.querySelector('.shtrix-xato');
    let busy = false;
    function close() { form.hidden = true; open.hidden = false; open.focus(); }
    open.addEventListener('click', () => {
      form.hidden = false; open.hidden = true;
      input.value = form.elements.eski.value; error.textContent = '';
      input.focus(); input.select();
    });
    form.querySelector('.shtrix-bekor').addEventListener('click', () => { if (!busy) close(); });
    input.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !busy) { event.preventDefault(); event.stopPropagation(); close(); }
    });
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (busy) return;
      busy = true; error.textContent = '';
      const payload = new FormData(form);
      form.querySelectorAll('button,input').forEach(el => el.disabled = true);
      try {
        const response = await fetch(form.action, {method: 'POST', body: payload});
        if (response.redirected) throw new Error('Seans tugadi. Hisobingizga qayta kiring.');
        const data = await response.json();
        if (!response.ok) throw new Error(data.xato || 'Saqlanmadi.');
        form.elements.eski.value = data.shtrix_kod;
        open.textContent = data.shtrix_kod || '—';
        close();
      } catch (e) { error.textContent = e.message || 'Aloqa xatosi. Qayta urinib ko‘ring.'; }
      finally { busy = false; form.querySelectorAll('button,input').forEach(el => el.disabled = false); }
    });
  });
})();
