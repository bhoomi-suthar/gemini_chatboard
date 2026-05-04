/* dark and light mode theme */

const el = id => document.getElementById(id);

const savedTheme = localStorage.getItem('theme') || 'dark';

if (savedTheme === 'dark') {
  document.body.classList.add('dark');
}

const moonSVG = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
const sunSVG = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;

function toggleTheme() {
  document.body.classList.toggle('dark');
  const isDark = document.body.classList.contains('dark');
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
  el('theme-btn').innerHTML = isDark ? sunSVG : moonSVG;
}

window.addEventListener('DOMContentLoaded', () => {
  if (localStorage.getItem('theme') === 'dark') {
    el('theme-btn').innerHTML = sunSVG;
  }
});

/* Search */
const historyData = JSON.parse(el('history-data').textContent);

function searchChats(query) {
  const results = el('search-results');
  query = query.trim().toLowerCase();

  if (!query) {
    results.classList.remove('open');
    results.innerHTML = '';
    return;
  }

  const matches = Object.entries(historyData).filter(([id, chat]) =>
    chat.title.toLowerCase().includes(query)
  );

  if (matches.length === 0) {
    results.innerHTML = `<div class="search-no-result">No chats found</div>`;
  } else {
    results.innerHTML = matches.map(([id, chat]) => `
         <a href="/chat/${id}" class="search-result-item">
          <span class="search-result-text">${chat.title}</span>
         </a>
        `).join('');
  }
  results.classList.add('open');
}

/* close search on outside click */
document.addEventListener('click', (e) => {
  if (!el('search-input').contains(e.target) && !el('search-results').contains(e.target)) {
    el('search-results').classList.remove('open');
  }
  // only close sidebar dropdowns, NOT table export dropdowns
  document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('open'));

  // close table export dropdowns only when clicking outside them
  if (!e.target.closest('.table-wrapper')) {
    document.querySelectorAll('.table-export-dropdown').forEach(d => d.classList.remove('open'));
  }
});


/* favorite panel */
function toggleFavPanel() {
  const panel = el('fav-panel');
  const btn = el('fav-nav-btn');
  panel.classList.toggle('open');
  btn.classList.toggle('active-fav');
}

function togglePin(id, e) {
  e.stopPropagation();
  el('menu-' + id).classList.remove('open');
  fetch('/chat/' + id + '/pin', { method: 'POST' })
    .then(() => location.reload());
}

/* loading */
function showLoading() {
  const messages = document.querySelector(".messages");
  if (messages) sessionStorage.setItem("scrollPos", messages.scrollTop);

  document.getElementById('response-mode-input').value = responseMode === 'chart' ? chartType : 'table';
  document.getElementById('btn-text').style.display = 'none';
  document.getElementById('dots').style.display = 'flex';
  document.getElementById('send-btn').disabled = true;
}

/* dropdown menu */
function toggleMenu(id, e) {
  e.stopPropagation();
  document.querySelectorAll('.dropdown').forEach(d => d.id !== 'menu-' + id && d.classList.remove('open'));
  el('menu-' + id).classList.toggle('open');
}

function openRename(id, title) {
  el('menu-' + id).classList.remove('open');
  el('normal-' + id).style.display = 'none';
  el('rename-' + id).classList.add('open');
  el('rename-input-' + id).value = title;
  el('rename-input-' + id).focus();
}

function closeRename(id) {
  el('normal-' + id).style.display = 'flex';
  el('rename-' + id).classList.remove('open');
}

function closeRename(id) {
  el('normal-' + id).style.display = 'flex';
  el('rename-' + id).style.display = 'none';
}

window.addEventListener("load", () => {
  const messages = document.querySelector(".messages");
  const saved = sessionStorage.getItem("scrollPos");
  if (messages && saved !== null) messages.scrollTop = saved;
});

