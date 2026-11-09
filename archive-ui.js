const filters = document.querySelector('[data-filters]');
if (filters) {
  const records = [...document.querySelectorAll('[data-record]')];
  const controls = [...filters.querySelectorAll('input, select')];
  const count = document.querySelector('[data-count]');
  const normalize = value => value.normalize('NFKD').replace(/\p{Diacritic}/gu, '').toLowerCase();
  const initial = new URLSearchParams(location.search);
  for (const control of controls) {
    const value = initial.get(control.name);
    if (value && (control.tagName === 'INPUT' || [...control.options].some(option => option.value === value))) {
      control.value = value;
    }
  }
  function applyFilters() {
    let visible = 0;
    for (const record of records) {
      record.hidden = !controls.every(({name, value}) => {
        if (!value.trim()) return true;
        if (name !== 'q') return (record.dataset[name] || '').split('|').includes(value);
        return normalize(value).trim().split(/\s+/).every(word => normalize(record.dataset.search).includes(word));
      });
      if (!record.hidden) visible++;
    }
    count.textContent = visible === 1 ? '1 result' : visible + ' results';
  }
  filters.addEventListener('input', applyFilters);
  filters.addEventListener('submit', event => {
    event.preventDefault();
    applyFilters();
  });
  applyFilters();
}
function revealLinkedProfile() {
  const id = location.hash.slice(1);
  const profile = document.getElementById(id);
  if (profile?.tagName !== 'DETAILS') return;
  profile.open = true;
}
window.addEventListener('hashchange', revealLinkedProfile);
revealLinkedProfile();
