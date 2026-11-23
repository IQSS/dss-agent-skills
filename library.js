(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  let skills = [];
  let activeGroup = 'All skills';
  let pinnedName = null;
  let shownName = '';
  let currentPage = 0;
  const PAGE_SIZE = 9;

  const normalize = (value) => value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  function displaySkill(name) {
    const skill = skills.find(item => item.name === name);
    if (!skill) return;
    if (shownName !== name) {
      $('skill-title').textContent = skill.title;
      $('skill-group').textContent = skill.group;
      $('skill-summary').textContent = skill.summary;
      $('skill-steps').replaceChildren(...skill.steps.map(text => {
        const li = document.createElement('li');
        li.textContent = text;
        return li;
      }));
      const icon = document.createElement('img');
      icon.src = `assets/library/${skill.icon}`;
      icon.alt = '';
      $('skill-illustration').replaceChildren(icon);
      $('open-skill').href = `skills/${skill.name}.html`;
      $('open-skill').setAttribute('aria-label', `Open ${skill.title}`);
      $('download-skill').href = `downloads/${skill.name}.zip`;
      $('download-skill').setAttribute('aria-label', `Download the ${skill.name} skill`);
      $('skill-command').textContent = skill.prompt.split('\n')[0];
      $('skill-example').textContent = skill.example;
      $('copy-prompt').textContent = 'Copy prompt';
      shownName = name;
    }
    document.querySelectorAll('.skill-book').forEach(book => {
      book.setAttribute('aria-pressed', String(book.dataset.skill === pinnedName));
    });
    const pinned = pinnedName === shownName;
    const label = pinned ? 'Unpin this book' : 'Pin this book';
    $('pin-book').setAttribute('aria-pressed', String(pinned));
    $('pin-book').setAttribute('aria-label', label);
    $('pin-book').title = label;
    $('selection-status').textContent = pinned
      ? `${skill.name} · pinned open · click the book or bookmark to unpin`
      : `${skill.name} · hover to explore, click to pin`;
  }

  function togglePin(name, scroll = true) {
    pinnedName = pinnedName === name ? null : name;
    history.replaceState(null, '', `${location.pathname}${location.search}${pinnedName ? '#' + pinnedName : ''}`);
    displaySkill(name);
    if (pinnedName && scroll && matchMedia('(max-width: 930px)').matches) {
      $('open-book').scrollIntoView({block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
    }
  }

  function previewSkill(name) {
    if (!pinnedName) displaySkill(name);
  }

  function renderShelves() {
    const query = normalize($('search').value.trim());
    const tokens = query.split(/\s+/).filter(Boolean);
    const matches = skills.filter(item => {
      const text = normalize([item.name, item.title, item.group, item.summary, item.requirements, item.prompt, item.example, ...item.outcomes].join(' '));
      return (activeGroup === 'All skills' || item.group === activeGroup) && tokens.every(token => text.includes(token));
    });
    $('shelves').replaceChildren();
    const pageCount = Math.max(1, Math.ceil(matches.length / PAGE_SIZE));
    currentPage = Math.min(currentPage, pageCount - 1);
    const visible = matches.slice(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE);
    const groups = [...new Set(visible.map(item => item.group))];
    for (const group of groups) {
      const groupSkills = visible.filter(item => item.group === group);
      for (let start = 0; start < groupSkills.length; start += 3) {
        const section = document.createElement('section');
        section.className = 'shelf-group';
        section.setAttribute('aria-label', group);
        const books = document.createElement('div');
        books.className = 'books';
        for (const skill of groupSkills.slice(start, start + 3)) {
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'skill-book';
          button.dataset.skill = skill.name;
          button.setAttribute('aria-label', `${skill.title}: ${skill.name}`);
          button.setAttribute('aria-pressed', String(skill.name === pinnedName));
          button.setAttribute('aria-controls', 'open-book');
          button.style.setProperty('--cover', skill.cover);
          button.style.setProperty('--cover-edge', skill.edge);
          const title = document.createElement('span');
          title.className = 'book-title';
          title.textContent = skill.coverTitle;
          const icon = document.createElement('img');
          icon.src = `assets/library/${skill.icon}`;
          icon.className = 'book-icon';
          icon.alt = '';
          const name = document.createElement('span');
          name.className = 'book-name';
          name.textContent = skill.name;
          const marker = document.createElement('span');
          marker.className = 'selected-tab';
          marker.setAttribute('aria-hidden', 'true');
          button.append(title, icon, name, marker);
          button.addEventListener('pointerenter', event => {
            if (event.pointerType === 'mouse') previewSkill(skill.name);
          });
          button.addEventListener('focus', () => previewSkill(skill.name));
          button.addEventListener('click', () => togglePin(skill.name));
          button.addEventListener('keydown', event => {
            if (event.key === 'Escape' && pinnedName) togglePin(pinnedName, false);
          });
          books.append(button);
        }
        const ledge = document.createElement('div');
        ledge.className = 'shelf-ledge';
        const label = document.createElement('span');
        label.className = 'shelf-label';
        label.textContent = group;
        ledge.append(label);
        section.append(books, ledge);
        $('shelves').append(section);
      }
    }
    $('shelves').hidden = !matches.length;
    $('empty-state').hidden = Boolean(matches.length);
    $('result-count').textContent = `${matches.length} ${matches.length === 1 ? 'skill' : 'skills'}`;
    $('shelf-pages').hidden = pageCount <= 1;
    $('page-number').textContent = `${currentPage + 1} of ${pageCount}`;
    $('previous-page').disabled = currentPage === 0;
    $('next-page').disabled = currentPage === pageCount - 1;
    displaySkill(pinnedName || shownName || skills[0].name);
  }

  function renderFilters() {
    $('filters').replaceChildren();
    for (const label of ['All skills', ...new Set(skills.map(item => item.group))]) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'filter';
      button.textContent = label;
      button.setAttribute('aria-pressed', String(label === activeGroup));
      button.addEventListener('click', () => {
        activeGroup = label;
        currentPage = 0;
        $('filters').querySelectorAll('button').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
        renderShelves();
      });
      $('filters').append(button);
    }
  }
  $('search').addEventListener('input', () => { currentPage = 0; renderShelves(); });
  $('previous-page').addEventListener('click', () => { currentPage -= 1; renderShelves(); });
  $('next-page').addEventListener('click', () => { currentPage += 1; renderShelves(); });
  $('reset-filters').addEventListener('click', () => {
    activeGroup = 'All skills';
    currentPage = 0;
    $('search').value = '';
    renderFilters();
    renderShelves();
    $('search').focus();
  });
  $('pin-book').addEventListener('click', () => togglePin(shownName, false));
  $('copy-prompt').addEventListener('click', async () => {
    const skill = skills.find(item => item.name === shownName);
    try {
      await navigator.clipboard.writeText(skill.prompt);
      $('copy-prompt').textContent = 'Copied';
    } catch {
      $('copy-prompt').textContent = 'Copy unavailable';
    }
  });

  try {
    skills = JSON.parse($('library-data').textContent);
    const hash = location.hash.slice(1);
    if (skills.some(item => item.name === hash)) pinnedName = hash;
    renderFilters();
    renderShelves();
    document.querySelector('.library-tools').hidden = false;
    document.querySelector('.library-scene').hidden = false;
    $('library-index').open = false;
  } catch {
    document.querySelector('.library-tools').hidden = true;
    document.querySelector('.library-scene').hidden = true;
    $('library-index').open = true;
  }

  // One set of corner coordinates joins the cabinet's top, side, and plinth.
  const cabinet = document.querySelector('.cabinet');
  new ResizeObserver(() => {
    const { width: w, height: h } = cabinet.getBoundingClientRect();
    if (!w || !h) return;
    const depth = w < 400 ? 12 : 20;
    const rise = depth * 0.7;
    const x = w - 1;
    const backX = x + depth;
    const bottom = h - 1;
    const artwork = cabinet.querySelector('.cabinet-depth');
    artwork.setAttribute('viewBox', `0 0 ${w} ${h}`);
    artwork.querySelector('.cabinet-top-face').setAttribute('d', `M1 1 L${1 + depth} ${1 - rise} H${backX} L${x} 1 Z`);
    artwork.querySelector('.cabinet-side-face').setAttribute('d', `M${x} 1 L${backX} ${1 - rise} V${bottom - rise} L${x} ${bottom} Z`);
    artwork.querySelector('.cabinet-base-side').setAttribute('d', `M${x} ${bottom - 22} L${backX} ${bottom - 22 - rise} V${bottom - rise} L${x} ${bottom} Z`);
  }).observe(cabinet);

})();
