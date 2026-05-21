/**
 * KST Chatbot Widget
 * Embed with:
 *   <script src="kst-chatbot.js" data-api="https://your-api-host/chat"></script>
 * Optional attribute: data-api — URL of your KST chatbot backend /chat endpoint.
 */
(function () {
  'use strict';

  const API_URL = (document.currentScript && document.currentScript.dataset.api)
    || 'http://localhost:8000/chat';

  // ── Markdown → HTML (lightweight, no deps) ──────────────────────────────────
  function renderMarkdown(text) {
    let html = text
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      // fenced code blocks
      .replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
        `<pre><code class="lang-${lang}">${code.trim()}</code></pre>`)
      // inline code
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // markdown links [text](url) — must come before bold/italic
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g,
        (_, label, url) =>
          `<a href="${url}" target="_blank" rel="noopener noreferrer">`+
          `<svg viewBox="0 0 24 24" width="11" height="11" fill="currentColor" style="vertical-align:middle;margin-right:4px;flex-shrink:0"><path d="M19 19H5V5h7V3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>`+
          `${label}</a>`)
      // bare URLs (not already inside an href)
      .replace(/(?<!['"=(])(https?:\/\/[^\s<>"')]+)/g,
        url =>
          `<a href="${url}" target="_blank" rel="noopener noreferrer">`+
          `<svg viewBox="0 0 24 24" width="11" height="11" fill="currentColor" style="vertical-align:middle;margin-right:4px;flex-shrink:0"><path d="M19 19H5V5h7V3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>`+
          `View documentation</a>`)
      // bold
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // italic
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      // headers
      .replace(/^### (.+)$/gm, '<h4>$1</h4>')
      .replace(/^## (.+)$/gm, '<h3>$1</h3>')
      .replace(/^# (.+)$/gm, '<h3>$1</h3>')
      // horizontal rule
      .replace(/^---$/gm, '<hr>')
      // unordered lists
      .replace(/^\s*[-*] (.+)$/gm, '<li>$1</li>')
      // ordered lists
      .replace(/^\s*\d+\. (.+)$/gm, '<li>$1</li>')
      // wrap consecutive <li>
      .replace(/(<li>[\s\S]+?<\/li>)(?=\s*<li>|$)/g, (m) => `<ul>${m}</ul>`)
      // simple table rows (| a | b |)
      .replace(/^\|(.+)\|$/gm, (row) => {
        const cells = row.split('|').slice(1, -1);
        const isDivider = cells.every(c => /^[-: ]+$/.test(c));
        if (isDivider) return '';
        return '<tr>' + cells.map(c => `<td>${c.trim()}</td>`).join('') + '</tr>';
      })
      .replace(/(<tr>[\s\S]+?<\/tr>)/g, '<table>$1</table>')
      // paragraphs (double newline)
      .replace(/\n\n+/g, '</p><p>')
      // single newline
      .replace(/\n/g, '<br>');

    return '<p>' + html + '</p>';
  }

  // ── State ────────────────────────────────────────────────────────────────────
  const history = [];
  let isOpen = false;
  let isLoading = false;
  let isExpanded = false;

  // ── SVG Icons ────────────────────────────────────────────────────────────────
  const ICON_EXPAND   = `<svg viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>`;
  const ICON_COLLAPSE = `<svg viewBox="0 0 24 24"><path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/></svg>`;

  const QUICK_CHIPS = [
    'What is KST?',
    'How do I install KST?',
    'GTM setup',
    'Shopify setup',
    'WooCommerce setup',
    'Test my pixel',
    'No conversions showing',
    'Where is my Merchant ID?',
  ];

  const WELCOME_MSG = 'Hi! I\'m the KST Support Assistant. I can help you understand Kelkoo Sales Tracking or guide you through installation on your platform. What would you like to know?';

  // ── DOM Build ────────────────────────────────────────────────────────────────
  function buildWidget() {
    const fab = document.createElement('button');
    fab.id = 'kst-chat-fab';
    fab.setAttribute('aria-label', 'Open KST support chat');
    fab.innerHTML = `<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 10H6V9h12v3zm0-4H6V5h12v3z"/></svg>`;

    const win = document.createElement('div');
    win.id = 'kst-chat-window';
    win.setAttribute('role', 'dialog');
    win.setAttribute('aria-label', 'KST Support Chat');
    win.classList.add('kst-hidden');

    win.innerHTML = `
      <div id="kst-chat-header">
        <div class="kst-avatar">
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93V18c0-.55-.45-1-1-1s-1 .45-1 1v1.93C7.06 19.44 4.56 16.94 4.07 13H6c.55 0 1-.45 1-1s-.45-1-1-1H4.07C4.56 7.06 7.06 4.56 11 4.07V6c0 .55.45 1 1 1s1-.45 1-1V4.07C16.94 4.56 19.44 7.06 19.93 11H18c-.55 0-1 .45-1 1s.45 1 1 1h1.93c-.49 3.94-2.99 6.44-6.93 6.93z"/></svg>
        </div>
        <div>
          <div class="kst-title">KST Support</div>
          <div class="kst-subtitle">Kelkoo Sales Tracking Assistant · RAG</div>
        </div>
        <div class="kst-header-actions">
          <button id="kst-chat-expand" aria-label="Expand chat">${ICON_EXPAND}</button>
          <button id="kst-chat-close" aria-label="Close chat">
            <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
          </button>
        </div>
      </div>
      <div id="kst-chat-messages" aria-live="polite" aria-atomic="false"></div>
      <div id="kst-quick-chips"></div>
      <div id="kst-chat-input-row">
        <textarea id="kst-chat-input" placeholder="Ask about KST…" rows="1" aria-label="Type your message"></textarea>
        <button id="kst-chat-send" aria-label="Send">
          <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
    `;

    document.body.appendChild(fab);
    document.body.appendChild(win);

    const chipsEl = win.querySelector('#kst-quick-chips');
    QUICK_CHIPS.forEach(label => {
      const btn = document.createElement('button');
      btn.className = 'kst-chip';
      btn.textContent = label;
      btn.addEventListener('click', () => sendMessage(label));
      chipsEl.appendChild(btn);
    });

    fab.addEventListener('click', toggleChat);
    win.querySelector('#kst-chat-close').addEventListener('click', toggleChat);
    win.querySelector('#kst-chat-expand').addEventListener('click', toggleExpand);

    const input = win.querySelector('#kst-chat-input');
    const sendBtn = win.querySelector('#kst-chat-send');

    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 100) + 'px';
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!isLoading) sendMessage(input.value);
      }
    });
    sendBtn.addEventListener('click', () => {
      if (!isLoading) sendMessage(input.value);
    });

    appendMessage('bot', WELCOME_MSG);
  }

  // ── Expand / Collapse ────────────────────────────────────────────────────────
  function toggleExpand() {
    isExpanded = !isExpanded;
    const win = document.getElementById('kst-chat-window');
    const btn = document.getElementById('kst-chat-expand');
    if (isExpanded) {
      win.classList.add('kst-expanded');
      btn.innerHTML = ICON_COLLAPSE;
      btn.setAttribute('aria-label', 'Collapse chat');
    } else {
      win.classList.remove('kst-expanded');
      btn.innerHTML = ICON_EXPAND;
      btn.setAttribute('aria-label', 'Expand chat');
    }
    const msgs = document.getElementById('kst-chat-messages');
    setTimeout(() => { msgs.scrollTop = msgs.scrollHeight; }, 310);
  }

  // ── Toggle ───────────────────────────────────────────────────────────────────
  function toggleChat() {
    isOpen = !isOpen;
    const win = document.getElementById('kst-chat-window');
    const fab = document.getElementById('kst-chat-fab');
    if (isOpen) {
      win.classList.remove('kst-hidden');
      document.getElementById('kst-chat-input').focus();
      fab.innerHTML = `<svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>`;
    } else {
      win.classList.add('kst-hidden');
      fab.innerHTML = `<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 10H6V9h12v3zm0-4H6V5h12v3z"/></svg>`;
    }
  }

  // ── Link post-processor ───────────────────────────────────────────────────────
  const LINK_ICON = '<svg viewBox="0 0 24 24" width="11" height="11" fill="currentColor" style="vertical-align:middle;margin-right:4px;flex-shrink:0"><path d="M19 19H5V5h7V3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>';
  function linkifyBotMessage(el) {
    const walk = (node) => {
      if (!node) return;
      if (node.nodeType === Node.TEXT_NODE) {
        if (!/(https?:\/\/)/.test(node.textContent)) return;
        const wrap = document.createElement('span');
        wrap.innerHTML = node.textContent.replace(
          /(https?:\/\/[^\s<>"')\]]+)/g,
          url => `<a href="${url}" target="_blank" rel="noopener noreferrer">${LINK_ICON}View documentation</a>`
        );
        node.parentNode.replaceChild(wrap, node);
      } else if (node.nodeType === Node.ELEMENT_NODE &&
                 node.tagName !== 'A' && node.tagName !== 'PRE' && node.tagName !== 'CODE') {
        Array.from(node.childNodes).forEach(walk);
      }
    };
    Array.from(el.childNodes).forEach(walk);
  }

  // ── Messages ─────────────────────────────────────────────────────────────────
  function appendMessage(role, text) {
    const container = document.getElementById('kst-chat-messages');
    const div = document.createElement('div');
    div.className = 'kst-msg kst-' + (role === 'user' ? 'user' : 'bot');
    if (role === 'bot') {
      div.innerHTML = renderMarkdown(text);
      linkifyBotMessage(div);
    } else {
      div.textContent = text;
    }
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
  }

  function showTyping() {
    const container = document.getElementById('kst-chat-messages');
    const el = document.createElement('div');
    el.className = 'kst-typing';
    el.id = 'kst-typing-indicator';
    el.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(el);
    container.scrollTop = container.scrollHeight;
  }

  function removeTyping() {
    const el = document.getElementById('kst-typing-indicator');
    if (el) el.remove();
  }

  // ── Send ─────────────────────────────────────────────────────────────────────
  async function sendMessage(text) {
    text = (text || '').trim();
    if (!text || isLoading) return;

    const input = document.getElementById('kst-chat-input');
    const sendBtn = document.getElementById('kst-chat-send');

    input.value = '';
    input.style.height = 'auto';

    history.push({ role: 'user', content: text });
    appendMessage('user', text);

    isLoading = true;
    sendBtn.disabled = true;
    showTyping();

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history }),
      });

      if (!res.ok) throw new Error('API error ' + res.status);

      const data = await res.json();
      const reply = data.reply || 'Sorry, I could not get a response. Please try again.';

      removeTyping();
      appendMessage('bot', reply);
      history.push({ role: 'assistant', content: reply });
    } catch (err) {
      removeTyping();
      appendMessage('bot', 'Sorry, something went wrong. Please try again in a moment.');
      history.pop();
      console.error('[KST Chatbot RAG]', err);
    } finally {
      isLoading = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  // ── Init ─────────────────────────────────────────────────────────────────────
  function init() {
    const style = document.createElement('link');
    style.rel = 'stylesheet';
    const cssHref = (document.currentScript && document.currentScript.src)
      ? document.currentScript.src.replace(/\.js(\?.*)?$/, '.css')
      : 'kst-chatbot.css';
    style.href = cssHref;
    document.head.appendChild(style);
    buildWidget();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
