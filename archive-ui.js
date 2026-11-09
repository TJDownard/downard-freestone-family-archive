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

// Enhance the existing link lists after they are available to the browser.
const archiveNavigation = document.querySelector('.archive-menu, .site-head nav');
const archiveHeader = document.querySelector('.top, .site-head > div');

if (archiveNavigation && archiveHeader) {
  const menu = document.createElement('div');
  menu.className = 'archive-menu-wrap';

  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'archive-menu-toggle';
  toggle.setAttribute('aria-label', 'Menu');
  toggle.setAttribute('aria-controls', 'archive-navigation');
  toggle.innerHTML = '<span class="archive-menu-icon" aria-hidden="true"><span></span><span></span><span></span></span>' +
    '<span class="archive-menu-label" aria-hidden="true">Menu</span>';

  archiveNavigation.id = 'archive-navigation';
  archiveNavigation.classList.add('archive-menu-panel');

  function setMenuOpen(open, restoreFocus = false) {
    toggle.setAttribute('aria-expanded', String(open));
    archiveNavigation.hidden = !open;
    if (restoreFocus) toggle.focus({ preventScroll: true });
  }

  setMenuOpen(false);
  menu.append(toggle, archiveNavigation);
  archiveHeader.classList.add('archive-nav-enhanced');
  archiveHeader.append(menu);

  toggle.addEventListener('click', () => setMenuOpen(archiveNavigation.hidden));
  archiveNavigation.addEventListener('click', event => {
    if (event.target.closest('a')) setMenuOpen(false, true);
  });
  document.addEventListener('click', event => {
    if (!archiveNavigation.hidden && !menu.contains(event.target)) setMenuOpen(false);
  });
  menu.addEventListener('focusout', event => {
    if (event.relatedTarget && !menu.contains(event.relatedTarget)) setMenuOpen(false);
  });
  menu.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !archiveNavigation.hidden) {
      event.preventDefault();
      setMenuOpen(false, true);
    }
  });
}