/* PDF viewer */
function openPdfViewer(filename) {
  el('pdf-viewer-title').textContent = filename;
  el('pdf-iframe').src = '/pdf/' + filename;
  el('pdf-viewer-panel').classList.add('open');
}

function closePdfViewer() {
  el('pdf-viewer-panel').classList.remove('open');
  el('pdf-iframe').src = '';
}

/* pdf */
function showPdfTag(input) {
  if (input.files[0]) {
    el('pdf-name-text').textContent = input.files[0].name;
    el('pdf-tag').classList.add('show');
  }
}

function removePdf() {
  el('pdf-input').value = '';
  el('pdf-name-text').textContent = '';
  el('pdf-tag').classList.remove('show');
}

function showPdfTag(input) {
  if (input.files[0]) {
    let name = input.files[0].name;
    if (name.length > 28) {
      name = name.substring(0, 25) + "...";
    }
    el('pdf-name-text').textContent = name;
    el('pdf-tag').classList.add('show');
  }
}

/* text box size */
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 160) + 'px';

  // trigger text wave animation
  el.classList.remove('animate-text');
  void el.offsetWidth; // restart animation
  el.classList.add('animate-text');
}

function handleEnter(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (el('send-btn') && !el('send-btn').disabled) {
      el('send-btn').closest('form').requestSubmit();
    }
  }
}

/* table-chart mode toggle */
let responseMode = localStorage.getItem('responseMode') || 'table';
let chartType = localStorage.getItem('chartType') || 'bar';

const chartIcons = {
  bar: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  pie: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>`,
  line: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
  doughnut: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/></svg>`,
  radar: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5"/></svg>`
};

const chartLabels = { bar: 'Bar', pie: 'Pie', line: 'Line', doughnut: 'Doughnut', radar: 'Radar' };

window.addEventListener('DOMContentLoaded', () => {
  updateModeBtn();
  if (localStorage.getItem('theme') === 'dark') el('theme-btn').innerHTML = sunSVG;
});

function toggleResponseMode() {
  if (responseMode === 'table') {
    // Table -> Chart
    responseMode = 'chart';
    localStorage.setItem('responseMode', responseMode);
    updateModeBtn();
  } else {
    responseMode = 'table';
    localStorage.setItem('responseMode', responseMode);
    updateModeBtn();
    el('chart-dropdown').classList.remove('open');
  }
}

function selectChart(type) {
  chartType = type;
  localStorage.setItem('chartType', chartType);
  el('chart-dropdown').classList.remove('open');
  updateModeBtn();
  document.querySelectorAll('.chart-option').forEach(o => o.classList.remove('active'));
  document.querySelectorAll('.chart-option').forEach(o => {
    if (o.textContent.toLowerCase().includes(type)) o.classList.add('active');
  });
  // convert last chart to new type
  convertLastChart(type);
}


function convertLastChart(newType) {
  const canvases = document.querySelectorAll('.messages canvas');
  if (canvases.length === 0) return;
  // get only the last canvas
  const lastCanvas = canvases[canvases.length - 1];
  const canvasId = lastCanvas.id;
  const existingChart = Chart.getChart(canvasId);
  if (!existingChart) return;
  // grab current data and labels from existing chart
  const currentData = existingChart.data;
  const currentOptions = existingChart.options;

  existingChart.destroy();
  // new chart but same data
  new Chart(lastCanvas, {
    type: newType,
    data: currentData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true }
      }
    }
  });
}

// update button on select any chart
function updateModeBtn() {
  const tableIcon = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>`;
  const btn = el('mode-btn');
  if (!btn) return;
  if (responseMode === 'chart') {
    btn.innerHTML = `
      ${chartIcons[chartType]} 
      <span id="mode-label">${chartLabels[chartType]}</span> 
      <svg id="chart-arrow" onclick="toggleDropdown(event)" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-left:2px; cursor:pointer;">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    `;
  } else {
    btn.innerHTML = `
      ${tableIcon} 
      <span id="mode-label">Table</span>
    `;
    responseMode = 'table';
    localStorage.setItem('responseMode', responseMode);
  }
}

