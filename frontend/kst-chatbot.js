/**
 * KST Chatbot Widget v1.2
 * Embed with:
 *   <script src="kst-chatbot.js" data-api="https://your-api-host/chat"></script>
 */
(function () {
  'use strict';

  const API_URL = (document.currentScript && document.currentScript.dataset.api)
    || 'http://localhost:8000/chat';

  // ── Markdown → HTML (lightweight, no deps) ──────────────────────────────────
  function renderMarkdown(text) {
    let html = text
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
        `<pre><code class="lang-${lang}">${code.trim()}</code></pre>`)
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g,
        (_, label, url) =>
          `<a href="${url}" target="_blank" rel="noopener noreferrer">` +
          `<svg viewBox="0 0 24 24" width="11" height="11" fill="currentColor" style="vertical-align:middle;margin-right:4px;flex-shrink:0"><path d="M19 19H5V5h7V3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>` +
          `${label}</a>`)
      .replace(/(?<!['"=(])(https?:\/\/[^\s<>"')]+)/g,
        url =>
          `<a href="${url}" target="_blank" rel="noopener noreferrer">` +
          `<svg viewBox="0 0 24 24" width="11" height="11" fill="currentColor" style="vertical-align:middle;margin-right:4px;flex-shrink:0"><path d="M19 19H5V5h7V3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>` +
          `View documentation</a>`)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/^### (.+)$/gm, '<h4>$1</h4>')
      .replace(/^## (.+)$/gm, '<h3>$1</h3>')
      .replace(/^# (.+)$/gm, '<h3>$1</h3>')
      .replace(/^---$/gm, '<hr>')
      .replace(/^\s*[-*] (.+)$/gm, '<li>$1</li>')
      .replace(/^\s*\d+\. (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>[\s\S]+?<\/li>)(?=\s*<li>|$)/g, (m) => `<ul>${m}</ul>`)
      .replace(/^\|(.+)\|$/gm, (row) => {
        const cells = row.split('|').slice(1, -1);
        const isDivider = cells.every(c => /^[-: ]+$/.test(c));
        if (isDivider) return '';
        return '<tr>' + cells.map(c => `<td>${c.trim()}</td>`).join('') + '</tr>';
      })
      .replace(/(<tr>[\s\S]+?<\/tr>)/g, '<table>$1</table>')
      .replace(/\n\n+/g, '</p><p>')
      .replace(/\n/g, '<br>');
    return '<p>' + html + '</p>';
  }

  // ── State ────────────────────────────────────────────────────────────────────
  const history = [];
  let isOpen = false;
  let isLoading = false;
  let isExpanded = false;
  // 'normal' | 'other_issue' | 'awaiting_resolution' | 'ended'
  let conversationMode = 'normal';

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
    'Other Issue',
  ];

  const WELCOME_MSG = "Hi! I'm the KST Support Assistant. I can help you understand Kelkoo Sales Tracking or guide you through installation on your platform. What would you like to know?";

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

    // Build chips — "Other Issue" gets a special style
    const chipsEl = win.querySelector('#kst-quick-chips');
    QUICK_CHIPS.forEach(label => {
      const btn = document.createElement('button');
      btn.className = label === 'Other Issue' ? 'kst-chip kst-chip-other' : 'kst-chip';
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

    // Welcome message — no follow-up after this
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

  // ── Toggle open/close ────────────────────────────────────────────────────────
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

  // ── Link post-processor ──────────────────────────────────────────────────────
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

  // ── Append a chat message bubble ─────────────────────────────────────────────
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

  // ── Typing indicator ─────────────────────────────────────────────────────────
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

  // ── Disable action buttons after one is clicked ──────────────────────────────
  function disableActionBtns(wrapper) {
    wrapper.querySelectorAll('.kst-action-btn').forEach(btn => {
      btn.disabled = true;
    });
  }

  // ── "Do you have any other doubt?" prompt ────────────────────────────────────
  function appendFollowUp() {
    if (conversationMode === 'ended') return;
    const container = document.getElementById('kst-chat-messages');
    const div = document.createElement('div');
    div.className = 'kst-followup';
    div.innerHTML = `
      <p class="kst-followup-text">Do you have any other doubt?</p>
      <div class="kst-action-btns">
        <button class="kst-action-btn kst-action-yes">Yes</button>
        <button class="kst-action-btn kst-action-no">No, end chat</button>
      </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    div.querySelector('.kst-action-yes').addEventListener('click', () => {
      disableActionBtns(div);
      appendMessage('bot', 'Sure! What would you like to know? Pick an option below or type your question.');
      // Scroll chips into view
      setTimeout(() => {
        const chips = document.getElementById('kst-quick-chips');
        if (chips) chips.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }, 200);
    });

    div.querySelector('.kst-action-no').addEventListener('click', () => {
      disableActionBtns(div);
      conversationMode = 'ended';
      appendMessage('bot', 'Thank you for using KST Support! Have a great day. 👋');
      const input = document.getElementById('kst-chat-input');
      const sendBtn = document.getElementById('kst-chat-send');
      input.disabled = true;
      input.placeholder = 'Chat ended';
      sendBtn.disabled = true;
    });
  }

  // ── "Is your issue resolved?" prompt ─────────────────────────────────────────
  function appendResolutionCheck() {
    const container = document.getElementById('kst-chat-messages');
    const div = document.createElement('div');
    div.className = 'kst-followup';
    div.innerHTML = `
      <p class="kst-followup-text">Was this helpful? Is your issue resolved?</p>
      <div class="kst-action-btns">
        <button class="kst-action-btn kst-action-yes">Yes, resolved!</button>
        <button class="kst-action-btn kst-action-no">No, still having issue</button>
      </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    div.querySelector('.kst-action-yes').addEventListener('click', () => {
      disableActionBtns(div);
      conversationMode = 'normal';
      appendMessage('bot', 'Great! Glad I could help. 😊');
      setTimeout(() => appendFollowUp(), 400);
    });

    div.querySelector('.kst-action-no').addEventListener('click', () => {
      disableActionBtns(div);
      appendCreateCasePrompt();
    });
  }

  // ── "Create SF Support Case" button ──────────────────────────────────────────
  function appendCreateCasePrompt() {
    const container = document.getElementById('kst-chat-messages');
    const div = document.createElement('div');
    div.className = 'kst-msg kst-bot';
    div.innerHTML = `
      <p>No worries! You can raise a support case and our KST team will get back to you.</p>
      <button class="kst-create-case-btn">📋 Create SF Support Case</button>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    div.querySelector('.kst-create-case-btn').addEventListener('click', () => {
      div.querySelector('.kst-create-case-btn').style.display = 'none';
      appendSFForm();
    });
  }

  // ── Salesforce case form ──────────────────────────────────────────────────────
  function appendSFForm() {
    const container = document.getElementById('kst-chat-messages');
    const div = document.createElement('div');
    div.className = 'kst-msg kst-bot kst-sf-wrapper';
    div.innerHTML = `
      <p class="kst-sf-title">🎫 Create Support Case</p>
      <div class="kst-sf-form">
        <input class="kst-sf-input" id="sf-name"  type="text"  placeholder="Your Name *" />
        <input class="kst-sf-input" id="sf-mid"   type="text"  placeholder="Merchant ID *" />
        <input class="kst-sf-input" id="sf-email" type="email" placeholder="Email Address *" />
        <textarea class="kst-sf-textarea" id="sf-issue" placeholder="Describe your issue in detail... *" rows="4"></textarea>
        <button class="kst-sf-submit">Submit Case →</button>
      </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    div.querySelector('.kst-sf-submit').addEventListener('click', () => {
      const nameEl  = div.querySelector('#sf-name');
      const midEl   = div.querySelector('#sf-mid');
      const emailEl = div.querySelector('#sf-email');
      const issueEl = div.querySelector('#sf-issue');

      // Validate all fields
      let valid = true;
      [nameEl, midEl, emailEl, issueEl].forEach(field => {
        if (!field.value.trim()) {
          field.classList.add('kst-sf-error');
          valid = false;
        } else {
          field.classList.remove('kst-sf-error');
        }
      });
      if (!valid) return;

      const emailVal = emailEl.value.trim();

      // Show success state
      div.innerHTML = `
        <div class="kst-sf-success">
          <div class="kst-sf-success-icon">✅</div>
          <p><strong>Case submitted successfully!</strong></p>
          <p>Our KST support team will get back to you at <strong>${emailVal}</strong> shortly.</p>
        </div>
      `;
      conversationMode = 'ended';
      const input = document.getElementById('kst-chat-input');
      const sendBtn = document.getElementById('kst-chat-send');
      input.disabled = true;
      input.placeholder = 'Chat ended';
      sendBtn.disabled = true;
      container.scrollTop = container.scrollHeight;
    });
  }

  // ── Send message ─────────────────────────────────────────────────────────────
  async function sendMessage(text) {
    text = (text || '').trim();
    if (!text || isLoading || conversationMode === 'ended') return;

    const input  = document.getElementById('kst-chat-input');
    const sendBtn = document.getElementById('kst-chat-send');

    input.value = '';
    input.style.height = 'auto';

    // ── Special case: "Other Issue" chip ──────────────────────────────────────
    if (text === 'Other Issue') {
      history.push({ role: 'user', content: 'I have another issue not listed here.' });
      appendMessage('user', 'Other Issue');
      conversationMode = 'other_issue';
      const botMsg = "Of course! Please explain your issue in detail and I'll do my best to help you.";
      history.push({ role: 'assistant', content: botMsg });
      setTimeout(() => appendMessage('bot', botMsg), 300);
      return;
    }

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

      const data  = await res.json();
      const reply = data.reply || 'Sorry, I could not get a response. Please try again.';

      removeTyping();
      appendMessage('bot', reply);
      history.push({ role: 'assistant', content: reply });

      // ── Post-response flow ────────────────────────────────────────────────
      if (conversationMode === 'other_issue') {
        // User just explained their issue → ask if resolved
        conversationMode = 'awaiting_resolution';
        setTimeout(() => appendResolutionCheck(), 500);
      } else if (conversationMode !== 'ended') {
        // Normal Q&A → ask if they have more doubts
        setTimeout(() => appendFollowUp(), 500);
      }

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
