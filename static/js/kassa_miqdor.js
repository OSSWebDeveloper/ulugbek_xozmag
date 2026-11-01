(() => {
  'use strict';
  const dialog = document.getElementById('miqdor-dialog');
  if (!dialog) return;
  const form = document.getElementById('miqdor-almashtir-forma');
  const input = document.getElementById('miqdor-katta-kirish');
  const error = document.getElementById('miqdor-katta-xato');
  const submit = document.getElementById('miqdor-katta-saqlash');
  let trigger = null;
  let replace = true;
  const numeric = text => Number(text.trim().replace(',', '.'));
  const format = value => value.toLocaleString('ru-RU', {maximumFractionDigits: 6});
  function preview() {
    const old = numeric(document.getElementById('miqdor-eski').value);
    const entered = numeric(input.value);
    const result = old * entered;
    const unit = trigger ? trigger.dataset.birlik : '';
    document.getElementById('miqdor-natija').textContent = input.value.trim() && Number.isFinite(result) && result > 0
      ? format(old) + ' × ' + format(entered) + ' = ' + format(result) + ' ' + unit : '';
  }
  document.querySelectorAll('[data-miqdor-och]').forEach(button => {
    button.addEventListener('click', () => {
      trigger = button;
      form.action = button.dataset.amal;
      document.getElementById('miqdor-eski').value = button.dataset.miqdor;
      input.value = '1';
      document.getElementById('miqdor-tovar-nomi').textContent = button.dataset.nom;
      error.hidden = true;
      submit.disabled = false;
      replace = true;
      preview();
      dialog.showModal();
      input.focus();
      input.select();
    });
  });
  dialog.addEventListener('close', () => { if (trigger) trigger.focus(); });
  dialog.addEventListener('keydown', e => { if (e.key !== 'Escape') e.stopPropagation(); });
  input.addEventListener('input', () => { replace = false; error.hidden = true; preview(); });
  dialog.addEventListener('click', e => {
    const button = e.target.closest('button');
    if (!button) return;
    if (button.hasAttribute('data-miqdor-yop')) return dialog.close();
    if (button.hasAttribute('data-miqdor-tozala')) { input.value = ''; replace = false; }
    else if (button.hasAttribute('data-miqdor-orqaga')) {
      input.value = replace ? '' : input.value.slice(0, -1);
      replace = false;
    } else if (button.hasAttribute('data-miqdor-raqam')) {
      const digit = button.dataset.miqdorRaqam;
      let value = replace ? '' : input.value;
      if (digit === ',' && /[.,]/.test(value)) return;
      if (digit === ',' && !value) value = '0';
      input.value = value + digit;
      replace = false;
    } else return;
    error.hidden = true;
    preview();
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
  });
  form.addEventListener('submit', e => {
    const raw = input.value.trim().replace(',', '.');
    const value = Number(raw);
    if (!/^\d+(\.\d{1,3})?$/.test(raw) || !Number.isFinite(value) || value <= 0 || value > 999999999.999) {
      e.preventDefault();
      error.textContent = 'Miqdor musbat son bo‘lsin. Masalan: 20 yoki 0,5.';
      error.hidden = false;
      input.focus();
      return;
    }
    const result = value * numeric(document.getElementById('miqdor-eski').value);
    if (result < .001 || result > 999999999.999 || Math.abs(result * 1000 - Math.round(result * 1000)) > .0001) {
      e.preventDefault();
      error.textContent = 'Natija musbat son bo‘lsin va ko‘pi bilan 3 kasr xonasi bo‘lsin.';
      error.hidden = false;
      input.focus();
      return;
    }
    submit.disabled = true;
  });
})();