// close chart dropdown on outside click 
document.addEventListener('click', (e) => {
  if (!el('search-input').contains(e.target) && !el('search-results').contains(e.target))
    el('search-results').classList.remove('open');
  document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('open'));
  const wrapper = el('chart-mode-wrapper');
  if (wrapper && !wrapper.contains(e.target))
    el('chart-dropdown').classList.remove('open');
});

// open close the chart dropdown
function toggleDropdown(e) {
  e.stopPropagation();
  if (responseMode === 'chart') {
    el('chart-dropdown').classList.toggle('open');
  }
}

/* speech to text */
let recognition = null;
let isListening = false;

function toggleSpeech() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('Speech recognition is not supported in your browser. Please use Chrome.');
    return;
  }

  if (isListening) {
    stopSpeech();
    return;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();

  recognition.lang = 'en-US';
  recognition.continuous = false; // stop after one sentence
  recognition.interimResults = false;

  recognition.onend = () => {
    stopSpeech();
  };

  recognition.onstart = () => {
    isListening = true;
    el('mic-btn').classList.add('listening');
    el('voice-wave').style.display = 'flex';
    const textarea = document.querySelector('.msg-input');
    textarea.placeholder = '';
    textarea.dataset.oldText = textarea.value;
    textarea.classList.add('speaking');
  };

  recognition.onresult = (event) => {
    let transcript = '';
    for (let i = 0; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    const textarea = document.querySelector('.msg-input');
    textarea.value = (textarea.dataset.oldText || '') + ' ' + transcript;

    textarea.classList.remove('animate-text');
    void textarea.offsetWidth;
    textarea.classList.add('animate-text');

    autoResize(textarea);
  };

  recognition.onerror = (event) => {
    console.error('Speech error:', event.error);
    stopSpeech();
  };

  recognition.start();
}

function stopSpeech() {
  isListening = false;
  el('mic-btn').classList.remove('listening');
  el('voice-wave').style.display = 'none';
  const textarea = document.querySelector('.msg-input');
  textarea.placeholder = 'Enter here';
  textarea.classList.remove('speaking'); // stop animation

  if (recognition) {
    recognition.stop();
    recognition = null;
  }
}


/* topic mode */
let currentTopic = localStorage.getItem('currentTopic') || '';

window.addEventListener('DOMContentLoaded', () => {
  updateModeBtn();
  if (localStorage.getItem('theme') === 'dark') el('theme-btn').innerHTML = sunSVG;
  applyTopic(currentTopic);
});

function openTopicModal() {
  el('topic-modal-overlay').classList.add('open');
  el('topic-input').value = currentTopic;
  el('topic-input').focus();
}

function closeTopicModal(e) {
  el('topic-modal-overlay').classList.remove('open');
}

function saveTopic() {
  const topic = el('topic-input').value.trim();
  currentTopic = topic;
  localStorage.setItem('currentTopic', topic);
  applyTopic(topic);
  el('topic-modal-overlay').classList.remove('open');
}

function clearTopic() {
  currentTopic = '';
  localStorage.removeItem('currentTopic');
  el('topic-input').value = '';
  const hidden = el('topic-hidden');
  if (hidden) hidden.value = '';
  applyTopic('');
  el('topic-modal-overlay').classList.remove('open');
}

function applyTopic(topic) {
  const btn = el('topic-btn');
  const badge = el('topic-badge');
  const badgeText = el('topic-badge-text');
  const label = el('topic-btn-label');

  // always update ALL hidden inputs 
  document.querySelectorAll('#topic-hidden').forEach(h => {
    h.value = topic || '';
  });

  if (topic) {
    btn.classList.add('active');
    label.textContent = topic.length > 12 ? topic.substring(0, 12) + '...' : topic;
    badge.classList.add('show');
    badgeText.textContent = topic;
  } else {
    btn.classList.remove('active');
    label.textContent = 'Topic';
    badge.classList.remove('show');
    badgeText.textContent = '';
  }
}


/* edit message */
function openEditMsg(idx) {
  const bubble = el('bubble-' + idx);
  const editBox = el('editbox-' + idx);
  const ta = el('edit-ta-' + idx);
  const editBtn = document.querySelector('#msgrow-' + idx + ' .edit-msg-btn');

  const raw = bubble.innerText.trim();
  ta.value = raw;
  bubble.style.display = 'none';
  if (editBtn) editBtn.style.display = 'none';
  editBox.classList.add('open');
  ta.style.height = 'auto';
  ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
  ta.focus();
  ta.oninput = () => {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
  };
}

function closeEditMsg(idx) {
  const bubble = el('bubble-' + idx);
  const editBox = el('editbox-' + idx);
  const editBtn = document.querySelector('#msgrow-' + idx + ' .edit-msg-btn');
  bubble.style.display = '';
  if (editBtn) editBtn.style.display = '';
  editBox.classList.remove('open');
}

function submitEdit(idx) {
  const ta = el('edit-ta-' + idx);
  const text = ta.value.trim();
  if (!text) return;

  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/chat/edit';
  form.enctype = 'multipart/form-data';
  form.style.display = 'none';

  const fields = {
    chat_id: document.querySelector('input[name="chat_id"]').value,
    message: text,
    response_mode: responseMode === 'chart' ? chartType : 'table',
    topic: document.querySelector('#topic-hidden') ? document.querySelector('#topic-hidden').value : '',
    edit_from_index: idx
  };

  Object.entries(fields).forEach(([name, value]) => {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value;
    form.appendChild(input);
  });

  document.body.appendChild(form);

  el('btn-text').style.display = 'none';
  el('dots').style.display = 'flex';
  el('send-btn').disabled = true;

  form.submit();
}

/* edit button delegation */
document.addEventListener('click', function (e) {
  const editBtn = e.target.closest('.edit-msg-btn');
  if (editBtn) {
    const idx = editBtn.dataset.idx;
    const bubble = el('bubble-' + idx);
    const editBox = el('editbox-' + idx);
    const ta = el('edit-ta-' + idx);
    const raw = bubble.innerText.trim();
    ta.value = raw;
    bubble.style.display = 'none';
    editBtn.style.display = 'none';
    editBox.classList.add('open');
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
    ta.focus();
    ta.oninput = () => {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
    };
    return;
  }

  const cancelBtn = e.target.closest('.edit-cancel-btn');
  if (cancelBtn) {
    const idx = cancelBtn.dataset.idx;
    const bubble = el('bubble-' + idx);
    const editBox = el('editbox-' + idx);
    const editBtnEl = document.querySelector('#msgrow-' + idx + ' .edit-msg-btn');
    bubble.style.display = '';
    if (editBtnEl) editBtnEl.style.display = '';
    editBox.classList.remove('open');
    return;
  }

  const sendBtn = e.target.closest('.edit-send-btn');
  if (sendBtn) {
    const idx = sendBtn.dataset.idx;
    submitEdit(idx);
    return;
  }
});


/* share chat */

function openShareModal() {
  const chatId = document.querySelector('input[name="chat_id"]').value;
  if (!chatId) {
    alert('No chat to share.');
    return;
  }
  // generate share link from backend
  fetch(`/chat/${chatId}/share`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
      const link = `${window.location.origin}/share/${data.share_id}`;
      el('share-preview').innerHTML = `
        <div style="display:flex;flex-direction:column;gap:10px;">
          <div style="display:flex;gap:8px;align-items:center;">
            <input id="share-link-input" type="text" value="${link}" readonly
              style="flex:1;padding:8px 12px;border:1px solid var(--input-border);border-radius:8px;background:var(--bg);color:var(--input-text);font-size:0.82rem;outline:none;font-family:sans-serif;" />
          </div>
        </div>
      `;

      // save to localStorage so it shows in "Shared Chats" section
      const shareKey = 'shared_chats';
      let sharedList = [];
      try { sharedList = JSON.parse(localStorage.getItem(shareKey) || '[]'); } catch (e) { }
      const chatTitle = document.querySelector('.history-row.active .history-item')?.textContent?.trim() || 'Shared Chat';
      sharedList.unshift({ share_id: data.share_id, title: chatTitle, link: link, time: Date.now() });
      localStorage.setItem(shareKey, JSON.stringify(sharedList.slice(0, 20)));

      /* instantly add shared chat to sidebar without refresh */
      const sharedContainer = document.getElementById('shared-chats-list');

      if (sharedContainer) {
        const existing = sharedContainer.querySelector(`[data-share-id="${data.share_id}"]`);

        if (!existing) {
          const item = document.createElement('a');
          item.href = `/share/${data.share_id}`;
          item.className = 'history-item';
          item.setAttribute('data-share-id', data.share_id);
          item.textContent = chatTitle;

          const row = document.createElement('div');
          row.className = 'history-row';
          row.appendChild(item);

          // add at top
          sharedContainer.prepend(row);
        }
      }

      el('share-modal-overlay').classList.add('open');

      // reset copy button
      const btn = el('share-copy-btn');
      btn.classList.remove('copied');
      btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy Link`;
    })
    .catch(() => alert('Could not generate share link.'));
}

function closeShareModal(e) {
  if (!e || e.target === el('share-modal-overlay'))
    el('share-modal-overlay').classList.remove('open');
}

function copyShareText() {
  const input = el('share-link-input');
  if (!input) return;
  navigator.clipboard.writeText(input.value).then(() => {
    const btn = el('share-copy-btn');
    btn.classList.add('copied');
    btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
    setTimeout(() => {
      btn.classList.remove('copied');
      btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy Link`;
    }, 2000);

    // add to shared chats sidebar instantly
    addToSharedSidebar();
  });
}


function addToSharedSidebar() {
  const sharedList = document.getElementById('shared-chats-list');
  if (!sharedList) return;

  const chatTitle = document.querySelector('.history-row.active .history-item')?.textContent?.trim() || 'Shared Chat';
  const input = el('share-link-input');
  if (!input) return;
  const link = input.value;

  // check if already added
  if (sharedList.querySelector(`[href="${link}"]`)) return;

  // show the shared chats label if hidden
  const label = document.querySelector('.sidebar-section-label[style*="4a90e2"]');
  if (label) label.style.display = '';

  const row = document.createElement('div');
  row.className = 'history-row';
  row.innerHTML = `
    <div class="row-normal">
      <a href="${link}" class="history-item" style="color:#4a90e2;">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:3px;vertical-align:middle;flex-shrink:0">
          <circle cx="18" cy="5" r="3"/>
          <circle cx="6" cy="12" r="3"/>
          <circle cx="18" cy="19" r="3"/>
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
          <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
        </svg>
        ${chatTitle}
      </a>
    </div>
  `;
  sharedList.prepend(row);
}

/* unshare chat */

function unshareChat(chatId) {
  fetch('/chat/' + chatId + '/unshare', { method: 'POST' })
    .then(() => location.reload());
}

function updateShareButton() {
  const btn = document.getElementById('share-btn');
  if (!btn) return;

  if (isShared === true || isShared === 'true') {
    btn.innerHTML = `
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
      Unshare
    `;
  } else {
    btn.innerHTML = `
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="18" cy="5" r="3"/>
        <circle cx="6" cy="12" r="3"/>
        <circle cx="18" cy="19" r="3"/>
        <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
        <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
      </svg>
      Share
    `;
  }
}


function handleShareClick() {
  if (isShared === true || isShared === 'true') {

    if (!confirm("Unshare this chat?")) return;

    fetch(`/chat/${currentChatId}/unshare`, {
      method: 'POST'
    }).then(() => location.reload());

  } else {
    openShareModal();
  }
}
document.addEventListener('DOMContentLoaded', updateShareButton);


/* ── Table Export ── */
function wrapTablesWithExport() {
  document.querySelectorAll('.msg-row.gemini .bubble table').forEach(table => { //only select table inside ai response
    if (table.parentElement.classList.contains('table-wrapper')) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'table-wrapper';
    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);

    // export button sits ABOVE table via padding-top on wrapper
    const exportBtn = document.createElement('button');
    exportBtn.className = 'table-export-btn';
    exportBtn.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>&nbsp;Export`;

    const dropdown = document.createElement('div');
    dropdown.className = 'table-export-dropdown';
    dropdown.innerHTML = `
      <button class="table-export-option" data-format="csv">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>CSV
      </button>
      <button class="table-export-option" data-format="excel">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>Excel
      </button>
      <button class="table-export-option" data-format="json">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>JSON
      </button>`;

    exportBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      // close all other dropdowns first
      document.querySelectorAll('.table-export-dropdown.open').forEach(d => d.classList.remove('open'));
      dropdown.classList.toggle('open');
    });


    dropdown.querySelectorAll('.table-export-option').forEach(opt => {
      opt.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.remove('open');
        exportTable(table, opt.dataset.format);
      });
    });

    // append button and dropdown to wrapper
    wrapper.insertBefore(dropdown, table);
    wrapper.insertBefore(exportBtn, dropdown);
  });
}


function parseTable(table) {
  const rows = [];
  table.querySelectorAll('tr').forEach(tr => {
    const cells = [];
    tr.querySelectorAll('th, td').forEach(td => cells.push(td.innerText.trim()));
    if (cells.length) rows.push(cells);
  });
  return rows;
}

function exportTable(table, format) {
  const rows = parseTable(table);
  if (!rows.length) return;

  if (format === 'csv') {
    const csv = rows.map(r => r.map(c => `"${c.replace(/"/g, '""')}"`).join(',')).join('\n');
    downloadFile('table_export.csv', csv, 'text/csv');
  } else if (format === 'json') {
    if (rows.length < 2) return;
    const headers = rows[0];
    const data = rows.slice(1).map(row => {
      const obj = {};
      headers.forEach((h, i) => obj[h] = row[i] || '');
      return obj;
    });
    downloadFile('table_export.json', JSON.stringify(data, null, 2), 'application/json');
  } else if (format === 'excel') {
    let xml = `<?xml version="1.0"?><Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><Worksheet ss:Name="Sheet1"><Table>`;
    rows.forEach(row => {
      xml += '<Row>';
      row.forEach(cell => {
        xml += `<Cell><Data ss:Type="String">${cell.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</Data></Cell>`;
      });
      xml += '</Row>';
    });
    xml += '</Table></Worksheet></Workbook>';
    downloadFile('table_export.xls', xml, 'application/vnd.ms-excel');
  }
}

function downloadFile(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/* ── Scroll to bottom ── */
function initScrollButton() {
  const msgs = document.querySelector('.messages');
  const btn = document.getElementById('scroll-bottom-btn');
  if (!msgs || !btn) return;
  msgs.addEventListener('scroll', () => {
    const atBottom = msgs.scrollHeight - msgs.scrollTop - msgs.clientHeight < 80;
    if (atBottom) {
      btn.classList.remove('show');
    } else {
      btn.classList.add('show');
    }
  });
}

function scrollToBottom() {
  const msgs = document.querySelector('.messages');
  if (msgs) msgs.scrollTo({ top: msgs.scrollHeight, behavior: 'smooth' });
}



// run on page load — wrap existing tables and init scroll button
window.addEventListener('load', () => {
  wrapTablesWithExport();
  initScrollButton();

  // get suggestions only from last AI response
  const aiMessages = document.querySelectorAll('.msg-row.gemini .bubble');

  if (aiMessages.length > 0) {
    const lastBubble = aiMessages[aiMessages.length - 1];
    lastAISuggestions = extractSuggestionsFromText(lastBubble.innerText);
  } else {
    lastAISuggestions = [];
  }

  initSuggestions();

  const msgs = document.querySelector('.messages');
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
});


/* ── Suggestions ── */


const defaultSuggestions = [
  'What is this topic about?',
  'How does this work?',
  'Explain this concept simply',
  'Create a table from this data',
  'Generate a chart from numbers',
  'Summarize this information',
  'how to create this?',
];

let lastAISuggestions = [];

/* extract suggestions from latest AI response */
function extractSuggestionsFromText(text) {
  if (!text) return [];

  const plain = text
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  if (!plain) return [];

  // split into sentences
  const sentences = plain
    .split(/[.!?]/)
    .map(s => s.trim())
    .filter(s => s.length > 15);

  const suggestions = [];
  sentences.slice(0, 5).forEach(sentence => {
    const words = sentence.split(' ');

    if (words.length >= 4) {
      const topic = words.slice(0, 6).join(' ');
      suggestions.push(topic);
    }
  });
  return [...new Set(suggestions)].slice(0, 3);
}

/* render suggestions */
function renderSuggestions(items) {
  const box = document.getElementById('suggestions-box');
  if (!box) return;

  box.innerHTML = '';

  items.slice(0, 3).forEach(text => {   // only first 3
    const div = document.createElement('div');
    div.className = 'suggestion-item';
    div.textContent = text;
    div.onclick = () => useSuggestion(text);
    box.appendChild(div);
  });

  box.style.display = items.length ? 'flex' : 'none';
}

/* get suggestions */
function getSuggestionsForQuery(query) {
  query = query.toLowerCase().trim();

  // choose source:
  // if AI suggestions exist use them, otherwise use default ones
  const source = lastAISuggestions.length
    ? lastAISuggestions
    : defaultSuggestions;

  // empty input = show defaults/AI suggestions
  if (!query) {
    return source;
  }

  const filtered = source.filter(item =>
    item.toLowerCase().includes(query)
  );

  return filtered.length ? filtered : ['No suggestions found'];
}

/* init */
function initSuggestions() {
  const textarea = document.querySelector('.msg-input');
  const box = document.getElementById('suggestions-box');

  if (!textarea || !box) return;

  function updateSuggestions() {
    renderSuggestions(getSuggestionsForQuery(textarea.value));
  }

  textarea.addEventListener('focus', updateSuggestions);
  textarea.addEventListener('input', updateSuggestions);
  textarea.addEventListener('click', updateSuggestions);

  document.addEventListener('click', (e) => {
    if (
      !e.target.closest('#suggestions-box') &&
      !e.target.closest('.msg-input')
    ) {
      box.style.display = 'none';
    }
  });
}

/* click suggestion */
function useSuggestion(text) {
  const textarea = document.querySelector('.msg-input');
  if (!textarea) return;
  textarea.value = text;
  textarea.focus();
  autoResize(textarea);
  document.getElementById('suggestions-box').style.display = 'none';
}

/* run after everything fully loads */
window.addEventListener('load', () => {
  wrapTablesWithExport();
  initScrollButton();

  const aiMessages = document.querySelectorAll('.msg-row.gemini .bubble');

  if (aiMessages.length > 0) {
    const lastBubble = aiMessages[aiMessages.length - 1];
    lastAISuggestions = extractSuggestionsFromText(lastBubble.innerText);
  } else {
    lastAISuggestions = [];
  }

  initSuggestions();

  const msgs = document.querySelector('.messages');
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
});